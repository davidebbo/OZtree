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

def process_node(node, parent_age):
    node_age = node.edge_length if node.edge_length else 0

    node.edge_length = round(parent_age - node_age, 2)
    if node.edge_length == 0:
        node.edge_length = None 

    for child_node in node.child_nodes():
        process_node(child_node, node_age)


tree = Tree.get(stream=args.OpenTree_file, schema="newick", suppress_leaf_node_taxa=True)
process_node(tree.seed_node, tree.seed_node.edge_length)
print(tree)
