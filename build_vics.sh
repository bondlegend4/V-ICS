#!/bin/bash
set -e

echo "Starting V-ICS Engine Build Process..."

# 1. Define paths based on the v-ics.le root structure
MODBUS_CRATE_PATH="./lunco-modbus"
TARGET_LUNCO_DIR="../mars-colony-sim/lunco-sim"

# 2. Verify target directory exists
if [ ! -d "$TARGET_LUNCO_DIR" ]; then
    echo "Error: Could not find lunco-sim at $TARGET_LUNCO_DIR"
    exit 1
fi

echo "Injecting lunco-modbus crate into the simulation engine..."

# 3. Explicitly copy only the necessary source files
echo "Copying source files..."
DEST_DIR="$TARGET_LUNCO_DIR/crates/lunco-modbus"

rm -rf "$DEST_DIR"
mkdir -p "$DEST_DIR"

cp -r "$MODBUS_CRATE_PATH/src" "$DEST_DIR/"
cp -r "$MODBUS_CRATE_PATH/tests" "$DEST_DIR/"
cp "$MODBUS_CRATE_PATH/Cargo.toml" "$DEST_DIR/"
cp "$MODBUS_CRATE_PATH/README.md" "$DEST_DIR/"

# 4. Rewrite the dependency paths (Using perl for macOS compatibility)
echo "Rewriting internal dependency paths for the workspace..."
perl -pi -e 's|\.\./\.\./mars-colony-sim/lunco-sim/crates/lunco-modelica|\.\./lunco-modelica|g' "$DEST_DIR/Cargo.toml"

echo "Aligning Bevy workspace dependencies..."
perl -pi -e 's/^bevy = .*/bevy = { workspace = true }/g' "$DEST_DIR/Cargo.toml"

cd "$TARGET_LUNCO_DIR"

# 5. Inject the new crate into the Root Workspace Cargo.toml
echo "Registering crate in workspace..."
perl -pi -e 's/"crates\/luncosim",/"crates\/luncosim",\n    "crates\/lunco-modbus",/g' Cargo.toml

# 6. Add the dependency to the luncosim application Cargo.toml
if ! grep -q "lunco-modbus" crates/luncosim/Cargo.toml; then
    echo "Updating luncosim dependencies..."
    echo "" >> crates/luncosim/Cargo.toml
    echo "[dependencies.lunco-modbus]" >> crates/luncosim/Cargo.toml
    echo "path = \"../lunco-modbus\"" >> crates/luncosim/Cargo.toml
fi

# 7. Inject the Plugin into the Bevy App lifecycle in main.rs
if ! grep -q "LunCoModbusPlugin" crates/luncosim/src/main.rs; then
    echo "Modifying luncosim/src/main.rs..."
    perl -pi -e 's/\.run\(\);/\.add_plugins\(lunco_modbus::LunCoModbusPlugin::default\(\)\)\n        \.run\(\);/g' crates/luncosim/src/main.rs
fi

# 8. Build the custom V-ICS binary
echo "Compiling the V-ICS Custom Engine..."
cargo build --release --bin luncosim

echo "========================================================"
echo "Build Complete! V-ICS Engine with Native Modbus Support."
echo "Binary located at: mars-colony-sim/lunco-sim/target/release/luncosim"
echo "========================================================"