#!/bin/bash

set -e

NAME_OPTIONS=("platypus")
ROOT_DIR=$PWD
DRONE_NAME=${1:?"DRONE_NAME argument is mandatory"} # TODO check for valid drone name
PX4_VERSION="v1.15.0" # TODO: DRONE SPECIFIC
CUSTOM_VERSION="0.0.1" # TODO: DRONE SPECIFIC

usage() {
  echo "Usage: $0"
  echo ""
  echo "Available drone names:"
  for option in "${NAME_OPTIONS[@]}"; do
      echo "    - ${option}"
  done
  exit 1
}

if [ -z "$1" ]; then
  echo "Error: No argument provided."
  usage
fi

if [[ ! " ${NAME_OPTIONS[@]} " =~ " $1 " ]]; then
  echo "Error: Invalid drone name '$1'."
  usage
fi

if [ ! -d "PX4-Autopilot" ]; then
    git clone https://github.com/PX4/PX4-Autopilot.git --recursive
fi

build_firmware() {
    local px4_version="$1"
    local drone_fw_version="$2"
    local vendor="$3"
    local model="$4"
    local drone_name="$5"

    local temp_tag="${px4_version}-${drone_fw_version}"

    # Navigate to PX4-Autopilot directory
    cd $ROOT_DIR/PX4-Autopilot

    echo "Checking out PX4 firmware version: $px4_version"
    git fetch --all --tags
    git checkout $px4_version
    git submodule sync --recursive
    git submodule update --init --recursive

    # working out the tags for the custom firmware version format
    git tag -f -a "$temp_tag" -m "${temp_tag}"

    bash ./Tools/setup/ubuntu.sh --no-sim-tools
    sudo apt -y install gcc-arm-none-eabi # check https://github.com/PX4/PX4-Autopilot/issues/15719#issuecomment-1582186108

    cd $ROOT_DIR
    cp -r boards/* $ROOT_DIR/PX4-Autopilot/boards/

    cd $ROOT_DIR/PX4-Autopilot

    local target="${vendor}_${model}_${drone_name}"
    make $target

    # # restore the original px4 tag
    git tag -d "$temp_tag"
    git checkout "$px4_version"

    local output="${ROOT_DIR}/${drone_name}_v${drone_fw_version}.px4"
    cp $ROOT_DIR/PX4-Autopilot/build/$target/$target.px4 $output

    echo ""
    echo "==============================================="
    echo "The firmware file has been created in ${output}"
    echo "==============================================="
}

DRONE_NAME=$1

case "$DRONE_NAME" in

    # To add a new drone the following variables are mandatory:
    # PX4_VERSION: the version of the PX4 firmware to build
    # DRONE_FW_VERSION: Drone spe
    #
    # VENDOR: The manufacturer of the board. The vendor name for Pixhawk series boards is "px4".
    # MODEL: The board model.
    # see https://docs.px4.io/main/en/dev_setup/building_px4.html#px4-make-build-targets
    platypus)
        PX4_VERSION="v1.15.0"
        DRONE_FW_VERSION="0.0.1"

        VENDOR="px4"
        MODEL="fmu-v3"
        ;;
    *) echo "Error: Unknown drone name '$1'."; usage ;;
esac

build_firmware "$PX4_VERSION" "$DRONE_FW_VERSION" "$VENDOR" "$MODEL" "$DRONE_NAME"

# if [ "$1" == "all" ]; then
  # Loop through all options except 'all' and execute each action
  # for action in "${VALID_OPTIONS[@]}"; do
  #   if [ "$action" != "all" ]; then
  #     perform_action "$action"
  #   fi
  # done
# else
#
#   build_firmware "$1"
# fi
