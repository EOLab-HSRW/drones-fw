import subprocess
from argparse import Namespace, ArgumentParser
from easy_px4.backend import Command, valid_dir_path, run_command
from ..api import get_drones, get_drone_path, get_components_path

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

        parser.add_argument("--msgs-output",
                            type=valid_dir_path,
                            help="Output directory to copy PX4 msgs.")

        parser.add_argument("--overwrite",
                            action="store_true",
                            help="Overwrite build if present.")

    def execute(self, args: Namespace):

        build_cmd = ["easy_px4", "build",
                     "--type", args.type,
                     "--path", get_drone_path(args.drone),
                     "--comps", get_components_path()]

        if args.type == "firmware":
            build_cmd.extend(["--output", "."])

        if args.msgs_output:
            build_cmd.extend(["--msgs-output", str(args.msgs_output.resolve())])

        if args.overwrite:
            build_cmd.append("--overwrite")

        process = subprocess.Popen(
            build_cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True  # Ensures output is decoded to string
        )

        for line in process.stdout:
            print(line, end='')  # Avoid double newline

        # build_drone = run_command(build_cmd)
        # print(f"\nProcess finished with return code: {process.returncode}")

        # if build_drone["returncode"] != 0:
        #     self.logger.error(f"Failed to build firmware. {build_drone['stderr']}, {build_drone['stdout']}")

        return None


