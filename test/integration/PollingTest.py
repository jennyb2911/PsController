"""
This is an integration test script. It tests every voltage value from 0 - (InputVoltage-4) by going through
increments of 0.1 V for a low target current. Then it sets a low voltage and goes through set current of
0 - 1000 mA. In this second run the goal is simply to see if every set value is correct and that
communication between device and computer behaves as expected.

The test condition are
 - target voltage and current are the same as what was set
 - output voltage is closer to the set values then a predefined deviation

Preconditions:
- DPS201 is connected to the computer via usb
- DPS201 is powered on and with input voltage > 4V
"""

import time

from ps_controller.Control.Controller import Controller
from ps_controller.Model.Model import Model


control = Controller(Model=Model(), threaded=False)
MAX_VOLTAGE_PERCENTAGE_DEVIATION = 0.02
MAX_VOLTAGE_ABSOLUTE_DEVIATION = 0.21

MAX_CURRENT_PERCENTAGE_DEVIATION = 0.02
MAX_CURRENT_ABSOLUTE_DEVIATION = 21

TARGET_CURRENT = 10
SLEEP_BETWEEN_STEPS = 2


def connect():
    if control.connected:
        return True
    print("Connecting")
    connected = control.connect()
    if not connected:
        print("Unable to connect")
    else:
        print("Connected")
    return connected


def runSetValuesVsOutputValuesTest(targetCurrent, targetVoltage):
    """Sets the values of the device to target values and then records the device output values.
    Finally compares these values and throws an exception if they do not match according to expectations"""
    print("Checking voltage: ", targetVoltage, " and current: ", targetCurrent)
    control.setTargetCurrent(targetCurrent)
    control.setTargetVoltage(targetVoltage)
    time.sleep(SLEEP_BETWEEN_STEPS)
    measuredTargetCurrent = control.getTargetCurrent()
    measuredTargetVoltage = control.getTargetVoltage()
    outputVoltage = control.getOutputVoltage()
    outputCurrent = control.getOutputCurrent()
    allValues = control.getAllValues()

    if targetCurrent != measuredTargetCurrent:
        raise Exception("Wrong target current measured. Target current is ", targetCurrent,
                        " but measured target current is ", measuredTargetCurrent)
    if targetVoltage != measuredTargetVoltage:
        raise Exception("Wrong target voltage measured. Target voltage is ", targetVoltage,
                        " but measured target voltage is ", measuredTargetVoltage)
    compareTargetAndOutputValues(targetVoltage, outputVoltage, targetCurrent, outputCurrent, allValues)
    print("OK")


def compareTargetAndOutputValues(targetVoltage, outputVoltage, targetCurrent, outputCurrent, allValues):
    if not currentWithinBounds(targetCurrent, outputCurrent):
        raiseException(targetCurrent, outputCurrent, "Current")
    if not voltageWithinBounds(targetVoltage, outputVoltage):
        raiseException(targetVoltage, outputVoltage, "Voltage")
    if not currentWithinBounds(targetCurrent, allValues.outputCurrent):
        raiseException(targetCurrent, allValues.outputCurrent, "All values current")
    if not voltageWithinBounds(targetVoltage, allValues.outputVoltage):
        raiseException(targetVoltage, outputVoltage, "All values voltage")


def voltageWithinBounds(target, measured):
    return abs(target - measured) <= max(MAX_VOLTAGE_ABSOLUTE_DEVIATION, MAX_VOLTAGE_PERCENTAGE_DEVIATION * target)


def currentWithinBounds(target, measured):
    return abs(target - measured) <= max(MAX_CURRENT_ABSOLUTE_DEVIATION, MAX_CURRENT_PERCENTAGE_DEVIATION * target)


def raiseException(target, measured, valueName):
    raise Exception(valueName, " not correct. Target: ", target, " but measure: ", measured)


def runVoltageIntegrationTest():
    if not control.connected:
        raise Exception("Not connected")
    inputVoltage = control.getInputVoltage()
    if inputVoltage < 4:
        raise Exception("Input voltage not high enough to test. Input voltage value: ", inputVoltage)

    endVoltageTestRange = inputVoltage - 4
    voltageValues = [x / 10 for x in range(int(endVoltageTestRange * 10))]
    for v in voltageValues:
        runSetValuesVsOutputValuesTest(TARGET_CURRENT, v)
    print("Test script ran successfully")


def runCurrentIntegrationTest():
    if not control.connected:
        raise Exception("Could not connect to device")

    for c in range(10, 1000, 10):
        runSetValuesVsOutputValuesTest(c, 1)
    print("Test script ran successfully")


def setup():
    connected = connect()
    if connected:
        control.stopAutoUpdate()
        control.setOutputOnOff(True)


def cleanup():
    control.setTargetCurrent(0)
    control.setTargetVoltage(0)
    control.setOutputOnOff(False)


if __name__ == "__main__":
    setup()
    runVoltageIntegrationTest()
    runCurrentIntegrationTest()
    cleanup()