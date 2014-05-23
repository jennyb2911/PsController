import unittest
from ps_controller.connection.UsbConnection import UsbConnection
from ps_controller.Constants import *


class TestUsbConnection(unittest.TestCase):

    def setUp(self):
        self._test_connection = UsbConnection(
            logger=None,
            serial_link_generator=lambda: SerialLinkMock(baud_rate=9600, timeout=0.1),
            id_message=None,
            device_verification_func=lambda x: True)

    def test_should_start_disconnected(self):
        self.assertFalse(self._test_connection.connected(), "Should start disconnected")

    def test_connecting_works(self):
        self._test_connection.connect()
        self.assertTrue(self._test_connection.connected(), "Should be connected")

    def test_connecting_twice_works(self):
        self._test_connection.connect()
        self._test_connection.connect()
        self.assertTrue(self._test_connection.connected(),
                        "Connecting twice should still leave connection connected")

    def test_disconnecting_works(self):
        self._test_connection.connect()
        self._test_connection.disconnect()
        self.assertFalse(self._test_connection.connected(),
                         "Manually disconnecting. Should not be connected")

    def test_disconnecting_twice_works(self):
        self._test_connection.connect()
        self._test_connection.disconnect()
        self._test_connection.disconnect()
        self.assertFalse(self._test_connection.connected(),
                         "Manually disconnecting twice. Should not be connected")

    def test_reconnecting_works(self):
        self._test_connection.connect()
        self._test_connection.disconnect()
        self._test_connection.connect()
        self.assertTrue(self._test_connection.connected(),
                        "Connecting after disconnecting should work")

    def test_setting_values(self):
        #Check for exception
        self._test_connection.set(None)
        self._test_connection.set(_get_normal_single_data_package())

    def test_getting_from_empty_connection(self):
        self.assertEquals(None, self._test_connection.get(),
                          "A new connection should not contain any values")

    def test_getting_values_from_disconnected(self):
        self._test_connection._base_connection.set_read_return_value(_get_normal_single_data_package())
        self.assertEquals(None, self._test_connection.get(),
                          "A disconnected connection should not return any values")

    def test_getting_values(self):
        self._test_connection._base_connection.set_read_return_value(_get_normal_single_data_package())
        self.assertEquals(None, self._test_connection.get(),
                          "A disconnected connection should not return any values")
        self._test_connection.connect()
        self.assertEquals(_get_normal_single_data_package(), self._test_connection.get(),
                          "A connected connection should return the mock set values")
        self.assertEquals(None, self._test_connection.get(),
                          "We should already have gotten the values from connection. Should be empty now")

    def test_getting_two_values(self):
        self._test_connection.connect()
        self._test_connection._base_connection.set_read_return_value(_get_normal_double_data_package())
        self.assertEquals(_get_normal_single_data_package(), self._test_connection.get(),
                          "Should only get the first half of the double message")
        self.assertEquals(_get_normal_single_data_package(), self._test_connection.get(),
                          "Should only get the second half of the double message")

    def test_clearing_buffer(self):
        self._test_connection.connect()
        self._test_connection._base_connection.set_read_return_value(self._test_connection.get())
        self._test_connection.clear_buffer()
        self.assertEquals(None, self._test_connection.get(),
                          "Already cleared the buffer so nothing should come back")

if __name__ == '__main__':
    unittest.main()


def _get_normal_single_data_package():
        """
        Gets a normal single data package. This is the normal case
        where the data starts and ends with a START char
        """
        byte_array = bytearray()
        byte_array.append(START)
        byte_array.append(1)
        byte_array.append(2)
        byte_array.append(3)
        byte_array.append(4)
        byte_array.append(5)
        byte_array.append(START)
        return byte_array

def _get_normal_double_data_package():
        """
        Gets a normal double data package. This is the normal case
        where the data starts and ends with a START char for bothc packages
        """
        byte_array = bytearray()
        byte_array.append(START)
        byte_array.append(1)
        byte_array.append(2)
        byte_array.append(3)
        byte_array.append(4)
        byte_array.append(5)
        byte_array.append(START)
        byte_array.append(START)
        byte_array.append(1)
        byte_array.append(2)
        byte_array.append(3)
        byte_array.append(4)
        byte_array.append(5)
        byte_array.append(START)
        return byte_array


class SerialLinkMock:
    def __init__(self, baud_rate, timeout):
        self._port = None
        self._baud_rate = baud_rate
        self._timeout = timeout

        self._connected = False
        self._return_read_value = []

    def open(self):
        self._connected = True

    def close(self):
        self._connected = False

    def isOpen(self):
        return self._connected

    def flushInput(self):
        self._return_read_value = []

    def read(self, number_of_bytes):
        try:
            return_value = self._return_read_value[0:number_of_bytes]
            self._return_read_value = self._return_read_value[number_of_bytes:]
            return return_value
        except Exception as e:
            pass

    def write(self, data):
        pass

    def set_read_return_value(self, data):
        self._return_read_value = data