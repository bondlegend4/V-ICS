#!/bin/bash
set -e

echo "Starting V-ICS Engine Build Process..."

# 1. Define paths based on the v-ics.le root structure
MODBUS_CRATE_PATH="./lunco-modbus"
TARGET_LUNCO_DIR="../mars-colony-sim.git/lunco-sim"

# 2. Verify target directory exists
if [ ! -d "$TARGET_LUNCO_DIR" ]; then
    echo "Error: Could not find lunco-sim at $TARGET_LUNCO_DIR"
    exit 1
fi  

echo "Injecting lunco-modbus crate into the simulation engine..."

# 3. Copy the Modbus crate into the lunco-sim workspace
cp -r $MODBUS_CRATE_PATH $TARGET_LUNCO_DIR/crates/

cd $TARGET_LUNCO_DIR

# 4. Inject the new crate into the Root Workspace Cargo.toml
# This finds the "crates/luncosim" line and adds our crate right below it
sed -i '/"crates\/luncosim",/a \    "crates\/lunco-modbus",' Cargo.toml

# 5. Add the dependency to the luncosim application Cargo.toml
# Checks if it already exists to prevent duplicate appends on re-runs
if ! grep -q "lunco-modbus" crates/luncosim/Cargo.toml; then
    echo "Updating luncosim dependencies..."
    echo "" >> crates/luncosim/Cargo.toml
    echo "[dependencies.lunco-modbus]" >> crates/luncosim/Cargo.toml
    echo "path = \"../lunco-modbus\"" >> crates/luncosim/Cargo.toml
fi

# 6. Inject the Plugin into the Bevy App lifecycle in main.rs
# Checks if already injected, if not, replaces .run() with .add_plugins().run()
if ! grep -q "LunCoModbusPlugin" crates/luncosim/src/main.rs; then
    echo "Modifying luncosim/src/main.rs..."
    sed -i 's/\.run();/.add_plugins(lunco_modbus::LunCoModbusPlugin::default())\n        .run();/' crates/luncosim/src/main.rs
fi

# 7. Build the custom V-ICS binary
echo "Compiling the V-ICS Custom Engine..."
cargo build --release --bin luncosim

echo "========================================================"
echo "Build Complete! V-ICS Engine with Native Modbus Support."
echo "Binary located at: mars-colony-sim.git/lunco-sim/target/release/luncosim"
echo "========================================================"