#!/bin/bash

set -e

ROOT_DIR=$PWD
DRONE_NAME=${1:?"DRONE_NAME argument is mandatory"} # TODO check for valid drone name
PX4_VERSION="v1.15.0" # TODO: DRONE SPECIFIC
CUSTOM_VERSION="0.0.1" # TODO: DRONE SPECIFIC

TEMP_TAG="${PX4_VERSION}-${CUSTOM_VERSION}" # TODO: DRONE SPECIFIC

echo $TEMP_TAG

if [ ! -d "PX4-Autopilot" ]; then
    git clone https://github.com/PX4/PX4-Autopilot.git --recursive
fi

# Navigate to PX4-Autopilot directory
cd $ROOT_DIR/PX4-Autopilot

echo "Checking out PX4 firmware version: $PX4_VERSION"
git fetch --all --tags
git checkout $PX4_VERSION
git submodule sync --recursive
git submodule update --init --recursive

# Set a temporary tag in PX4-Autopilot
echo "Setting temporary tag in PX4-Autopilot: $TEMP_TAG"``
git tag -f $TEMP_TAG

# Ensure the temporary tag is removed at the end of the script
# trap 'echo "Removing temporary tag $TEMP_TAG"; git tag -d $TEMP_TAG' EXIT ERR

echo "This take some time, just wait for it..."
bash ./Tools/setup/ubuntu.sh --no-sim-tools
sudo apt -y install gcc-arm-none-eabi # check https://github.com/PX4/PX4-Autopilot/issues/15719#issuecomment-1582186108

# Return to the root directory and copy custom configuration files into PX4-Autopilot
cd $ROOT_DIR
cp -r boards/* ./PX4-Autopilot/boards/

TARGET="px4_fmu-v3_${DRONE_NAME}" # TODO: DRONE SPECIFIC

cd $ROOT_DIR/PX4-Autopilot
make $TARGET

cp $ROOT_DIR/PX4-Autopilot/build/$TARGET/$TARGET.px4 "${ROOT_DIR}/${DRONE_NAME}_${CUSTOM_VERSION}".px4
