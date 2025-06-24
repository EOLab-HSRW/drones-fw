import subprocess
from argparse import Namespace, ArgumentParser
import sys
from easy_px4.backend import Command, valid_dir_path, run_command
from ..api import get_drones, get_drone_path, get_components_path

class BuildAllCommand(Command):

    cmd_name = "build_all"

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

        parser.add_argument("--msgs-output",
                            type=valid_dir_path,
                            help="Output directory to copy PX4 msgs.")

        parser.add_argument("--deb-output",
                            type=valid_dir_path,
                            help="Output directory .deb (only SITL).")

        parser.add_argument("--overwrite",
                            action="store_true",
                            help="Overwrite build if present.")


    def execute(self, args: Namespace):
        failed_drones = []

        for drone in get_drones().keys():
            build_cmd = ["eolab_drones", "build",
                         "--type", args.type,
                         "--drone", drone]

            if args.type == "firmware":
                build_cmd.extend(["--output", "."])

            if args.msgs_output:
                build_cmd.extend(["--msgs-output", args.msgs_output])

            if args.overwrite:
                build_cmd.append("--overwrite")

            if args.type == "sitl" and args.deb_output:
                build_cmd.extend(["--deb-output", args.deb_output])

            self.logger.info(f"\n=========== Buiding: {drone} ===========\n")

            build = run_command(
                build_cmd,
                live=True,
                logger=self.logger
            )

            if build.returncode != 0:
                self.logger.error(f"Buiding failed for drone: {drone}")


        if failed_drones:
            self.logger.error("Some builds failed: ")
            for drone in failed_drones:
                self.logger.error(f"  - {drone}")
            sys.exit(1)

        self.logger.info("All builds completed successfully")

        return None


