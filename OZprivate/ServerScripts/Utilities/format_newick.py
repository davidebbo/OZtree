#!/usr/bin/env python3
"""
Transform an ultrametric newick tree into an additive newick tree
"""
import argparse
from dendropy import Tree

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument(
    "OpenTree_file", type=argparse.FileType('r'), help="The ultrametric tree in newick form")
# parser.add_argument(
#     "outfile", type=argparse.FileType('w'), nargs='?', default=sys.stdout, help="The output tree")
args = parser.parse_args()

tree = Tree.get(stream=args.OpenTree_file, schema="newick", suppress_leaf_node_taxa=True)

output_string = ""
indent_string = "  "

def get_full_label(node):
    full_label = ""
    if node.label:
        full_label += node.label
    if node.edge_length:
        full_label += ":" + str(node.edge_length)
    return full_label

def process_node(node, depth):
    global output_string



    if len(node.child_nodes()) > 0:
        output_string += indent_string * depth + "(\n"

        for count, child_node in enumerate(node.child_nodes()):
            process_node(child_node, depth+1)
            if count < len(node.child_nodes())-1:
                output_string += ","
            output_string += "\n"

        output_string += indent_string * depth + ")" + get_full_label(node)
    else:
        output_string += indent_string * depth + get_full_label(node)

process_node(tree.seed_node, 0)
output_string += ";"
print(output_string)

