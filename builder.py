from automata import NonDeterministicAutomata, DeterministicAutomata, EPSILON
from typing import Dict, List, Tuple


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
    new = NonDeterministicAutomata(table=shifted_table, final_states=[])
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
    new = NonDeterministicAutomata(table=shifted_table, final_states=[])
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


def is_character(c):
    return c not in (list(operations.keys()) + ['(', ')'])


def prepare_regexp(regexp: str) -> str:
    if len(regexp) == 0:
        return ''
    new = []
    last = None
    for c in regexp:
        if last is None:
            last = c
            new.append(c)
            continue
        if last in unary and c == '(' \
                or last in unary and is_character(c) \
                or is_character(last) and is_character(c) \
                or last == ')' and is_character(c) \
                or is_character(last) and c == '(':
            new.append(',')
        new.append(c)
        last = c
    return ''.join(new)


def construct_fnda(regexp: str) -> NonDeterministicAutomata:
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

    regexp = prepare_regexp(regexp)

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
    def split_set(target, splitter, split_char) -> Tuple[set, set]:
        R1 = set()
        R2 = set()
        for v in target:
            if fda.table[split_char][v] in splitter:
                R1.add(v)
            else:
                R2.add(v)
        return R1, R2

    sets = [{*fda.final_states}]
    non_final = {*list(range(fda.num_of_states()))}.difference(fda.final_states)
    if len(non_final) > 0:
        sets.append(non_final)
    queue = []
    for c in fda.alphabet():
        for s in sets:
            queue.append((s, c))
    while len(queue) > 0:
        splitter, char = queue.pop(0)
        for s in sets:
            R1, R2 = split_set(s, splitter, char)
            if len(R1) > 0 and len(R2) > 0:
                sets.remove(s)
                sets.extend([R1, R2])
                if (s, char) in queue:
                    queue.remove((s, char))
                    queue.append((R1, char))
                    queue.append((R2, char))
                else:
                    if len(R1) < len(R2):
                        queue.append((R1, char))
                    else:
                        queue.append((R2, char))

    first_state_index = [sets.index(s) for s in sets if 0 in s][0]
    first_state = sets.pop(first_state_index)
    sets.insert(0, first_state)

    num_of_states = len(sets)
    new_table = {k: [None] * num_of_states for k in fda.alphabet()}
    for i, s in enumerate(sets):
        for v in s:
            for c in fda.alphabet():
                new_indexes = [sets.index(s) for s in sets if fda.table[c][v] in s]
                new_table[c][i] = None if len(new_indexes) == 0 else new_indexes[0]
    new_final = [sets.index(s) for s in sets if s.intersection(fda.final_states)]
    return DeterministicAutomata(table=new_table, final_states=new_final)
