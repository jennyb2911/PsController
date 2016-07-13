from ..DeviceValues import DeviceValues
from ..connection.BaseConnectionInterface import BaseConnectionInterface


class BaseProtocolInterface:
    def __init__(self, connection: BaseConnectionInterface):
        self._connection = connection

    def connect(self) -> bool:
        """
        Tries to connect to PS201
        """
        raise NotImplementedError()

    def connected(self) -> bool:
        """
        Returns if connect to PS201
        """
        raise NotImplementedError()

    def authentication_errors_on_machine(self) -> bool:
        """
        Returns if machine has trouble connecting to devices because of authentication issues
        """
        raise NotImplementedError()

    def get_all_values(self) -> DeviceValues:
        """
        Returns the current values of the connected PS201.
        Throws SerialException if not connected
        """
        raise NotImplementedError()

    def set_target_voltage(self, voltage: float):
        """
        Set the target voltage of the connected PS201.
        To set 1V then set voltage value to 1000
        Throws SerialException if not connected
        """
        raise NotImplementedError()

    def set_target_current(self, current: int):
        """
        Set the target current of the connected PS201.
        To set to 1A set the current value to 1000
        Throws SerialException if not connected
        """
        raise NotImplementedError()

    def set_device_is_on(self, is_on: bool):
        """
        Set if connected PS201 is on or off
        Throws SerialException if not connected
        """
        raise NotImplementedError()
