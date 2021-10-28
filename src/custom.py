import serial
import struct
import numbers

from enums import *


class CheckSumException(Exception):
    pass


class RRG12:
    ADDR_DEF_COMMAND = 2
    STATE_COMMAND = 1
    GAS_GET_FLOW = 17
    GAS_SET_FLOW = 37
    REDEFINE_COMMAND = 27
    VALVE_COMMAND = 32
    REGIME_COMMAND = 24
    BAUDRATE_SET = 22

    def __init__(self, port: str = None,
            max_flow: numbers.Number = None,
            ser: serial.Serial = None,
            address: int = None,
            baudrate: int = 19200):
        self.address = address
        self.number = None
        if ser is None:
            self.ser = serial.Serial(port=port, baudrate=baudrate,
                                     stopbits=serial.STOPBITS_ONE, bytesize=serial.EIGHTBITS,
                                     parity=serial.PARITY_NONE)
        else:
            self.ser = ser
        self.max_flow = max_flow
        self.state = None

    @staticmethod
    def calculate_checksum(message):
        return sum(message).to_bytes(2, "big")

    @staticmethod
    def check_checksum(message: bytes):
        if int.from_bytes(message[8:10], "big") == sum(message[:8]):
            return True
        else:
            return False

    def close(self):
        self.ser.close()

    def is_opened(self):
        return self.ser.is_open()

    def open(self):
        self.ser.open()

    def write_read_answer(self, message: bytes):
        self.ser.write(message + self.calculate_checksum(message))
        answer = self.ser.read(10)
        if not self.check_checksum(answer):
            raise CheckSumException("Wrong checksum")
        return answer

    def get_state(self):  # 0x01
        message = bytes((self.STATE_COMMAND, ) + (0, )*6 + (self.address,))
        answer = self.write_read_answer(message)
        if self.number:
            if int.from_bytes(answer[2:4], "big") != self.number:
                raise Exception("Wrong device number")

        self.state = process_state_masks(answer[1], answer[6])
        return [(state, state.name) for state in self.state]

    def define_address(self):  # 0x02
        if self.address is None:
            message = bytes((self.ADDR_DEF_COMMAND, )) + bytes(7)
            answer = self.write_read_answer(message)
            self.number = int.from_bytes(answer[5:7], "big")
            self.address = answer[7]
            return self.address
        else:
            return self.address

    def refresh_address(self):
        self.address = None
        self.define_address()

    def set_regime(self, typemode: TypeMode, measuringmode: MeasuringMode): # 24
        message = bytearray(8)
        message[0] = self.REGIME_COMMAND
        message[1] = typemode.value
        message[3] = measuringmode.value
        message[7] = self.address
        answer = self.write_read_answer(message)

    def check_connection(self):
        message = bytearray(8)
        message[0] = 25
        message[7] = self.address
        answer = self.write_read_answer(message)
        address = answer[7]
        number = int.from_bytes(answer[5:7], "big")
        return address, number

    def read_flow(self): # 17
        message = bytes((self.GAS_GET_FLOW, )) + \
            bytes(6) + self.address.to_bytes(1, "big")
        answer = self.write_read_answer(message)
        sign = -1 if (answer[2] & 2**8) else 1
        flow = int.from_bytes(answer[2:4], "big") & (2**16)-1 * sign
        setup = int.from_bytes(answer[4:6], "big")
        return flow / 10000 * self.max_flow, setup / 10000 * self.max_flow

    def set_baudrate(self, baudrate): # 22
        """baudrate from list: [9600, 19200, 38400]"""
        baudrates = {9600: 0, 19200: 0xFF, 38400: 1}
        message = bytearray(8)
        message[0] = self.BAUDRATE_SET
        try:
            message[2] = baudrates[baudrate]
        except KeyError:
            raise Exception("Wrong baudrate")
        else:
            message[7] = self.address
            answer = self.write_read_answer(message)


    def write_flow(self, flow): # 37
        if self.max_flow:
            message = bytearray(8)
            message[0] = self.GAS_SET_FLOW
            message[1] = 0
            flow_int =int(flow/self.max_flow * 10000) 
            message[2:4] = flow_int.to_bytes(2, "big")
            message[7] = self.address
            answer = self.write_read_answer(message)

    def redefine_address(self, new_address: int): # 27
        message = bytearray(8)
        message[0] = self.REDEFINE_COMMAND
        message[2] = new_address
        message[7] = self.address
        answer = self.write_read_answer(message)

    def set_recovery_mode(self, mode: Recovery):
        message= bytearray(8)
        message[0] = 31
        message[1] = mode.value
        message[7] = self.address
        answer = self.write_read_answer(message)

    def set_plug_mode(self, plug_mode: Plug):
        message = bytearray(8)
        message[0] = 32
        message[2] = plug_mode.value
        message[7] = self.address
        answer = self.write_read_answer(message)

    def set_zero(self, shift):
        message = bytearray(8)
        message[0] = 35
        message[7] = self.address
        message[3] = 1
        message[4:6] = shift.to_bytes(2, "big")
        answer = self.write_read_answer(message)

    def get_zero(self):
        message = bytearray(8)
        message[0] = 35
        message[7] = self.address
        answer = self.write_read_answer(message)
        shift = int.from_bytes(answer[4:6], "big")
        return shift
        
