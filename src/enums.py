from enum import Enum


class TypeMode(Enum):
    REGULATION = 1
    MEASURING = 0

class Input(Enum):
    ANALOG = 0
    DIGITAL = 1

class Plug(Enum):
    OPENED = 1
    CLOSED = 2
    REGULATION = 0
    OPENED_ = 3

class Recovery(Enum):
    ANALOG = 1
    MIXED = 0

class MeasuringMode(Enum):
    RRG = 0
    RDG = 1

class ZeroSetup(Enum):
    ON = 1
    OFF = 0

class State(Enum):
    NORMAL = 0
    LOW_GAS = 1

class PlugState(Enum):
    REGULATION = 0
    OPEN_OR_CLOSED = 1

class MeasuringModeChosen(Enum):
    RRG = 0
    RDG = 1

class RRGAvaliable(Enum):
    YES = 1
    NO = 0

class RDGAvaliable(Enum):
    YES = 1
    NO = 0

class OuterPlugState(Enum):
    OPENED = 1
    CLOSED = 2
    REGULATION = 0
    UNKNOWN = 3

first_byte_masks = {
    (1, 0): TypeMode,
    (2, 1): Input,
    (4+8, 2): Plug,
    (16, 4): Recovery,
    (32, 5): MeasuringMode,
    (64, 6): ZeroSetup
}
second_byte_masks = {
    (1, 0): State,
    (2, 1): PlugState,
    (4, 2): MeasuringModeChosen,
    (8, 3): RDGAvaliable,
    (16, 4): RRGAvaliable,
    (32+64, 5): OuterPlugState
}

def process_state_masks(first_byte, second_byte):
    answer = []
    for (mask, shift), mask_enum in first_byte_masks.items():
        answer.append(mask_enum((first_byte & mask) >> shift))

    for (mask, shift), mask_enum in second_byte_masks.items():
        answer.append(mask_enum((second_byte & mask) >> shift))

    return answer

def process_first_byte(first_byte):
    answer = []
    for (mask, shift), mask_enum in first_byte_masks.items():
        answer.append(mask_enum((first_byte & mask) >> shift))
    return answer

def process_second_byte(second_byte):
    answer = []
    for (mask, shift), mask_enum in second_byte_masks.items():
        answer.append(mask_enum((second_byte & mask) >> shift))
    return answer

def from_enum_to_int(changed_answer):
    new_int = 0
    for (mask, shift), mask_enum in zip(first_byte_masks.keys(), changed_answer):
        new_int += (mask_enum.value << shift)
    return new_int

