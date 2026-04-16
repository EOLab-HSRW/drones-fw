import shutil
import sys
import argparse

from .commands.build import BuildDroneCommand
from easy_px4.backend import Command

# available command registration
COMMAND_REGISTRY: list[type[Command]] = [
    BuildDroneCommand,
]

def _check_environment() -> None:
    if not sys.platform.startswith("linux"):
        raise SystemExit(
                "This package is deliberately restricted to GNU/Linux systems."
                )

    tools = ("git", "dpkg-deb", "easy_px4")

    missing = [tool for tool in tools if shutil.which(tool) is None]

    apt_installable = [tool for tool in missing if tool != "easy_px4"]

    msg: str = ""

    if missing:
        msg = f"Missing system dependency: {', '.join(missing)}."

        if apt_installable:
            msg += f" Please install them with: sudo apt install {' '.join(apt_installable)}\n"

        if "easy_px4" in missing:
            msg += f"To install `easy_px4` follow the installation instruction from: https://github.com/EOLab-HSRW/easy-px4"

        raise SystemExit(msg)

def main() -> int:

    _check_environment()

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
    raise SystemExit(main())
