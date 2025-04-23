# Using pyModbusTCP as it seems simpler for basic reads/writes
from pyModbusTCP.client import ModbusClient
from pyModbusTCP.utils import encode_ieee, decode_ieee, \
                                word_list_to_long, long_list_to_word
import logging
import time
from typing import Union, List, Any, Dict # Make sure Union and Any are imported here

logger = logging.getLogger(__name__)

class ModbusIO:
    """Helper class for Modbus TCP Communication with OpenPLC."""
    def __init__(self, host="127.0.0.1", port=502, timeout=1.0, auto_open=True, debug=False):
        self._host = host
        self._port = port
        self._client = ModbusClient(host=host, port=port, timeout=timeout, auto_open=auto_open)
        self._last_ok_time = 0.0

    def is_connected(self):
        """Check if the client is currently connected."""
        return self._client.is_open

    def connect(self) -> bool:
        """Attempt to connect or reconnect."""
        if self._client.is_open:
            return True
        logger.info(f"Attempting Modbus connection to {self._host}:{self._port}")
        if self._client.open():
            logger.info("Modbus connection successful.")
            self._last_ok_time = time.time()
            return True
        else:
            logger.warning("Modbus connection failed.")
            return False

    def close(self):
        """Close the Modbus connection."""
        if self._client.is_open:
            logger.info("Closing Modbus connection.")
            self._client.close()

    def get_last_ok_time(self):
        """Get the timestamp of the last successful communication."""
        return self._last_ok_time

    def read_coils(self, start_addr: int, count: int) -> Union[List[bool], None]:
        """Read Coils (QX). Returns list of bools or None on error."""
        if not self.is_connected():
            if not self.connect():
                return None
        try:
            coils = self._client.read_coils(start_addr, count)
            if coils:
                self._last_ok_time = time.time()
                return coils
            else:
                logger.warning(f"Modbus read_coils failed (Addr: {start_addr}, Count: {count}). Error: {self._client.last_error()}, Exc: {self._client.last_exception()}")
                self.close() # Assume connection issue
                return None
        except Exception as e:
            logger.error(f"Exception during Modbus read_coils: {e}")
            self.close()
            return None

    def write_single_coil(self, addr: int, value: bool) -> bool:
        """Write a single Coil (QX). Returns True on success."""
        if not self.is_connected():
            if not self.connect():
                return False
        try:
            success = self._client.write_single_coil(addr, value)
            if success:
                self._last_ok_time = time.time()
                return True
            else:
                logger.warning(f"Modbus write_single_coil failed (Addr: {addr}, Value: {value}). Error: {self._client.last_error()}, Exc: {self._client.last_exception()}")
                self.close()
                return False
        except Exception as e:
            logger.error(f"Exception during Modbus write_single_coil: {e}")
            self.close()
            return False

    def read_holding_registers(self, start_addr: int, count: int) -> list[int] | None:
        """Read Holding Registers (%MW). Returns list of ints or None on error."""
        # NOTE: OpenPLC typically uses Input Registers (%IW) for inputs,
        # Holding Registers (%MW) might be used for internal state or outputs.
        # Adjust function if you primarily use Input Registers.
        if not self.is_connected():
            if not self.connect():
                return None
        try:
            regs = self._client.read_holding_registers(start_addr, count)
            if regs:
                self._last_ok_time = time.time()
                return regs
            else:
                logger.warning(f"Modbus read_holding_registers failed (Addr: {start_addr}, Count: {count}). Error: {self._client.last_error()}, Exc: {self._client.last_exception()}")
                self.close()
                return None
        except Exception as e:
            logger.error(f"Exception during Modbus read_holding_registers: {e}")
            self.close()
            return None

    def read_input_registers(self, start_addr: int, count: int) -> list[int] | None:
        """Read Input Registers (%IW). Returns list of ints or None on error."""
        if not self.is_connected():
            if not self.connect():
                return None
        try:
            regs = self._client.read_input_registers(start_addr, count)
            if regs:
                self._last_ok_time = time.time()
                return regs
            else:
                logger.warning(f"Modbus read_input_registers failed (Addr: {start_addr}, Count: {count}). Error: {self._client.last_error()}, Exc: {self._client.last_exception()}")
                self.close()
                return None
        except Exception as e:
            logger.error(f"Exception during Modbus read_input_registers: {e}")
            self.close()
            return None

    def write_multiple_registers(self, start_addr: int, values: list[int]) -> bool:
        """Write Multiple Holding Registers (%MW). Returns True on success."""
        # NOTE: OpenPLC usually doesn't allow writing directly to Input Registers (%IW).
        # This function targets Holding Registers (%MW).
        if not self.is_connected():
            if not self.connect():
                return False
        try:
            success = self._client.write_multiple_registers(start_addr, values)
            if success:
                self._last_ok_time = time.time()
                return True
            else:
                logger.warning(f"Modbus write_multiple_registers failed (Addr: {start_addr}). Error: {self._client.last_error()}, Exc: {self._client.last_exception()}")
                self.close()
                return False
        except Exception as e:
            logger.error(f"Exception during Modbus write_multiple_registers: {e}")
            self.close()
            return False

    # --- Convenience Methods from your original file (using new backend) ---
    def QX_plc(self, address, count):
        """Read coils."""
        return self.read_coils(address, count)

    def IR_plc(self, address, count, values=None):
        """Write to Input Registers (Not typically possible directly via Modbus write).
           This method likely intended to write to *Holding* Registers used as inputs.
           Let's map it to write_multiple_registers for compatibility assumption.
        """
        if values is None:
             logger.error("IR_plc called without values to write.")
             return False # Or raise error
        # Assuming the intent was to write to Holding Registers mapped to inputs internally
        logger.warning("IR_plc mapped to write_multiple_registers (Holding Registers). Ensure PLC logic handles this.")
        return self.write_multiple_registers(address, values)


    def QR_plc(self, address, count):
        """Read Holding or Input Registers. Prioritize Input Registers for sensors."""
        # Try Input Registers first as they are common for sensor inputs in OpenPLC
        input_regs = self.read_input_registers(address, count)
        if input_regs is not None:
            return input_regs
        # Fallback to Holding Registers if Input Registers fail or aren't used
        logger.debug(f"Falling back to read_holding_registers for addr {address}")
        return self.read_holding_registers(address, count)