from pymodbus.client import ModbusTcpClient
from pymodbus.exceptions import ModbusException

class ModbusIO:
    def __init__(self, ip, port):
        self.client = ModbusTcpClient(ip, port=port)

    def connect(self):
        return self.client.connect()

    def close(self):
        self.client.close()

    def IX_plc(self, register, count, input_values):
        # Write `value` to coils at `address`.
        write_result = self.client.write_coils(register, input_values)
        if not write_result.isError():  # Check if the write was successful
            print(f"Wrote value to input register {register}: {input_values}")
        else:
            print(f"Error writing to input register: {write_result}")

    def QX_plc(self, output_register_address, count):
        # Reads `count` coils from a given address.
        read_result = self.client.read_coils(output_register_address, count)
        if not read_result.isError():  # Check if the read was successful
            output_value = read_result.bits
            print(f"Read value from output register {output_register_address}: {output_value}")
            return output_value
        else:
            print(f"Error reading from output register: {read_result}")

    def IR_plc(self, input_register_address, count, input_values):
        # Write list of `values` to input registers starting at `address`.
        write_result = self.client.write_registers(input_register_address, input_values)
        if not write_result.isError():  # Check if the write was successful
            print(f"Wrote value to input register {input_register_address}: {input_values}")
        else:
            print(f"Error writing to input register: {write_result}")

    def QR_plc(self, output_register_address, count):
        # Read `count` number of holding registers starting at `address`.
        read_result = self.client.read_holding_registers(output_register_address, count)
        if not read_result.isError():  # Check if the read was successful
            output_value = read_result.registers
            print(f"Read value from output register {output_register_address}: {output_value}")
            return output_value
        else:
            print(f"Error reading from output register: {read_result}")
