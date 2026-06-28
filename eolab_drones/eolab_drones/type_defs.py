from typing import TypedDict, TypeAlias

DroneInfo: TypeAlias = dict[str, dict]
Drones: TypeAlias = dict[str, DroneInfo]
Components: TypeAlias = list[str]

class Catalog(TypedDict):
    drones: Drones
    components: Components
