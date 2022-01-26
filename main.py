from builder import *
from automata import *

a_table = {
    'a': [[1], [3], [3], []],
    'b': [[2], [], [], []],
}

b_table = {
    'a': [[1], [], []],
    'c': [[], [2], []]
}

c = plus(
    NonDeterministicAutomata(b_table, [2])
)

d = {
    EPSILON: [[1], [2], [3], [5], [5], [6], [7]]
}

convert_to_fda(construct_fnda('(A;B),C,(A;B)')).print_table()