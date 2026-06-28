from typing import Union
from eolab_drones.type_defs import (
    Catalog,
    Drones,
    DroneInfo,
    Components
)
from eolab_drones.paths import DRONES_DIR, COMPONENTS_DIR
import easy_px4_utils

def get_catalog() -> Catalog:
    """
    Returns dictionary with EOLab's drones and components.
    """

    drones = {}

    components = [f.name for f in COMPONENTS_DIR.iterdir() if f.is_file()]

    for info_file in DRONES_DIR.rglob("info.toml"):
        info_dict = easy_px4_utils.load_info_dict(info_file)
        name = info_dict["name"]
        drones[name] = info_dict

    return {"drones": drones, "components": components}

def get_drones() -> Union[Drones, None]:
    """
    Returns a dictionary with EOLab's drone catalog.
    """
    return get_catalog().get("drones")

def get_drone(name: str) -> Union[DroneInfo, None]:
    """
    Returns drones specific information
    """
    drones = get_drones()
    if drones is not None:
        return drones.get(name)
    return None

def get_components() -> Union[Components, None]:
    """
    Returns list of names of EOLab's components.
    """
    components = get_catalog().get("components")
    if components is not None:
        return components
    return None

def get_id(drone_name: str) -> Union[int, None]:
    """
    Returns the id of a given drone in the EOLab's drone catalog.


    Return: int if the name of the drone is in the catalog, None otherwise.
    """
    drone = get_drone(drone_name)
    if drone is not None:
        return int(drone["id"])
    return None

def get_drone_path(drone_name: str) -> str:
    """
    Returns dictionary containing drone information.
    """
    drone = get_drone(drone_name)
    if drone is not None:
        return str((DRONES_DIR / drone_name).resolve())
    return ""

def get_components_path() -> str:
    """
    Returns path to components files.
    """
    return str(COMPONENTS_DIR.resolve())
