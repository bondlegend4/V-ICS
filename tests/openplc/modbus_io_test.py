import unittest
from unittest.mock import patch, MagicMock
from modbus_io import ModbusIO
from pymodbus.exceptions import ModbusException


class TestModbusIO(unittest.TestCase):

    @patch('modbus_io.ModbusTcpClient')
    def setUp(self, MockModbusTcpClient):
        # Mock the Modbus client
        self.mock_client = MockModbusTcpClient.return_value
        # Create an instance of the ModbusIO class for testing
        self.modbus_io = ModbusIO('127.0.0.1', 502)

    def test_connect_success(self):
        self.mock_client.connect.return_value = True
        result = self.modbus_io.connect()
        self.assertTrue(result)
        self.mock_client.connect.assert_called_once()

    def test_IX_plc_valid(self):
        self.mock_client.write_coils.return_value.isError.return_value = False
        self.modbus_io.IX_plc(0, 1, [True])  # Valid input: True/False
        self.mock_client.write_coils.assert_called_once_with(0, [True])

    def test_IX_plc_invalid(self):
        with self.assertRaises(ValueError):
            self.modbus_io.IX_plc(0, 1, [1])  # Invalid input: Integer instead of True/False

    def test_QX_plc_valid(self):
        self.mock_client.read_coils.return_value.isError.return_value = False
        self.mock_client.read_coils.return_value.bits = [True]
        result = self.modbus_io.QX_plc(0, 1)
        self.assertEqual(result, [True])

    def test_IR_plc_valid(self):
        self.mock_client.write_registers.return_value.isError.return_value = False
        self.modbus_io.IR_plc(0, 1, [255])  # Valid input: 8-bit integer
        self.mock_client.write_registers.assert_called_once_with(0, [255])

        self.modbus_io.IR_plc(0, 1, [65535])  # Valid input: 16-bit integer
        self.mock_client.write_registers.assert_called_with(0, [65535])

        self.modbus_io.IR_plc(0, 1, [4294967295])  # Valid input: 32-bit integer
        self.mock_client.write_registers.assert_called_with(0, [4294967295])

    def test_IR_plc_invalid(self):
        with self.assertRaises(ValueError):
            self.modbus_io.IR_plc(0, 1, [5000000000])  # Invalid: 33-bit integer

    def test_QR_plc_valid(self):
        self.mock_client.read_holding_registers.return_value.isError.return_value = False
        self.mock_client.read_holding_registers.return_value.registers = [255]
        result = self.modbus_io.QR_plc(0, 1)
        self.assertEqual(result, [255])


if __name__ == '__main__':
    unittest.main()
