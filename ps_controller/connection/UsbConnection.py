import glob

import serial

from .BaseConnectionInterface import BaseConnectionInterface
import ps_controller.utilities.OsHelper as osHelper
from ..Constants import *


class UsbConnection(BaseConnectionInterface):
    def __init__(
            self,
            logger,
            serial_link_generator,
            id_message,
            device_verification_func):
        """
        Parameters
        ----------
        logger : object
            A logger object that the connection can use to log events
        serial_link_generator : serial.Serial interface generator
            A function that returns a interface that implements serial.Serial. Allows mocking
        id_message : bytes
            A data package that is sent to the device in order to establish a connection.
            `device_verification_func` function is then used to evaluate the device response
        device_verification_func : function(device_response)
            A function used to establish if device is responsive on given port. First `id_message`
            is sent to the device and then    this function evaluates the device response and returns a bool
        """
        self._logger = logger
        self._serial_link_generator = serial_link_generator
        self._id_message = id_message
        self._device_verification_func = device_verification_func
        self._base_connection = serial_link_generator()

    def connect(self):
        """
        Tries to connect to a PS201 via USB. Returns a bool indicating if connecting was successful
        """
        available_ports = self._available_connections()
        for port in available_ports:
            if self._device_on_port(port):
                self._base_connection.port = port
                self._base_connection.open()
                break
        return self.connected()

    def disconnect(self):
        """
        Disconnects from the currently connected PS201.
        """
        self._base_connection.close()

    def connected(self):
        """
        Returns a bool value indicating if connected to PS201
        """
        return self._base_connection.isOpen()

    def clear_buffer(self):
        """
        Clears the read buffer from the device.
        """
        if self.connected():
            self._base_connection.flushInput()

    def get(self):
        """
        Reads a single response from PS201 and returns them. A single response from PS201 is surrounded
        with START characters. If not connected, None is returned
        """
        if not self.connected():
            return None
        serial_response = self._read_device_response(self._base_connection)
        if serial_response == b'':
            return None
        return serial_response

    def set(self, sending_data):
        """
        Sends sending_data to the connected PS201.
        """
        if not self.connected():
            return
        self._send_to_device(self._base_connection, sending_data)

    def _available_connections(self):
        """Get available usb ports"""
        system_type = osHelper.getCurrentOs()
        available = []
        usb_list = []
        if system_type == osHelper.WINDOWS:
            usb_list = range(256)
        elif system_type == osHelper.OSX:
            usb_list = glob.glob('/dev/tty*') + glob.glob('/dev/cu*')
        elif system_type == osHelper.LINUX:
            usb_list = glob.glob('/dev/ttyS*') + glob.glob('/dev/ttyUSB*')

        for port in usb_list:
            try:
                tmp_connection = self._serial_link_generator()
                tmp_connection.port = port
                tmp_connection.open()
                available.append(tmp_connection.port)
                tmp_connection.close()
            except serial.SerialException:
                pass
        return available

    def _send_to_device(self, serial_connection, data):
        serial_connection.write(data)

    def _read_device_response(self, serial_connection):
        return self._read_line(serial_connection)

    def _read_line(self, serial_connection):
        """Custom readLine method to avoid end of line char issues"""
        line = bytearray()
        start_count = 0
        while True:
            c = serial_connection.read(1)
            if c:
                line += c
            else:
                break

            if c[0] == START:
                start_count += 1
            if start_count == 2:
                break
        return bytes(line)

    def _device_on_port(self, usb_port):
        try:
            tmp_connection = self._serial_link_generator()
            tmp_connection.port = usb_port
            tmp_connection.open()
            self._send_to_device(tmp_connection, self._id_message)
            device_response = self._read_device_response(tmp_connection)
            tmp_connection.close()
            return self._device_verification_func(device_response)
        except Exception as e:
            return False