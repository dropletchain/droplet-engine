#© 2017-2020, ETH Zurich, D-INFK, lubu@inf.ethz.ch

MAGIC_BYTES = 'ab'

# Opcodes
ADD = '+'
CHANGE = ':'
DELETE = '-'

OPCODES = [
    ADD,
    CHANGE,
    DELETE
]

OPCODE_NAMES = {
    ADD: "ADD",
    CHANGE: "CHANGE",
    DELETE: "DELETE",
}

OPCODE_FIELDS = {
    ADD: ['uid', 'data'],
    CHANGE: ['uid', 'data'],
    DELETE: ['uid'],
}

NAME_OPCODES = {
    "ADD": ADD,
    "CHANGE": CHANGE,
    "DELETE": DELETE,
}

# op-return formats
LENGTHS = {
    'magic_bytes': 2,
    'opcode': 1,
    'name_min': 1,
    'name_max': 34,
    'max_op_length': 80
}
