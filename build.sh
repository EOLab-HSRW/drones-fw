#!/bin/bash

set -e

NAME_OPTIONS=("platypus" "sar" "phoenix" "condor" "protoflyer" "all")
ROOT_DIR=$PWD

usage() {
  echo "Usage: $0 DRONE_NAME"
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
  echo "Error: Invalid drone name '$1'"
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
    cp -r ROMFS/* $ROOT_DIR/PX4-Autopilot/ROMFS/
    # add same frame files into the posix platform
    cp -r ROMFS/px4fmu_common/init.d/airframes/* $ROOT_DIR/PX4-Autopilot/ROMFS/px4fmu_common/init.d-posix/airframes/

    # Add the radio parameters to the firmware
    sed -i '/rc.sensors/a\rc.radiomaster_tx16s' $ROOT_DIR/PX4-Autopilot/ROMFS/px4fmu_common/init.d/CMakeLists.txt
    # Add radio parameters to SIMULATION
    sed -i '/rcS/a\rc.radiomaster_tx16s' $ROOT_DIR/PX4-Autopilot/ROMFS/px4fmu_common/init.d-posix/CMakeLists.txt

    # Patch the airframes file
    # [IMPORTANT] DO NOT CHANGE THE IDENTATION
    # START
sed -i "/Quadrotor x/{
r airframes.eolab
}" $ROOT_DIR/PX4-Autopilot/ROMFS/px4fmu_common/init.d/airframes/CMakeLists.txt
    # END

    # Add airframes to sim
    # START
sed -i "/px4_add_romfs_files/{
r airframes.eolab
}" $ROOT_DIR/PX4-Autopilot/ROMFS/px4fmu_common/init.d-posix/airframes/CMakeLists.txt
    # END

    cd $ROOT_DIR/PX4-Autopilot

    rm -rf build
    make clean
    local target="${vendor}_${model}_${drone_name}"
    make $target

    # restore the original px4 tag
    git tag -d "$temp_tag"
    git checkout "$px4_version"
    # restore airframes patch
    sed -i "/### BEGIN EOLAB DRONES ###/,/### END EOLAB DRONES ###/d" $ROOT_DIR/PX4-Autopilot/ROMFS/px4fmu_common/init.d/airframes/CMakeLists.txt
    sed -i "/### BEGIN EOLAB DRONES ###/,/### END EOLAB DRONES ###/d" $ROOT_DIR/PX4-Autopilot/ROMFS/px4fmu_common/init.d-posix/airframes/CMakeLists.txt
    sed -i '/rc.radiomaster_tx16s/d' $ROOT_DIR/PX4-Autopilot/ROMFS/px4fmu_common/init.d/CMakeLists.txt
    sed -i '/rc.radiomaster_tx16s/d' $ROOT_DIR/PX4-Autopilot/ROMFS/px4fmu_common/init.d-posix/CMakeLists.txt

    local output="${ROOT_DIR}/${drone_name}_v${drone_fw_version}.px4"
    cp $ROOT_DIR/PX4-Autopilot/build/$target/$target.px4 $output

    echo ""
    echo "==============================================="
    echo "The firmware file has been created in ${output}"
    echo "==============================================="

}

build_drone() {
    local drone_name=$1

    drone_name=$1

    # To add a new drone the following variables are mandatory:
    # PX4_VERSION: the version of the PX4 firmware to build
    # DRONE_FW_VERSION: Drone spe
    #
    # VENDOR: The manufacturer of the board. The vendor name for Pixhawk series boards is "px4".
    # MODEL: The board model.
    # see https://docs.px4.io/main/en/dev_setup/building_px4.html#px4-make-build-targets
    case "$drone_name" in
        platypus)
            PX4_VERSION="v1.15.4"
            DRONE_FW_VERSION="0.0.1"

            VENDOR="px4"
            MODEL="fmu-v3"
            ;;
        sar)
            PX4_VERSION="v1.15.4"
            DRONE_FW_VERSION="0.0.1"

            VENDOR="px4"
            MODEL="fmu-v6x"
            ;;
        phoenix)
            PX4_VERSION="v1.15.4"
            DRONE_FW_VERSION="0.0.1"

            VENDOR="px4"
            MODEL="fmu-v3"
            ;;
        condor)
            PX4_VERSION="v1.15.4"
            DRONE_FW_VERSION="0.0.1"

            VENDOR="px4"
            MODEL="fmu-v3"
            ;;
        protoflyer)
            PX4_VERSION="v1.15.4"
            DRONE_FW_VERSION="0.0.1"

            VENDOR="px4"
            MODEL="fmu-v3"
            ;;
        # demo)
        #     PX4_VERSION="v1.12.3"
        #     DRONE_FW_VERSION="1.2.0"
        #     VENDOR="px4"
        #     MODEL="fmu-v5"
        #     ;;
        *)
            echo "Error: Unknown drone name '$1'."
            usage
            ;;
    esac

    build_firmware "$PX4_VERSION" "$DRONE_FW_VERSION" "$VENDOR" "$MODEL" "$drone_name"
}

if [ "$1" == "all" ]; then
    echo "build all firmwares"
    for drone in "${NAME_OPTIONS[@]}"; do
        if [ "$drone" != "all" ]; then
            build_drone "$drone"
        fi
    done
else
    build_drone "$1"
fi
