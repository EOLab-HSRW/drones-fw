import pytest
from eolab_drones import api

def test_get_catalog() -> None:
    catalog = api.get_catalog()
    assert isinstance(catalog, dict)
    assert "drones" in catalog
    assert "components" in catalog

def test_get_drones() -> None:
    drones = api.get_drones()
    assert isinstance(drones, dict)

def test_get_components() -> None:
    components = api.get_components()
    assert isinstance(components, list)

def test_get_components_path() -> None:
    path = api.get_components_path()
    assert isinstance(path, str)
