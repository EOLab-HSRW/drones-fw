import subprocess
from argparse import Namespace, ArgumentParser
from easy_px4.backend import Command, valid_dir_path
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

    def execute(self, args: Namespace):

        build_cmd = ["easy_px4", "build",
                     "--type", args.type,
                     "--path", get_drone_path(args.drone),
                     "--comps", get_components_path(),
                     "--msgs-output", args.msgs_output]

        # subprocess.check_output([])

        print(build_cmd)
        return None


