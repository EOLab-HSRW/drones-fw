import sys

if sys.version_info >= (3, 11):
    import tomllib
else:
    import tomli as tomllib

import re
import shutil
from pathlib import Path
from typing import Optional, Union, get_origin, get_args
from dataclasses import dataclass
from argparse import ArgumentParser, Namespace
from .command import Command
from ..utils import parse_directory
from ..paths import PX4_DIR
from ..runner import run_command

import subprocess

@dataclass
class Info:
    """Class for keeping track structure of the info file."""
    name: str
    id: int
    vendor: str
    model: str
    px4_version: str
    custom_fw_version: str

    components: dict[str, list[str]]

    defualt_components: Optional[Union[str, list[str]]] = None


class BuildCommand(Command):
    """
    Build command to handled the build of PX4.
    We make a distintion on:
    - firmware: binary that is flash into the flight controller
    - sitl: binary running for simulation (Software in the Loop)

    Clearly both are firmware but the terminology distintion is mainly
    to create a mental separation between the one running on the FMU and 
    the one for development.

    The way how the build command works is by getting:
    - type: define the type of build
    - path: a path to a directory containing the files
        - info.toml: information specific to the drone
        - board.modules: list of modules to enable on hardware
        - sitl.modules: list of modules to enable for simulation
        - parms.airframe: airframe file defining all the parameter for the drone
    """
    cmd_name = "build"

    INFO_FILE = "info.toml"
    PARMS_FILE = "parms.airframe"

    REQUIRED_COMMON = [
        INFO_FILE,
        PARMS_FILE
    ]

    FIRM_MODULES = "board.modules"
    REQUIRED_FIRMWARE = [
        FIRM_MODULES
    ]

    SITL_MODULES = "sitl.modules"
    REQUIRED_SITL = [
        SITL_MODULES
    ]

    BUILD_TYPES = [
        "firmware",
        "sitl"
    ]

    def __init__(self) -> None:
        super().__init__()
        self.target_tag = None
        self.original_tag = None
        self.commit_hash = None

    def add_arguments(self, parser: ArgumentParser) -> None:

        parser.add_argument("--type",
                            required=True,
                            type=str.lower,
                            choices=self.BUILD_TYPES,
                            help="type of build"
                            )

        parser.add_argument("--path",
                            type=parse_directory,
                            required=True,
                            help="Path to the directory containing all the firmware files")

        parser.add_argument("--output",
                            default=".",
                            type=parse_directory,
                            help="Path to the output directory")

        # Parameters check
        # see if the parameter is set to default
        # check if the parameter exist ?
        parser.add_argument("--params-check",
                            default=False,
                            type=bool,
                            help="Parameter check. Check if the parameter are set with the right default-value")

        # caching ?
        # clean run ?

    def __dir_validations(self, type: str, path: Path):
        """
        Check that all required files exist in the given directory.
        """

        required_files = self.REQUIRED_COMMON

        if type == "firmware":
            required_files.extend(self.REQUIRED_FIRMWARE)
        elif type == "sitl":
            required_files.extend(self.REQUIRED_SITL)

        missing = [fname for fname in required_files if not (path / fname).is_file()]

        if missing:
            raise FileNotFoundError(f"Missing required file(s) in path {path}: {', '.join(missing)}")


    def __read_info(self, path: Path):

        info_file = path / self.INFO_FILE

        info = None

        try:
            with open(str(info_file), "r", encoding="utf-8") as f:
                content = f.read()
                info = tomllib.loads(content)
        except tomllib.TOMLDecodeError as e:
            self.logger.error(f"Problem parsing {self.INFO_FILE}. \nTraceback:\n\n{e}")
        except Exception as e:
            self.logger.error(f"Unexpected error: {e}")

        return info



    def __matches_type(self, value, expected_type) -> bool:
        """
        Return True if `value` conforms to `expected_type`.  Works for:
          - basic built-ins, e.g. str, int, float
          - Optional[...]  (i.e. Union[..., NoneType])
          - Union[...]     (checks any one branch)
          - list[SomeType]
          - dict[KeyType,ValueType]
          - (and will treat other non‐generic types as simple isinstance checks)
        """

        origin = get_origin(expected_type)
        args = get_args(expected_type)

        # 1) If it’s a Union (including Optional), try each branch:
        if origin is Union:
            # “Union[..., NoneType]” is the same as Optional[...]
            for branch in args:
                # Allow None if branch is NoneType
                if branch is type(None) and value is None:
                    return True
                # Otherwise, recursively check the other branch
                if branch is not type(None) and self.__matches_type(value, branch):
                    return True
            return False

        # 2) If it’s a list[T], first check isinstance(value, list), then each element matches T
        if origin is list:
            if not isinstance(value, list):
                return False
            (item_type,) = args
            for element in value:
                if not self.__matches_type(element, item_type):
                    return False
            return True

        # 3) If it’s a dict[K, V], check isinstance(value, dict) and each key/value pair matches
        if origin is dict:
            if not isinstance(value, dict):
                return False
            key_type, val_type = args
            for k, v in value.items():
                if not self.__matches_type(k, key_type) or not self.__matches_type(v, val_type):
                    return False
            return True

        return isinstance(value, expected_type)


    def __validate_component(self, defualt_components: Union[str, list[str]], compatibles: list[str]):
        """
        This validation is done after the type validation.
        There for is expected that the types of the parameter are correct at this point.
        """
        if isinstance(defualt_components, str):
            components = [defualt_components]
        elif isinstance(defualt_components, list):
            components = defualt_components

        invalid = [component for component in components if component not in compatibles]

        if invalid:
            self.logger.error(f"Invalid component(s): {invalid} in '{self.INFO_FILE}'. Must be one the compatible components: {compatibles}")
            sys.exit(1)
        return components


    def __validate_info(self, info_dict: dict):

        for expected_key, expected_type in Info.__annotations__.items():
            if expected_key not in info_dict:
                # maybe is Optional
                if get_origin(expected_type) is Union and type(None) in get_args(expected_type):
                    continue
                else:
                    self.logger.error(f"{self.INFO_FILE}: Missing required field: {expected_key} of type {type(expected_type)}")
                    sys.exit(1)

            value = info_dict[expected_key]

            if value is None:
                # If the field really is Optional[...] (Union[..., NoneType]), None is okay.
                if get_origin(expected_type) is Union and type(None) in get_args(expected_type):
                    continue
                else:
                    self.logger.error(f"Field '{expected_key}' must be of type {expected_type}, but got None.")
                    sys.exit(1)


            if not self.__matches_type(value, expected_type):
                self.logger.error(
                    f"Field '{expected_key}' must be of type '{expected_type.__name__}'. "
                    f"Got value={value!r} (type={type(value).__name__})"
                )
                sys.exit(1)


        if not re.fullmatch(r"v\d+\.\d+\.\d+", info_dict["px4_version"]):
            self.logger.error("'px4_version' must be in format v<int>.<int>.<int>")
            sys.exit(1)

        if not re.fullmatch(re.compile(r"^(beta|alpha|rc)\d+$|^\d+\.\d+\.\d+$"), info_dict["custom_fw_version"]):
            self.logger.error(
                f"'custom_fw_version' must be semantic version <int>.<int>.<int> or beta<int>, alpha<int>, rc<int> got value={info_dict['custom_fw_version']}"
            )
            sys.exit(1)

        if info_dict.get("defualt_components") is not None:
            info_dict["defualt_components"] = self.__validate_component(info_dict["defualt_components"], info_dict["components"]["compatible"])

        return True


    def __load_info(self, path: Path) -> Info:

        info_dict = self.__read_info(path)
        if self.__validate_info(info_dict):
            self.logger.info(f"valid {self.INFO_FILE}")
            return Info(**info_dict)

    def __prepend_insertion(self, file: Path, match: str, insert: str):

        if not file.is_file():
            self.logger.error(f"the provided path is not a file. Got path {file}")
            sys.exit(1)

        temp = file.parent / f"{file.stem}.tmp"

        with file.open("r") as infile, temp.open("w") as outfile:
            for line in infile:
                if match in line:
                    outfile.write(insert + '\n')
                outfile.write(line)

        temp.replace(file)


    def execute(self, args: Namespace) -> None:

        self.__dir_validations(args.type, args.path)

        info = self.__load_info(args.path)

        # STEP: fetch all the tags
        fetch_res = run_command(['git', 'fetch', '--tags'], cwd=PX4_DIR)
        if fetch_res['returncode'] != 0:
            self.logger.error(f"Failed to fetch tags: {fetch_res['stderr']}")
            sys.exit(1)

        # STEP: composing the correct tag before checkout
        self.original_tag = ""
        if any(word in info.custom_fw_version for word in ["beta", "alpha", "rc"]):
            self.original_tag = f"{info.px4_version}-{info.custom_fw_version}"
            self.target_tag = self.original_tag
        else:
            self.original_tag = info.px4_version
            self.target_tag  = f"{info.px4_version}-{info.custom_fw_version}"

        # STEP: checkout to version
        self.logger.info(f"Checking out to version {self.original_tag}")
        git_checkout = run_command(['git', 'checkout', self.original_tag], cwd=PX4_DIR)
        if git_checkout['returncode'] != 0:
            self.logger.error(f"Failed to checkout to {self.original_tag}. Make sure if a valid px4 version. {git_checkout['stderr']}")
            sys.exit(1)

        self.logger.info("Syncronizing submodules")
        run_command(["git", "submodule", "sync", "--recursive"], cwd=PX4_DIR)
        run_command(["git", "submodule", "update" "--init", "--recursive"], cwd=PX4_DIR)

        # STEP: get commit hash
        self.commit_hash = run_command(['git', 'rev-list', '-n', '1', self.original_tag], cwd=PX4_DIR)["stdout"]

        run_command(['git', 'tag', '-d', self.original_tag], cwd=PX4_DIR, check=True)

        run_command(['git', 'tag', self.target_tag, self.commit_hash], cwd=PX4_DIR, check=True)

        if args.type == "firmware":
            tooling_cmd = ["bash", "./Tools/setup/ubuntu.sh", "--no-sim-tools"]
            target_px4board = PX4_DIR / "boards"/ info.vendor / info.model / f"{info.name}.px4board"
            airframes = PX4_DIR / "ROMFS" / "px4fmu_common" / "init.d" / "airframes"
            target = f"{info.vendor}_{info.model}_{info.name}"
        elif args.type == "sitl":
            tooling_cmd = ["bash", "./Tools/setup/ubuntu.sh"]
            target_px4board = PX4_DIR / "boards"/ info.vendor / "sitl" / f"{info.name}.px4board"
            airframes = PX4_DIR / "ROMFS" / "px4fmu_common" / "init.d-posix" / "airframes" 
            target = f"{info.vendor}_sitl_{info.name}"


        self.logger.info("Install PX4 tooling...")
        run_command(tooling_cmd, cwd=PX4_DIR)

        shutil.copy2(args.path / self.FIRM_MODULES, target_px4board)

        airframes_CMakeLists = airframes / "CMakeLists.txt"
        airframe_file = f"{info.id}_{info.name}"
        target_airframe = airframes / airframe_file

        shutil.copy2(args.path / self.PARMS_FILE, target_airframe)

        self.__prepend_insertion(airframes_CMakeLists, "[4000, 4999] Quadrotor x", airframe_file)

        CMakeLists_init = PX4_DIR / "ROMFS" / "px4fmu_common" / "init.d" / "CMakeLists.txt"

        if info.defualt_components is not None:
            self.logger.info("No components found. Skipping components.")
            components_normalized = " ".join(info.defualt_components) if isinstance(info.defualt_components, list) else info.defualt_components
            self.__prepend_insertion(CMakeLists_init, "rcS", components_normalized)

        self.logger.info(f"Ready to build custom firmware for target {target}")
        run_command(["make", "clean"], cwd=PX4_DIR)
        build_px4 = run_command(["make", target], 
                                cwd=PX4_DIR,
                                stdout=subprocess.PIPE,
                                stderr=subprocess.STDOUT,
                                text=True,  # or encoding='utf-8'
                                capture_output=False
                                )

        if build_px4['returncode'] != 0:
            self.logger.error(f"Failed to build target {target}. {build_px4['stderr']} {build_px4['stdout']} {build_px4['error']}")
            sys.exit(1)


        # shutil.copy2(PX4_DIR / "build" / target / f"{target}.px4", args.output / f"{info.name}_{info.custom_fw_version}.px4")

        # cleaning steps

        # can I do cleaning by using just git ? does it affect the build folder ?

        # target_px4board.unlink() # remove file

    def cleanup(self):
        run_command(['git', 'tag', '-d', self.target_tag], cwd=PX4_DIR, check=True)
        run_command(['git', 'tag', self.original_tag, self.commit_hash], cwd=PX4_DIR, check=True)
        run_command(['git', 'restore', '.'], cwd=PX4_DIR, check=True)
