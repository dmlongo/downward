import os
import pddl
import pddl_to_prolog
import subprocess
import sys

def subset(l1, l2):
    for e in l1:
        if e not in l2:
            return False
    return True

class Hypertree:
    def __init__(self) -> None:
        self.bag = []
        self.cover = []
        self.parent = None
        self.children = []

    def set_bag(self, vertices):
        self.bag = vertices

    def set_cover(self, edges):
        self.cover = edges

    def add_child(self, child):
        self.children.append(child)
        child.parent = self

    def del_child(self, child):
        self.children.remove(child)
        child.bag = None
        child.cover = None
        child.parent = None
        child.children = None

    def _upwards(self):
        if self.parent is not None:
            p = self.parent
            if subset(self.bag, p.bag):
                p.cover.extend(self.cover)
                p.cover = list(dict.fromkeys(p.cover))
                for c in self.children:
                    p.add_child(c)

                p.del_child(self)
                return True
        return False

    def _downwards(self):
        heir = None
        for c in self.children:
            if subset(self.bag, c.bag):
                heir = c
                break
        if heir is not None:
            heir.cover.extend(self.cover)
            heir.cover = list(dict.fromkeys(heir.cover))
            self.children.remove(heir)
            for s in self.children:
                heir.add_child(s)
            if self.parent is not None:
                self.parent.add_child(heir)
                self.parent.del_child(self)
            else:
                heir.parent = None
                self.children = None
            return True
        return False

def delete_previous_htd_files():
    print("Deleting previous '.htd' files.")
    delete_files(".htd")


def delete_files(extension):
    cwd = os.getcwd()
    files = os.listdir(cwd)
    for f in files:
        if f.endswith(extension):
            os.remove(os.path.join(cwd, f))

def get_hypertree_decompositions(action):
    #f_name, map_pred_edge = generate_action_hypertree(action)
    #hd = compute_decompositions(f_name)
    #action.decomposition = parse_decompositions(hd, map_pred_edge)
    #action.join_tree = get_join_tree(hd)
    delete_files(".ast")
    delete_files(".htd")

def is_ground(rule):
    if len(rule.effect.args) > 0:
        return False
    for c in rule.conditions:
        if len(c.args) > 0:
            return False
    return True

def generate_hypertree(rule):
    map_predicate_to_edge = dict()
    counter = 0
    f = open("rule-hypertree.ast", 'w')
    for idx, p in enumerate(rule.conditions):
        if len(p.args) == 0:
            continue
        atom_name = "{}-{}".format(p.predicate, str(counter))
        map_predicate_to_edge[atom_name] = (idx, p)
        counter = counter + 1
        terms = ','.join([x for x in p.args if x[0] == '?']).replace('?', 'Var_')
        f.write('%s(%s)\n' % (atom_name, terms))
        p.hyperedge = atom_name
    f.close()
    return f.name, map_predicate_to_edge

def compute_decompositions(file):
    decomp_file_name = file
    decomp_file_name = decomp_file_name.replace('.ast', '.htd')
    f = open(decomp_file_name, 'w')
    BALANCED_GO_CMD = ['BalancedGo',
                       '-bench',
                       '-approx', '10',
                       '-det',
                       '-graph', file,
                       '-complete',
                       '-cpu', '1',
                       '-gml', decomp_file_name]

    res = subprocess.run(BALANCED_GO_CMD, stdout=subprocess.PIPE,
                         check=True, universal_newlines=True)
    hd = []
    parents = []
    for line in res.stdout.splitlines():
        if 'Bag: {' in line:
            node = Hypertree()
            line = line.strip()[6:-1]
            node.set_bag([v.strip() for v in line.split(',')])
            hd.append(node)

            if len(parents):
                par = parents[-1]
                par.add_child(node)
        elif 'Cover: {' in line:
            line = line.strip()[8:-1]
            hd[-1].set_cover([v.strip() for v in line.split(',')])
            #hd[-1].covered = covered(hd[-1]) # Davide told to comment out this list
        elif 'Children:' in line:
            parents.append(hd[-1])
        elif ']' in line:
            parents = parents[:-1]
    return hd


def split_into_hypertree(rule, name_generator):
    print("Using Hypertree decompositions. 'BalancedGo' is expected to be in the PATH.")
    delete_previous_htd_files()
    if len(rule.conditions) == 1 or is_ground(rule):
        return [rule]
    file_name, map_predicate_to_edge = generate_hypertree(rule)
    htd = compute_decompositions(file_name)

    new_rules = []
    leaves = set()
    associated_new_relation = dict()
    # First we create a new rules for cases with multiple bags
    # We simultaneously also collect the leaves of the tree
    for node in htd:
        if len(node.cover) > 1:
            conditions = []
            for c in node.cover:
                pos, _ = map_predicate_to_edge[c]
                condition = rule.conditions[pos]
                conditions.append(condition)
            effect_variables = pddl_to_prolog.get_variables(conditions)
            effect = pddl.Atom(next(name_generator), effect_variables)
            associated_new_relation[node] = effect
            new_rule = pddl_to_prolog.Rule(conditions, effect)
            new_rules.append(new_rule)
        else:
            pos, _ = map_predicate_to_edge[node.cover[0]] # single element in the cover
            effect = rule.conditions[pos]
            associated_new_relation[node] = effect
        if len(node.children) == 0:
            leaves.add(node)

    # Now we go bottom-up creating the new rules
    current_layer = set()
    for l in leaves:
        current_layer.add(l.parent)

    while not len(current_layer) == 0:
        next_layer = set()
        for node in current_layer:
            for child in node.children:
                effect_parent = associated_new_relation[node]
                effect_child = associated_new_relation[child]
                conditions = [effect_parent, effect_child]
                effect_variables = pddl_to_prolog.get_variables(conditions)
                new_effect = pddl.Atom(next(name_generator), effect_variables)
                associated_new_relation[node] = new_effect
                new_rule = pddl_to_prolog.Rule(conditions, new_effect)
                new_rules.append(new_rule)
            if node.parent is not None:
                next_layer.add(node.parent)
        current_layer = next_layer

    # HACK! change effect of last new_rule head to be the effect of the original rule
    if len(new_rules) > 0:
        new_rules[-1].effect = rule.effect

    return new_rules