from pymodbus.client import ModbusTcpClient
from pymodbus.exceptions import ModbusException

class ModbusIO:
    def __init__(self, ip, port):
        self.client = ModbusTcpClient(ip, port=port)

    def connect(self):
        return self.client.connect()

    def close(self):
        self.client.close()
            
    def IX_plc (register, count, input_values):
        # Write `value` to coil at `address`.
        input_register_address = 0  # %QW0.0 in the PLC is Modbus address 0
        write_result = client.write_coils(input_register_address, count, input_values)
        if not write_result.isError():  # Check if the write was successful
            print(f"Wrote value to input register %IW0.0: {write_result}")
        else:
            print(f"Error writing to output register: {write_result}")

    def QX_plc (output_register_address, count, client):
        # Reads `count` coils from a given slave starting at `address`.
        read_result = client.read_coils(output_register_address, count, client)
        output_value = read_result.registers
        if not write_result.isError():  # Check if the write was successful
            print(f"Wrote value to output register %QW0.0: {output_value}")
        else:
            print(f"Error writing to output register: {read_result}")

    def IR_plc (input_register_address, count, input_values):
        # Write list of `values` to registers starting at `address`.
        write_result = client.write_register(input_register_address, count, input_values)
        if not write_result.isError():  # Check if the write was successful
            print(f"Wrote value to input register %IW0.0: {write_result}")
        else:
            print(f"Error writing to output register: {write_result}")

    def QR_plc (output_register_address, count):
        # Read `count` number of holding registers starting at `address`.
        read_result = client.read_holding_registers(output_register_address, count)
        output_value = read_result.registers
        if not write_result.isError():  # Check if the write was successful
            print(f"Wrote value to output register %QW0.0: {output_value}")
        else:
            print(f"Error writing to output register: {read_result}")