from typing import Dict, List, Set
import copy

FDA_table = Dict[str, List[int]]
NFDA_table = Dict[str, List[List[int]]]
EPSILON = 'EPSILON'


class CharCantBeAccepted(Exception):
    pass


class Automata:
    def accepts(self, input_string: str) -> bool:
        raise NotImplementedError()

    def num_of_states(self):
        raise NotImplementedError()

    def print_table(self):
        raise NotImplementedError()

    def alphabet(self):
        raise NotImplementedError()


class NonDeterministicAutomata(Automata):
    def __init__(self, table: NFDA_table, final_states: List[int]):
        self.table = table
        self.final_states = final_states

        self.states = None

    def next_state(self, state: int, char: str) -> List[int]:
        if char not in self.table:
            raise CharCantBeAccepted
        return self.table[char][state]

    def forward(self, old_state, char: str):
        new_state = set()
        for state in old_state:
            new_state.update(self.next_state(state, char))
            if EPSILON in self.table.keys():
                new_state.update(sum([self.eps_close(s) for s in new_state], []))
        return list(new_state)

    def add_transition(self, start, char, finish):
        if char not in self.table:
            self.table[char] = [[] for _ in range(self.num_of_states())]
        self.table[char][start].append(finish)

    def accepts(self, input_string: str) -> bool:
        self.states = self.eps_close(0)
        try:
            for c in input_string:
                self.states = self.forward(self.states, c)
            for state in self.states:
                if set(self.eps_close(state)).intersection(self.final_states):
                    return True
            return False
        except CharCantBeAccepted:
            return False

    def num_of_states(self):
        return len(list(self.table.values())[0])

    def copy(self):
        new_table = copy.deepcopy(self.table)
        new_final = copy.deepcopy(self.final_states)
        return NonDeterministicAutomata(new_table, new_final)

    def print_table(self):
        for char, state_list in self.table.items():
            states = '  |  '.join([f'{i} -> {s}' for i, s in enumerate(state_list) if len(s) != 0])
            print(char, '|', states)
        print(f'Final states: {self.final_states}')

    def eps_close(self, state: int) -> List[int]:
        if EPSILON not in self.table.keys():
            return [state]
        visited = []
        active = [state]
        while len(active) != 0:
            new_active = []
            for s in active:
                new_active.extend(self.table[EPSILON][s])
            visited = list(set(visited + active))
            active = list(set(new_active).difference(visited))
        return visited

    def alphabet(self):
        return list(self.table.keys())


class DeterministicAutomata(Automata):
    def __init__(self, table: FDA_table, final_states: List[int]):
        self.table = table
        self.final_states = final_states
        proxy_table = {}
        for char, states in table.items():
            proxy_table[char] = [[state] if state is not None else [] for state in states]
        self.proxy = NonDeterministicAutomata(proxy_table, final_states)

    def accepts(self, input_string: str) -> bool:
        return self.proxy.accepts(input_string)

    def print_table(self):
        self.proxy.print_table()

    def num_of_states(self):
        return self.proxy.num_of_states()

    def alphabet(self):
        return self.proxy.alphabet()
