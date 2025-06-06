try:
    from importlib.resources import files  # Python >=3.9
except ImportError:
    from importlib_resources import files  # Python <3.9

from pathlib import Path

# TODO fix data files import for editable packages
# this is mainly for development
CATALOG_DIR = Path(files(__package__)) / "catalog"
DRONES_DIR = CATALOG_DIR / "drones"
COMPONENTS_DIR = CATALOG_DIR / "components"
