#!/usr/bin/env python

import sys
import os
import random

from functools import reduce
from operator import mul

children = None # set of children
adjacencies = None # adjacency matrix representation 
neighbors = None # adjacency list representation
n = None # size
SCCs = None # list of lists of vertices, representing the SCC decomposition
which_SCC = None # mapping of nodes to the SCCs contianing them
SCC_adjacencies = None # adjacency matrices WITHIN each SCC
SCC_neighbors = None # adjacency lists WITHIN each SCC
SCC_n = None # sizes of each SCC

removed = set()

CYCLES = [] # cycles to return!


def total_value(vertices):
    return 2 * len(vertices & children) + len(vertices - children)


def is_complete():
    """Return whether the graph represented by the adjacency list in
    adjacencies is complete."""
    return all([all(lst) for lst in adjacencies])


def dfs_post_ordering(adjacencies):
    """Return a list of the DFS post-number ordering of the graph
    represented by ADJACENCIES."""
    def neighbors(v):
        neighbors = set()
        for u in range(n):
            if adjacencies[v][u]:
                neighbors.add(u)
        return neighbors

    ordering = []

    visited = set()

    def explore(v):
        visited.add(v)
        for u in neighbors(v):
            if u not in visited:
                explore(u)
        ordering.append(v) # count up post number

    while len(visited) < n:
        explore(min([i for i in range(n) if i not in visited]))

    return ordering


def get_SCCs():
    """Return a list of lists, representing the SCC decomposition of the graph."""
    SCCs = []

    reversed_adjacencies = [[False for j in range(n)] for i in range(n)]
    for i in range(n):
        for j in range(n):
            reversed_adjacencies[i][j] = adjacencies[j][i]

    reversed_post_ordering = dfs_post_ordering(reversed_adjacencies) # all vertices, in the order we'll use for the DFS (sink-first)
    processed = list(removed) # which vertices have been put in components yet?

    current_component = [] # an SCC we're currently constructing

    visited = set()

    def explore(v):
        visited.add(v)
        current_component.append(v)
        processed.append(v)

        for u in neighbors[v]:
            if u not in visited:
                explore(u)

    while len(processed) < n:
        explore([x for x in reversed_post_ordering if x not in processed][-1]) # explore vertex that comes last in ordering, which hasn't been processed yet
        SCCs.append(sorted(current_component)) # this component is finished
        current_component = [] # start new component

    return SCCs


def get_which_SCC():
    """Return a mapping of nodes to the SCCs containing them."""
    which_SCC = [0 for _ in range(n)]
    for i in range(n):
        for s in range(len(SCCs)):
            if i in SCCs[s]:
                which_SCC[i] = s
    return which_SCC


def remove(i):
    """Remove all connections, etc. from vertex I."""
    global children

    # update children
    children -= {i}

    # update adjacencies
    adjacencies[i] = [False for _ in range(n)]

    for j in range(len(adjacencies)):
        adjacencies[j][i] = False # remove all adjacencies TO vertex i
    
    # update neighbors

    neighbors[i] = set() # remove set of vertex i's neighbors

    for j in range(n):
        if i in neighbors[j]: # i is no longer anyone's neighbor
            neighbors[j].remove(i) 

    # update SCC stuff
    w = which_SCC[i]
    SCCs[w].remove(i)


def remove_all(s):
    """Completely remove all vertices in the set S."""
    global children

    for i in s:
        children -= {i}
        adjacencies[i] = [False for _ in range(n)]
        for j in range(len(adjacencies)):
            adjacencies[j][i] = False # remove all adjacencies TO vertex i

        # update neighbors
        neighbors[i] = set() # remove set of vertex i's neighbors
        for j in range(n):
            if i in neighbors[j]: # i is no longer anyone's neighbor
                neighbors[j].remove(i)

        # update SCC stuff
        w = which_SCC[i]
        SCCs[w].remove(i)

        removed.add(i)


def in_a_cycle(i):
    """Returns whether or not vertex I is in a cycle of size <= 5.
    (Does not consider SCCs.)"""
    visited = set()
    in_cycle = False

    def explore(v, d):
        nonlocal in_cycle
        if d >= 5:
            return 
        if i in neighbors[v]:
            in_cycle = True

        visited.add(v)

        for n in neighbors[v]:
            if n not in visited:
                explore(n, d + 1)

    explore(i, 0)
    return in_cycle


def in_a_cycle_SCC(i):
    """Returns whether or not vertex I is in a cycle of size <= 5, within its SCC."""
    visited = set()
    in_cycle = False

    s = which_SCC[i]
    
    def explore(v, d):
        nonlocal in_cycle
        if d >= 5: 
            return 
        if i in SCC_neighbors[s][v]:
            in_cycle = True

        visited.add(v)

        for n in SCC_neighbors[s][v]:
            if n not in visited:
                explore(n, d + 1)

    explore(i, 0)
    return in_cycle


def gonna_die():
    """Returns all people (vertices) who are definitely going to die."""
    dooomed = set()
    for i in range(n):
        if not in_a_cycle(i):
            dooomed.add(i)
    return dooomed


def gonna_die_SCC():
    """Returns all people (vertices) who are definitely going to die."""
    dooomed = set()
    for i in range(n):
        if not in_a_cycle_SCC(i):
            dooomed.add(i)
    return dooomed


def remove_not_in_a_cycle():
    """Remove from adjacencies and neighbors all vertices not in a cycle.
    (Does not take SCCs into account.)"""
    remove_all(gonna_die())
    generate_SCC_stuff()


def remove_not_in_a_cycle_SCC():
    """Remove from adjacencies and neighbors all vertices not in a cycle."""
    remove_all(gonna_die_SCC())
    generate_SCC_stuff()


def get_neighbors(i):
    """Find adjacency list of vertex I from adjacency matrix (adjacencies)."""
    all_neighbors = set()
    for j in range(n):
        if adjacencies[i][j]:
            all_neighbors.add(j)
    return all_neighbors


def all_cycles(i):
    """Find all cycles of length at most 5 starting from vertex I."""
    cycles = []

    visited = set()

    def explore(v, cycle):
        visited.add(v)

        if i in neighbors[v]:
            cycles.append(cycle)

        if len(cycle) >= 5:
            return

        for u in neighbors[v]:
            if u not in cycle:
                explore(u, cycle | {u})
    explore(i, {i})

    return cycles


def all_cycles_in_SCC(i):
    """Find all cycles of length at most 5 starting from vertex I, in its SCC."""
    cycles = []

    visited = set()

    s = which_SCC[i]

    def explore(v, cycle):
        visited.add(v)

        if i in SCC_neighbors[s][v]:
            cycles.append(cycle)

        if len(cycle) >= 5:
            return

        for u in SCC_neighbors[s][v]:
            if u not in cycle:
                explore(u, cycle | {u})
    explore(i, {i})

    return cycles


def value(cycle):
    """Returns the value of a cycle (children are worth 2, adults 1
       because that's the cost if they aren't included in any cycle)"""

    val = 0
    for x in cycle:
        if x in children:
            val += 2
        else:
            val += 1
    return val


def most_valuable_cycle(i):
    """Does what it says."""

    return max(all_cycles(i), key = value)


def most_valuable_cycle_in_SCC(i):
    """Does what it says."""

    return max(all_cycles_in_SCC(i), key = value)


def generate_SCC_stuff():
    global SCCs, which_SCC, SCC_adjacencies, SCC_neighbors, SCC_n

    SCCs = get_SCCs()

    which_SCC = get_which_SCC()

    # construct copies of adjacencies, neighbors, and n for each SCC
    SCC_adjacencies = [] # adjacency matrices WITHIN each SCC
    SCC_neighbors = [] # adjacency lists WITHIN each SCC
    SCC_n = [] # sizes of each SCC

    for SCC in SCCs:
        this_n = len(SCC)

        this_adjacencies = [[False for _ in range(n)] for _ in range(n)]
        for i in SCC:
            for j in SCC:
                this_adjacencies[i][j] = adjacencies[i][j]

        this_neighbors = [set() for _ in range(n)]
        for i in SCC:
            this_neighbors[i] = {x for x in neighbors[i] if x in SCC}

        SCC_adjacencies.append(this_adjacencies)
        SCC_neighbors.append(this_neighbors)
        SCC_n.append(this_n)


def take_small_SCCs():
    """Add all SCCs of size <= 5 to CYCLES, and remove them."""

    to_remove = set()

    for SCC in SCCs:
        if 2 <= len(SCC) <= 5:
            CYCLES.append(SCC[:]) # add a copy of SCC to CYCLES
            to_remove |= set(SCC)
        elif len(SCC) == 1:
            to_remove |= set(SCC)
    remove_all(to_remove)

    for i in range(len(SCCs) - 1, -1, -1):
        if len(SCCs[i]) == 0:
            del SCCs[i]

    generate_SCC_stuff()


def random_lowest_outorder(vertices, s):
    return min(sorted(vertices, key = lambda x: random.random()), key = lambda vertex: len(SCC_neighbors[s][vertex]))


def random_cycle(i, vertices):
    visited = set()

    def explore(v, cycle):
        visited.add(v)

        if i in neighbors[v] & vertices:
            return cycle

        if len(cycle) >= 5:
            return

        for u in sorted(neighbors[v] & vertices, key = lambda x: random.random()):
            if u not in cycle:
                new_cycle = explore(u, cycle | {u})
                if new_cycle:
                    return new_cycle
                    
    return explore(i, {i})



def process(s):
    """Do stuff to this SCC."""
    vertices = SCCs[s]

    values = {}
    for _ in range(len(vertices) ** 2): # |SCC|^2 because why not
        cycles = []
        processed = set()
        left = set(vertices)

        while True:
            cycle = None
            count = 0
            while not cycle and count < 100:
                c = random_lowest_outorder(list(left) + list(left & children), s) # weight children * 2
                cycle = random_cycle(c, left)
                count += 1
            if not cycle:
                break

            cycles.append(tuple(cycle))

            processed |= cycle
            left -= cycle

        value = total_value(left)
        values[tuple(cycles)] = value

    return min(values, key = lambda v: values[v])


def process_and_remove_all():
    while len(SCCs):
        result = process(0)
        CYCLES.extend([list(cycle) for cycle in result])
        remove_all(SCCs[0])
        del SCCs[0]

        generate_SCC_stuff()
        take_small_SCCs()


def brute_force(s):
    """(Badly) brute-force this (hopefully small) SCC."""

    S = SCCs[s]
    while len(S):
        if in_a_cycle_SCC(min(S)):
            cycle = most_valuable_cycle_in_SCC(min(S))
            CYCLES.append(cycle[:])
            remove_all(cycle)
        else:
            remove(min(S))
    del SCCs[s]



if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("usage: python3 -i code.py [input file]")
        os._exit(1)

    filename = sys.argv[1]

    input_file = None
    try:
        input_file = open(filename, "r")
    except IOError:
        print("Input file '%s' not found." % (filename))
        os._exit(1)

    n = int(input_file.readline())

    # construct set of children
    children = set(int(c) for c in input_file.readline().split())

    # construct list of whether is child
    is_child = []
    for i in range(n):
        is_child.append(i in children)

    # construct adjacency list and adjacency matrix
    adjacencies = []
    neighbors = []
    for i in range(n):
        adjacencies.append([bool(int(x)) for x in input_file.readline().split()])
        neighbors.append(get_neighbors(i))

    # determine SCC decomposition
    generate_SCC_stuff()

    remove_not_in_a_cycle_SCC()

    generate_SCC_stuff()

    take_small_SCCs()

    proces_and_remove_all()

    
