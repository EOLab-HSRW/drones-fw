import sys
import shutil
from setuptools import setup, find_packages
from pathlib import Path

if not sys.platform.startswith("linux"):
    sys.stderr.write("This package is deliberately restricted to GNU/Linux systems.")
    sys.exit(1)

for tool in ['git', 'dpkg-deb']:
    if shutil.which(tool) is None:
        sys.stderr.write(f"Missing system dependency: {tool}. Please install it with 'sudo apt install {tool}'")
        sys.exit(1)

__package__ = "eolab_drones"

with (Path(__file__).resolve().parent / "README.md").open(encoding='utf-8') as f:
    long_description = f.read()

setup(
    name=__package__,
    version='0.0.3',
    url='https://github.com/EOLab-HSRW/drones-fw.git',
    author='Harley Lara',
    author_email='harley.lara@outlook.com',
    description="Configs and firmwares for EOLab's drones.",
    long_description=long_description,
    long_description_content_type='text/markdown',
    packages=find_packages(),
    python_requires='>=3.10',
    install_requires=[
        "easy_px4_utils"
    ],
    include_package_data=True,
    entry_points={
        "console_scripts": [
            f"{__package__} = {__package__}.main:main",
        ],
    },
)
