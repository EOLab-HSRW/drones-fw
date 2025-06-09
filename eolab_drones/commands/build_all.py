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

        parser.add_argument("--overwrite",
                            action="store_true",
                            help="Overwrite build if present.")

    def execute(self, args: Namespace):

        for drone in get_drones().keys():
            build_cmd = ["easy_px4", "build",
                         "--type", args.type,
                         "--path", get_drone_path(drone),
                         "--comps", get_components_path()]

            if args.type == "firmware":
                build_cmd.extend(["--output", "."])

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

            return_code = process.wait()

            if return_code != 0:
                sys.exit(return_code)


        return None


