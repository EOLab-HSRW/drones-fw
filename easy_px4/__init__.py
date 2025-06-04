CATALOG: dict[str, dict]  = {
    "protoflyer": {
        "frame_id": 22105
    },
    "phoenix": {
        "frame_id": 22103
    }
}

def get_drones() -> list:

    return CATALOG.keys()

def get_frame_id(drone_name: str) -> str:

    normalized_name = drone_name.lower()

    if normalized_name in CATALOG.keys():
        return str(CATALOG[normalized_name]["frame_id"])
    else:
        raise Exception("not a drone name in the catalog")


from .utils.info import load_info
from .utils.directory import load_directory
from types import SimpleNamespace

utils = SimpleNamespace(
    load_directory=load_directory,
    load_info=load_info
)

__all__ = [
    "utils"
]
