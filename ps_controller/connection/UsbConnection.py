import glob

import serial

from .BaseConnectionInterface import BaseConnectionInterface
import ps_controller.utilities.OsHelper as osHelper
from ..logging.CustomLoggerInterface import CustomLoggerInterface


class UsbConnection(BaseConnectionInterface):
    def __init__(
            self,
            logger: CustomLoggerInterface,
            serial_link_generator,
            id_message: bytes,
            device_verification_func,
            device_start_end_byte: int):
        """
        Parameters
        ----------
        logger
            A logger object that the connection can use to log events
        serial_link_generator : serial.Serial interface generator
            A function that returns a interface that implements serial.Serial. Allows mocking
        id_message : bytes
            A data package that is sent to the device in order to establish a connection.
            `device_verification_func` function is then used to evaluate the device response
        device_verification_func : function(device_response)
            A function used to establish if device is responsive on given port. First `id_message`
            is sent to the device and then    this function evaluates the device response and returns a bool
        device_start_byte:
            The expected byte that starts and ends a transmission from the device
        """
        self._logger = logger
        self._serial_link_generator = serial_link_generator
        self._id_message = id_message
        self._device_verification_func = device_verification_func
        self._base_connection = serial_link_generator()
        self._connected = False
        self._device_start_end_byte = device_start_end_byte

    def connect(self):
        if self._connected:
            return True
        available_ports = self._available_connections()
        for port in available_ports:
            if self._device_on_port(port):
                if self._base_connection.isOpen():
                    self._base_connection.close()
                self._base_connection.port = port
                self._base_connection.open()
                self._connected = self._base_connection.isOpen()

                break
        return self._connected

    def disconnect(self):
        self._connected = False
        self._base_connection.close()

    def connected(self):
        return self._connected

    def get(self):
        try:
            serial_response = self._read_device_response(self._base_connection)
            if serial_response == b'':
                return None
            return serial_response
        except serial.SerialException:
            self._connected = False

    def set(self, sending_data):
        try:
            self._send_to_device(self._base_connection, sending_data)
        except serial.SerialException:
            self._connected = False

    def has_available_ports(self) -> bool:
        usb_ports = self._available_ports()
        for port in usb_ports:
            try:
                tmp_connection = self._serial_link_generator()
                tmp_connection.port = port
                tmp_connection.open()
                tmp_connection.close()
                return True
            except serial.SerialException:
                pass
        return False

    def _available_connections(self) -> list:
        available = []
        usb_ports = self._available_ports()
        for port in usb_ports:
            try:
                tmp_connection = self._serial_link_generator()
                tmp_connection.port = port
                tmp_connection.open()
                available.append(tmp_connection.port)
                tmp_connection.close()
            except serial.SerialException:
                pass
        return available

    def _available_ports(self):
        """Get available usb ports"""
        system_type = osHelper.get_current_os()
        usb_ports = []
        if system_type == osHelper.WINDOWS:
            usb_ports = range(256)
        elif system_type == osHelper.OSX:
            usb_ports = glob.glob('/dev/tty*') + glob.glob('/dev/cu*')
        elif system_type == osHelper.LINUX:
            usb_ports = glob.glob('/dev/ttyS*') + glob.glob('/dev/ttyUSB*')
        return usb_ports

    def _send_to_device(self, serial_connection, data: bytes):
        serial_connection.write(data)

    def _read_device_response(self, serial_connection: serial.Serial) -> bytearray:
        return self._read_line(serial_connection)

    def _read_line(self, serial_connection: serial.Serial) -> bytearray:
        """Custom readLine method to avoid end of line char issues"""
        line = bytearray()
        start_count = 0
        while True:
            c = serial_connection.read(1)
            if c:
                line += c
            else:
                break

            if c[0] == self._device_start_end_byte:
                start_count += 1
            if start_count == 2:
                break
        return line

    def _device_on_port(self, usb_port):
        try:
            tmp_connection = self._serial_link_generator()
            tmp_connection.port = usb_port
            tmp_connection.open()
            self._send_to_device(tmp_connection, self._id_message)
            self._logger.log("Sending handshake data on port " + str(usb_port))
            device_serial_response = self._read_device_response(tmp_connection)
            tmp_connection.close()
            return self._device_verification_func(device_serial_response, usb_port)
        except serial.SerialException:
            return False
