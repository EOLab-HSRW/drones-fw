import sys
import argparse

from easy_px4.backend import Command
from .commands.build import BuildDroneCommand
from .commands.build_all import BuildAllCommand

# available command registration
COMMAND_REGISTRY: list[type[Command]] = [
    BuildDroneCommand,
    BuildAllCommand,
]

def main():

    parser = argparse.ArgumentParser(
        prog=__package__,

        description="A simple tool to help building EOLab drones firmwares"
    )

    subparsers = parser.add_subparsers(dest="command", required=True, help="Available commands")

    cmd_register = {}

    for command_class in COMMAND_REGISTRY:
        subparser = subparsers.add_parser(command_class.cmd_name, help=f"{command_class.cmd_name} command")
        command_class().add_arguments(subparser)
        cmd_register[command_class.cmd_name] = command_class

    args = parser.parse_args()


    with cmd_register[args.command]() as worker:
        worker.execute(args)


    return 0


if __name__ == "__main__":
    sys.exit(main())
