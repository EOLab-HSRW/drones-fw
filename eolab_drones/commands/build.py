import os
import sys
import subprocess
import shutil
from argparse import Namespace, ArgumentParser
from easy_px4.backend import Command, valid_dir_path, run_command
from easy_px4.api import get_build_dir
from ..api import get_drones, get_drone_path, get_components_path, get_drone


class BuildDroneCommand(Command):

    cmd_name = "build"

    BUILD_TYPES = [
        "sitl",
        "firmware"
    ]

    def add_arguments(self, parser: ArgumentParser):

        parser.add_argument("--type",
                            required=True,
                            type=str.lower,
                            choices=self.BUILD_TYPES,
                            help="Build type.")

        parser.add_argument("--drone",
                            required=True,
                            type=str.lower,
                            choices=get_drones().keys(),
                            help="Build type.")

        parser.add_argument("--output",
                            default=".",
                            type=valid_dir_path,
                            help="*.px4 firmware file output folder.")

        parser.add_argument("--msgs-output",
                            type=valid_dir_path,
                            help="Output directory to copy PX4 msgs.")

        parser.add_argument("--overwrite",
                            action="store_true",
                            help="Overwrite build if present.")

        parser.add_argument("--deb-output",
                            type=valid_dir_path,
                            help="Output directory .deb (only SITL).")

        parser.add_argument("--arch",
                            default=os.environ.get('BUILD_ARCH', "amd64"),
                            type=str,
                            help="Output directory .deb (only SITL and --deb-output).")


    def get_current_branch(self):
        result = subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            capture_output=True,
            text=True
        )

        if result.returncode != 0:
            self.logger.error(f"Git error: {result.stderr.strip()}")
            sys.exit(1)
        return result.stdout.strip()


    def deb_packaging(self, args: Namespace):

        drone_info = get_drone(args.drone)
        _, px4_minor, _ = drone_info["px4_version"].split(".")

        drone_name = args.drone
        custom_fw_version = drone_info["custom_fw_version"]
        branch = self.get_current_branch()
        release_type = "stable" if branch == "main" else branch
        arch = args.arch

        package_name = f"eolab-sitl-{drone_name}"
        # format: eolab-sitl-<DRONE NAME>_<CUSTOM-FW-VERSION>_<RELEASE TYPE>_<ARCH>
        # e.g. eolab-sitl-protoflyer_1.2.3_stable_amd64
        # note: using underscore `_` to parse name easily.
        deb_full_name = f"{package_name}_{custom_fw_version}_{release_type}_{arch}"

        deb_folder = args.deb_output / deb_full_name
        deb_folder.mkdir(parents=True, exist_ok=True)

        # depends is structure as string with the DEB control file conventions
        DEPENDS: str = "libgz-transport13, libgz-sensors8, libgz-plugin2"
        control_content = f"""\
Package: {package_name}
Version:  {custom_fw_version}
Section: utils
Priority: optional
Architecture:  {arch}
Depends: {DEPENDS}
Maintainer: Harley Lara <contact@harleylara.com>
Description: SITL firmware for EOLab {drone_name}.
"""

        # debian_dir = deb_folder / "DEBIAN"
        # debian_dir.mkdir(parents=True, exist_ok=True)
        (deb_folder / "DEBIAN").mkdir(parents=True, exist_ok=True)

        # debian_control = debian_dir / "control"
        # debian_control.write_text(control_content)
        (deb_folder / "DEBIAN" / "control").write_text(control_content)

        # Copy binaries and structure
        build_dir = get_build_dir() / f"px4_sitl_{drone_name}"
        opt_dir = deb_folder / "opt" / package_name
        opt_dir.mkdir(parents=True, exist_ok=True)
        subprocess.run(["cp", "-aL", str(build_dir / "bin"), str(opt_dir / "bin")], check=True)

        if int(px4_minor) <= 15:
            self.logger.debug("PX4 minor version <= 15")
            source = build_dir / "etc"
            dest = opt_dir / "rootfs/"
            dest.mkdir(parents=True, exist_ok=True)
            copy_rootfs = subprocess.run(["cp", "-aL", str(source), str(dest)], check=True)
        elif int(px4_minor) >= 16:
            self.logger.debug("PX4 minor version >= 16")
            copy_rootfs = subprocess.run(["cp", "-aL", str(build_dir / "rootfs"), str(opt_dir / "rootfs")], check=True)

        if copy_rootfs.returncode != 0:
            self.logger.error(f"{copy_rootfs.stderr}. {copy_rootfs.stdout}")
            sys.exit(1)

        # Remove logs to reduce package size
        for log_dir in (opt_dir / "rootfs").rglob("log"):
            if log_dir.is_dir():
                self.logger.debug(f"Removing: {log_dir}")
                shutil.rmtree(log_dir)

        # Copy gz_plugins only if version is >= 1.16.0
        if int(px4_minor) >= 16:
            self.logger.debug(f"PX4 version: {drone_info['px4_version']}. Adding gz_plugins")
            gz_plugins_dir = opt_dir / "gz_plugins"

            gz_plugins_dir.mkdir(parents=True, exist_ok=True)
            subprocess.run(
                f"cp {build_dir}/src/modules/simulation/gz_plugins/*.so {gz_plugins_dir}",
                shell=True,
                check=True
            )

        # Create wrapper
        wrapper_path = deb_folder / "usr/bin"
        wrapper_path.mkdir(parents=True, exist_ok=True)
        wrapper_script = wrapper_path / package_name
        wrapper_script.write_text(f"""#!/bin/bash
DEFAULT_WORKDIR="/opt/{package_name}/rootfs"
ARGS=()

# Check if the user already passed -w
SKIP_W_OPTION=false
for arg in '$@'; do
    if [[ "$arg" == "-w" ]]; then
        SKIP_W_OPTION=true
        break
    fi
done

# Add default -w only if the user didn’t specify it
if ! $SKIP_W_OPTION; then
    ARGS+=("-w" "$DEFAULT_WORKDIR")
fi

# Append all user-provided arguments
ARGS+=("$@")

# Execute the actual px4 binary with merged args
exec /opt/{package_name}/bin/px4 "${{ARGS[@]}}"
""")
        wrapper_script.chmod(0o755)

        pkg_generation = run_command(
            ["dpkg-deb", "--build", str(deb_folder)],
            live=True,
            logger=self.logger
        )

        if pkg_generation.returncode != 0:
            self.logger.error(f"{pkg_generation.stderr}. {pkg_generation.stdout}")
            sys.exit(1)

        shutil.rmtree(deb_folder)


    def execute(self, args: Namespace):

        build_cmd = [
            "easy_px4", "build",
            "--type", args.type,
            "--path", get_drone_path(args.drone),
            "--comps", get_components_path()
        ]

        if args.type == "firmware" and args.output:
            build_cmd.extend(["--output", args.output])

        if args.msgs_output:
            build_cmd.extend(["--msgs-output", str(args.msgs_output.resolve())])

        if args.overwrite:
            build_cmd.append("--overwrite")

        build = run_command(
            cmd=build_cmd,
            live=True,
            logger=self.logger
        )

        if build.returncode != 0:
            self.logger.error(f"{build.stderr}. {build.stdout}")
            sys.exit(1)

        if args.type == "sitl" and args.deb_output:
            self.logger.debug("Getting ready for packaging")
            self.deb_packaging(args)

        # build_drone = run_command(build_cmd)
        # print(f"\nProcess finished with return code: {process.returncode}")

        # if build_drone["returncode"] != 0:
        #     self.logger.error(f"Failed to build firmware. {build_drone['stderr']}, {build_drone['stdout']}")

        return None
