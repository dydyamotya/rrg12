from pymodbus.client.sync import ModbusSerialClient
import struct
import serial
from pymodbus.exceptions import ModbusIOException

from .enums import *


class RRG12_modbus:
    AD_NET_ADDRESS = 0x0000
    AD_RRG_NUMBER = 0x0001
    AD_FLAGS1_REGISTER = 0x0002
    AD_FLAGS2_REGISTER = 0x0003
    AD_GASFLOWSET = 0x0004
    AD_GASFLOWREAD = 0x0005
    AD_COMPORT_SPEED = 0x0006
    convert_struct_from_word = struct.Struct(">H")
    convert_struct_to_int = struct.Struct(">h")

    def __init__(self, address: int, max_flow: float, port: str = None, client: ModbusSerialClient = None, baudrate: int = 19200):
        self.address = address
        self.number = None
        self.max_flow = max_flow
        if client is None:
            self.ser = ModbusSerialClient(method='rtu',
                                          port=port,
                                          baudrate=baudrate,
                                          bytesize=serial.EIGHTBITS,
                                          parity=serial.PARITY_NONE,
                                          stopbits=serial.STOPBITS_ONE)
        else:
            self.ser = client

    @classmethod
    def convert_from_word_to_int(cls, value: int):
        return cls.convert_struct_to_int.unpack(cls.convert_struct_from_word.pack(value))[0]

    def read_flow(self) -> float:
        try:
            flow_bytes = self.ser.read_holding_registers(
                RRG12_modbus.AD_GASFLOWREAD, unit=self.address).registers[0]
        except AttributeError:
            return 0
        else:
            flow_int = RRG12_modbus.convert_from_word_to_int(flow_bytes)
            return flow_int / 10000 * self.max_flow

    def get_state(self):
        answer = self.ser.read_holding_registers(self.AD_FLAGS1_REGISTER, 2, unit=self.address).registers
        answer_list = process_state_masks(*answer)
        return answer_list

    def get_changable_state(self):
        answer = self.ser.read_holding_registers(self.AD_FLAGS1_REGISTER, 1, unit=self.address).registers
        answer_list = process_first_byte(answer[0])
        return answer_list

    def write_flow(self, flow: float):
        if flow == 0:
            self.close_rrg_valve()
        else:
            self.regulate_rrg_valve()
            flow_percent = int(flow / self.max_flow * 10000)
            self.ser.write_register(
                RRG12_modbus.AD_GASFLOWSET, flow_percent, unit=self.address)

    def close_rrg_valve(self):
        state = self.get_changable_state()
        if state[2] != Plug.CLOSED:
            state[2] = Plug.CLOSED
            self.ser.write_register(RRG12_MODBUS.AD_FLAGS1_REGISTER, from_enum_to_int(state), unit=self.address)

    def regulate_rrg_valve(self):
        state = self.get_changable_state()
        if state[2] != Plug.REGULATION:
            state[2] = Plug.REGULATION
            self.ser.write_register(RRG12_MODBUS.AD_FLAGS1_REGISTER, _from_enum_to_int(state), unit=self.address)

    def close(self):
        self.ser.close()
