from argparse import ArgumentTypeError
from pathlib import Path

def parse_directory(directory: str):

    path = Path(directory)
    if not path.is_dir():
        raise ArgumentTypeError(f"{path} is not a valid directory.")
    return path
