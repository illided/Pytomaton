from automata import NonDeterministicAutomata, DeterministicAutomata, NFDA_table, FDA_table, EPSILON
from typing import Dict, List


def merge_tables(A: NonDeterministicAutomata, B: NonDeterministicAutomata) -> NonDeterministicAutomata:
    keys = set(list(A.table.keys()) + list(B.table.keys()))
    new_final = [state + A.num_of_states() for state in B.final_states]
    new_final.extend(A.final_states)
    new_table = {}
    for k in keys:
        new_row = []
        if k in A.table:
            new_row.extend(A.table[k])
        else:
            new_row.extend([[] for _ in range(A.num_of_states())])
        if k in B.table:
            new_row.extend([[s + A.num_of_states() for s in states] for states in B.table[k]])
        else:
            new_row.extend([[] for _ in range(B.num_of_states())])
        new_table[k] = new_row
    return NonDeterministicAutomata(table=new_table, final_states=new_final)


def concatenate(A: NonDeterministicAutomata, B: NonDeterministicAutomata) -> NonDeterministicAutomata:
    merged = merge_tables(A, B)
    for start in A.final_states:
        merged.add_transition(start, EPSILON, A.num_of_states())
    merged.final_states = [s + A.num_of_states() for s in B.final_states]
    return merged


def alternate(A: NonDeterministicAutomata, B: NonDeterministicAutomata) -> NonDeterministicAutomata:
    merged = merge_tables(A, B)
    shifted_finals = [f + 1 for f in merged.final_states]
    shifted_table = {}
    for char, state_list in merged.table.items():
        shifted_table[char] = [[]] + [[state + 1 for state in states] for states in state_list] + [[]]
    new = NonDeterministicAutomata(table=shifted_table, final_states=shifted_finals)
    new.add_transition(0, EPSILON, 1)
    new.add_transition(0, EPSILON, A.num_of_states() + 1)
    for f in shifted_finals:
        new.add_transition(f, EPSILON, new.num_of_states() - 1)
    new.final_states = [new.num_of_states() - 1]
    return new


def star(A: NonDeterministicAutomata) -> NonDeterministicAutomata:
    shifted_finals = [f + 1 for f in A.final_states]
    shifted_table = {}
    for char, state_list in A.table.items():
        shifted_table[char] = [[]] + [[state + 1 for state in states] for states in state_list] + [[]]
    new = NonDeterministicAutomata(table=shifted_table, final_states=shifted_finals)
    for f in shifted_finals:
        new.add_transition(f, EPSILON, 1)
        new.add_transition(f, EPSILON, new.num_of_states() - 1)
    new.add_transition(0, EPSILON, 1)
    new.add_transition(0, EPSILON, new.num_of_states() - 1)
    new.final_states = [new.num_of_states() - 1]
    return new


def plus(A: NonDeterministicAutomata) -> NonDeterministicAutomata:
    return concatenate(A, star(A))


def generalized_iteration(A: NonDeterministicAutomata, B: NonDeterministicAutomata) -> NonDeterministicAutomata:
    return concatenate(A, star(concatenate(A, B)))


def primitive_fnda(actual_string: str) -> NonDeterministicAutomata:
    table: Dict[str, List[List[int]]] = {}
    for i, c in enumerate(actual_string):
        if c not in table:
            table[c] = [[] for _ in range(len(actual_string) + 1)]
        table[c][i].append(i + 1)
    return NonDeterministicAutomata(table=table, final_states=[len(actual_string)])


def construct_fnda(regexp: str) -> NonDeterministicAutomata:
    operations = {
        '*': star,
        '+': plus,
        ';': alternate,
        ',': concatenate,
        '#': generalized_iteration
    }
    priorities = {
        ';': 0,
        '#': 1,
        ',': 1,
        '*': 2,
        '+': 2
    }

    binary = [';', '#', ',']
    unary = ['*', '+']

    op_stack = []
    automata_stack = []
    buffer = ''

    def avalanche(priority=-1):
        while len(op_stack) != 0 \
                and op_stack[-1] != '(' \
                and (op_stack[-1] not in operations.keys() or priorities[op_stack[-1]] > priority):
            op = op_stack[-1]
            if op in binary:
                automata_stack.append(operations[op](automata_stack[-2], automata_stack[-1]))
                automata_stack.pop(-2)
                automata_stack.pop(-2)
                op_stack.pop()
            elif op in unary:
                automata_stack.append(operations[op](automata_stack[-1]))
                automata_stack.pop(-2)
                op_stack.pop()
        if priority == -1 and len(op_stack) != 0 and op_stack[-1] == '(':
            op_stack.pop()

    for c in regexp:
        if c in list(operations.keys()) + ['(', ')']:
            if buffer != '':
                automata_stack.append(primitive_fnda(buffer))
            buffer = ''
        if c in operations:
            if len(op_stack) == 0 or op_stack[-1] in ['(', ')'] or priorities[op_stack[-1]] < priorities[c]:
                op_stack.append(c)
            else:
                avalanche(priorities[c])
                op_stack.append(c)
        elif c == '(':
            op_stack.append('(')
        elif c == ')':
            avalanche()
        else:
            buffer += c

    if buffer != '':
        automata_stack.append(primitive_fnda(buffer))
    avalanche()
    return automata_stack[-1]


def convert_to_fda(fnda: NonDeterministicAutomata) -> DeterministicAutomata:
    links = []
    newStates = [set(fnda.eps_close(0))]
    visitedStates = []
    alphabet = [x for x in list(fnda.table.keys()) if x != EPSILON]
    while len(newStates) > 0:
        tmp = newStates.pop()
        if tmp in visitedStates:
            continue
        visitedStates.append(tmp)
        for char in alphabet:
            newTmp = set(fnda.forward(tmp, char))
            if len(newTmp) != 0:
                newStates.append(newTmp)
                links.append((tmp, char, newTmp))
    formatted_links = []
    for link in links:
        formatted_links.append((visitedStates.index(link[0]), link[1], visitedStates.index(link[2])))
    links = formatted_links
    old_final = set(fnda.final_states)
    new_final = [i for i, s in enumerate(visitedStates) if s.intersection(old_final)]
    new_table = {}
    for k in alphabet:
        new_table[k] = [None for _ in enumerate(visitedStates)]
    for link in links:
        new_table[link[1]][link[0]] = link[2]
    return DeterministicAutomata(table=new_table, final_states=new_final)

def minimize_fda(fda: DeterministicAutomata) -> DeterministicAutomata:
    ...
