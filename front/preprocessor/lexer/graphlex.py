import pydot
import re
import types
import networkx as nx
import copy
import sys


class Relation:
    def __init__(self, left={}, right={}, predicate=None, extra=None, label="",params={"edge_style": {"color": "black"}}):
        self.left = left
        self.right = right
        self.predicate = types.MethodType(predicate, Relation)
        self.extra = extra
        self.label = label
        self.params = copy.deepcopy(params)


#===================================================================================

# complete common lex patterns

if_cond = re.compile(
    r'\s*if\s+\(\s*(\*?[a-zA-Z_$][a-zA-Z_$0-9]*|.*D\.\d+)' # left side of header
    r'\s+(>=|<=|>|<|==|!=)' # operation
    r'\s+((\*?[a-zA-Z_$][a-zA-Z_$0-9]*|.*D\.\d+)|(\d+(\.\d+)?))\s*\).*\n' # right side of header
    r'.*goto\s+(\<(bb\s+[0-9]+)\>);.*\nelse.\n\s+goto\s(\<(bb\s+[0-9]+)\>);.*', # body
    re.VERBOSE
)


assign_const = re.compile(
    r'(\*?[a-zA-Z_$][a-zA-Z_$0-9]*|.*D\.\d+)\s+='
    r'\s+(\d+(\.\d+)?);.*',
    re.VERBOSE
)

assign_var = re.compile(
    r'(\*?[a-zA-Z_$][a-zA-Z_$0-9]*|.*D\.\d+)\s+='
    r'\s+(\*?[a-zA-Z_$][a-zA-Z_$0-9]*);.*',
    re.VERBOSE
)

assign_string_const = re.compile(
    r'(\*?[a-zA-Z_$][a-zA-Z_$0-9]*|.*D\.\d+)\s+='
    r'\s+"(.*)";.*',
    re.VERBOSE
)

assign_function_call = re.compile(
    r'((\*?[a-zA-Z_$][a-zA-Z_$0-9]*|.*D\.\d+)\s?=?'
    r'\s+)?([a-zA-Z_{1}][a-zA-Z0-9_]+)\s*\((.*?)\);.*',
    re.VERBOSE
)

assign_aryphmetic_op = re.compile(
    r'(\*?[a-zA-Z_$][a-zA-Z_$0-9]*|.*D\.\d+)\s+='
    r'\s+((\*?[a-zA-Z_$][a-zA-Z_$0-9]*)|(\d+(\.\d+)?))\s+'
    r'(\%|\/|\+|\-|\*)\s+'
    r'((\*?[a-zA-Z_$][a-zA-Z_$0-9]*|.*D\.\d+)|(\d+(\.\d+)?));',
    re.VERBOSE
)

assign_MEM = re.compile(
    r'(\*?[a-zA-Z_$][a-zA-Z_$0-9]*|.*D\.\d+)\s+=\s+MEM(\[\(\*?[a-zA-Z_$][a-zA-Z_$0-9]*\*\))?'
    r'\s+((\*?[a-zA-Z_$][a-zA-Z_$0-9]*)|(\d+(\.\d+)?))\s+'
    r'(\%|\/|\+|\-|\*)\s+'
    r'((\*?[a-zA-Z_$][a-zA-Z_$0-9]*|.*D\.\d+)|(\d+(\.\d+)?));',
    re.VERBOSE
)

goto = re.compile(
    r'.*goto\s+(\<(bb\s+[0-9]+)\>);.*',
    re.VERBOSE
)

#===================================================================================

lex = dict()



lex['if_cond'] = {
    'exp':if_cond,
    'format':{
        'left':"",
        'comp_op':"",
        'right':"",
        'if_true':"",
        'if_false':""
    }
}

lex['assign_const'] = {
    'exp':assign_const,
    'format':{
        'left':"",
        'right':"",
    }
}

lex['assign_var'] = {
    'exp':assign_var,
    'format': {
        'left': "",
        'right': "",
    }
}

lex['assign_string_const'] = {
    'exp':assign_string_const,
    'format': {
        'left': "",
        'right': "",
    }
}

lex['assign_function_call'] = {
    'exp':assign_function_call,
    'format': {
        'left': "",
        'func_name': "",
        'arguments': "",
    }
}


lex['assign_aryphmetic_op'] = {
    'exp':assign_aryphmetic_op,
    'format': {
        'left': "",
        'r_operand1': "",
        'op': "",
        'r_operand2': "",
    }
}

lex['goto'] = {
    'exp':goto,
    'format': {
        'dest': "",
    }
}

lex['assign_MEM'] = {
    'exp': assign_MEM,
    'format': {
        'left': "",
        'cast': "",
        'base': "",
        'op': "",
        'shift': ""
    }
}

nodes = {}
for k in lex.keys():
    nodes.update({k:[]})


def load_graph(graph_filename = '2.original.dot'):
    graphs = pydot.graph_from_dot_file(graph_filename)
    graph = graphs[0]

    return graph


def write_graph(graph, filename='src.png'):
    graph.write_png()


def edge_get_nodes_labels(G, e):
    src_label = G.get_node(e.get_source())[0].get_attributes()['label']
    dst_label = G.get_node(e.get_destination())[0].get_attributes()['label']
    return src_label, dst_label


def edge_get_nodes(G, e):
    src = G.get_node(e.get_source())[0]
    dst = G.get_node(e.get_destination())[0]
    return src, dst


def trim_prefix(fn):
    file1 = open(fn, 'r')
    file2 = open(fn + "_prefix_trimmed", 'w')
    skip = True
    for line in file1.readlines():
        if (line.startswith('digraph code')):
            skip = False
        if not skip:
            file2.write(line)

    # close and save the files
    file2.close()
    file1.close()
    return fn + "_prefix_trimmed"


def lex_graph(inp_file):
    print("Load graph from", inp_file)
    tr_file=trim_prefix(inp_file)
    graph = load_graph(tr_file)
    node_lex_dict = {}
    graph.write_png("g.png")

    def make_lex_node(n):
        if n.get_name() in node_lex_dict.keys():
            return node_lex_dict[n.get_name()]

        label = n.get_attributes()['label'].replace("\\", "")[2:]
        _lex = copy.deepcopy(lex)
        for l, r in _lex.items():

            res = re.search(r['exp'], label)
            if res:
                if l == "if_cond":
                    r['format'].update({
                        'left': res.group(1),
                        'comp_op': res.group(2),
                        'right': res.group(3),
                        'if_true': res.group(8),
                        'if_false': res.group(10)
                    })
                elif l == "assign_const":
                    r['format'].update({
                        'left': res.group(1),
                        'right': res.group(2),
                    })
                elif l == "assign_var":
                    r['format'].update({
                        'left': res.group(1),
                        'right': res.group(2),
                    })

                elif l == "assign_string_const":
                    r['format'].update({
                        'left': res.group(1),
                        'right': res.group(2),
                    })

                elif l == "assign_function_call":
                    r['format'].update({
                        'left': res.group(2),
                        'func_name': res.group(3),
                        'arguments': res.group(4)
                    })

                elif l == "assign_aryphmetic_op":
                    r['format'].update({
                        'left': res.group(1),
                        'r_operand1': res.group(2),
                        'op': res.group(6),
                        'r_operand2': res.group(7),
                    })
                elif l == "goto":
                    r['format'].update({
                        'dest': res.group(1),
                    })

                elif l == "assign_MEM":
                    r['format'].update({
                        'left': "",
                        'cast': "",
                        'base': "",
                        'op': "",
                        'shift': ""
                    })

                print("PATTERN:\n", l)
                print("FORMAT:\n", r['format'], "\n---------------")
                node_lex_dict.update({n.get_name():{'pattern':l,'content':r}})
                pass
                nodes[l].append(n.get_name())

                continue

        if n.get_name() not in node_lex_dict.keys():
                node_lex_dict.update({n.get_name(): {'pattern': "none", 'content': None}})

        return node_lex_dict[n.get_name()], nodes

    for e in graph.get_edges():
        src, dst = edge_get_nodes(graph, e)
        make_lex_node(src)
        make_lex_node(dst)
        e.set('label', node_lex_dict[src.get_name()]['pattern']+" "+node_lex_dict[dst.get_name()]['pattern'])
    return graph, nodes, node_lex_dict


def shortest_path_check(graph, src, dst):
    nx_graph = nx.nx_pydot.from_pydot(graph)
    if nx.shortest_path(nx_graph, src, dst):
        return True
    return False


'''
default_pattern_composer-- now only fill fields, no specialize (or maybe later)
P - specializing by and for some pattern
'''
def default_pattern_composer(scenario={}):
    P = {'yes_df_list': [], 'no_df_list': [], 'yes_cf_list': [], 'no_cf_list': [], 'rel_kinds': set()}
    return P


def default_specializer(graph, nodes, node_lex_dict, P):
    return graph

'''
specialize_Dflow -- специализация по потоку данных (def-use)
# nodes: словарь по типам вершин
# P -- list(patterns (relation ))
'''
def specialize_Dflow(graph, nodes, node_lex_dict, P):
    for p in P: # for each entity (relation, edge) of pattern
        for n in nodes[p.left['type']]:
            n1s = node_lex_dict[n]['content']
            for n2 in nodes[p.right['type']]:
                n2s = node_lex_dict[n2]['content']
                # TO DO: check scope!
                if not p.extra and p.predicate(n1s['format'], n2s['format']) and shortest_path_check(graph, n, n2):
                    graph.add_edge(pydot.Edge(n,
                                    n2,
                                    color=p.params["edge_style"]["color"],
                                    style='dashed',
                                    label=p.label))
    return graph


def markup_graph(graph, nodes, nld, pattern_composer=default_pattern_composer, scenario=None, specializer=default_specializer):
    P = pattern_composer(scenario)
    # Adjust graph by extra edges marking (specializing)
    for _p in P["yes_df_list"]:
        graph = specializer(graph=graph, nodes=nodes, node_lex_dict=nld, P=_p)
    for _p in P["no_df_list"]:
        graph = specializer(graph=graph, nodes=nodes, node_lex_dict=nld, P=_p)
    return graph, P

def markup_edges(graph=pydot.Graph(), mapping={}):
    edges = graph.get_edges()
    for e in edges:
        attr = e.get_attributes()
        previous_label = attr['label']
        if attr['label'] in mapping.keys():
            e.set('label', mapping[attr['label']])
        elif attr['label'].split(" ")[0] + " any" in mapping.keys():
            e.set('label', mapping[attr['label'].split(" ")[0] + " any"])
        elif len(attr['label'].split(" ")) >= 2 and "any "+attr['label'].split(" ")[1] in mapping.keys():
            e.set('label', mapping["any "+attr['label'].split(" ")[1]])
        elif "any any" in mapping.keys():
            e.set('label', mapping["any any"])
        else:
            print("Error in markup")
            sys.exit(1)
        print("Edge remap:", e.get_source(), e.get_destination, previous_label, e.get_attributes()['label'])

    return graph
