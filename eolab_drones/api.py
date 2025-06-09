from types import NoneType
from typing import Union
from pathlib import Path
import easy_px4
from eolab_drones.paths import DRONES_DIR, COMPONENTS_DIR

def get_catalog() -> dict[str, dict]:
    """
    Returns dictionary with EOLab's drones and components.
    """

    drones = {}

    components = [f.name for f in COMPONENTS_DIR.iterdir() if f.is_file()]

    for info_file in DRONES_DIR.rglob("info.toml"):
        info_dict = easy_px4.load_info(info_file)
        name = info_dict.pop("name")  # remove and get the 'name' key
        drones[name] = info_dict

    return {"drones": drones, "components": components}

def get_drones() -> dict[str, dict]:
    """
    Returns a dictionary with EOLab's drone catalog.
    """
    return get_catalog().get("drones")

def get_components() -> list:
    """
    Returns list of names of EOLab's components.
    """
    return get_catalog().get("components")

def __check_drone(drone: str) -> Union[dict, NoneType]:
    """
    Checks if the given drone is in the catalog.
    """

    return get_drones().get(drone, None)


def get_id(drone: str) -> Union[int, NoneType]:
    """
    Returns the id of a given drone in the EOLab's drone catalog.


    Return: int if the name of the drone is in the catalog, None otherwise.
    """
    drone_info = __check_drone(drone)
    if drone_info:
        return drone_info["id"]
    else:
        return None

def get_build_dir(drone: str, build_type: str = "sitl") -> Union[Path, NoneType]:

    drone_info = __check_drone(drone)

    general_build = easy_px4.get_build_dir()

    if build_type == "sitl":
         drone_build = general_build / f"px4_sitl_{drone}"
    else:
        drone_build = general_build / f"{drone_info['vendor']}_{drone_info['model']}_{drone}"

    if not drone_build.is_dir() and not drone_build.exists():
        return None

    return drone_build


def get_stil_bin(drone: str) -> Union[Path, NoneType]:

    drone_build = get_build_dir(drone, "sitl")

    if not drone_build:
        return None

    return drone_build / "bin" / "px4"
