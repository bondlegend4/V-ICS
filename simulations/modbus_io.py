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
        """
        Write to coils.  For older/newer pymodbus versions,
        use keyword arguments to avoid TypeError.
        """
        # Example: write_coils(address=..., values=..., unit=...) if needed
        write_result = self.client.write_coils(address=register, values=input_values)
        if not write_result.isError():
            print(f"Wrote value to input register {register}: {input_values}")
        else:
            print(f"Error writing to input register: {write_result}")

    def QX_plc(self, output_register_address, count):
        """
        Read coils.  Use keyword arguments for address=, count=, unit=.
        """
        read_result = self.client.read_coils(address=output_register_address, count=count)
        if not read_result.isError():
            output_value = read_result.bits
            print(f"Read value from output register {output_register_address}: {output_value}")
            return output_value
        else:
            print(f"Error reading from output register: {read_result}")

    def IR_plc(self, input_register_address, count, input_values):
        """
        Write to holding/input registers (depending on PLC config).
        Use write_registers(address=..., values=..., unit=...).
        """
        write_result = self.client.write_registers(address=input_register_address, values=input_values)
        if not write_result.isError():
            print(f"Wrote value to input register {input_register_address}: {input_values}")
        else:
            print(f"Error writing to input register: {write_result}")

    def QR_plc(self, output_register_address, count):
        """
        Read holding registers. Use keyword arguments.
        """
        read_result = self.client.read_holding_registers(address=output_register_address, count=count)
        if not read_result.isError():
            output_value = read_result.registers
            print(f"Read value from output register {output_register_address}: {output_value}")
            return output_value
        else:
            print(f"Error reading from output register: {read_result}")
