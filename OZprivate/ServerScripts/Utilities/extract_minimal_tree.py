#!/usr/bin/env python3

import argparse
import sys
import re

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('treefile', type=argparse.FileType('r'), nargs='?', default=sys.stdin, help='The tree file in newick form')
args = parser.parse_args()


taxa = ["Primates"]
taxa = ["Piliocolobus_badius"]
taxa = ["Homininae"]
taxa = ["Vicugna", "Pan_paniscus"]
taxa = ["Camelidae"]
taxa = ["Bad"]
taxa = ["Vicugna", "Homininae"]
taxa = ["Rodentia", "Lagomorpha", "Primates", "Dermoptera", "Tupaia"]
taxa = ["Glires", "Primates", "Scandentia"]
taxa = ["Rodentia", "Lagomorpha", "Primates", "Dermoptera", "Tupaia"]
taxa = ["Sylvilagus_nuttallii", "Trichechus_manatus", "Pan_ppaniscus", "Canis_lupus",
        "Ornithorhynchus_anatinus", "Discoglossus_montalentii", "Heterodontus_japonicus"]
taxa = ["Tupaia_chrysogaster", "Tupaia_belangeri", "Canis_lupus", "Tupaia_montana", "Tupaia_moellendorffi"]

tree = args.treefile.read()

# We build the node list as we find them and process them
nodes = []

index = 0
index_stack = []

whole_token_regex = re.compile('[^(),;]*')
taxon_regex = re.compile('^(\w*)_ott\d*(:[\d\.]*)?')

taxon_count=0

while taxa or len(nodes) >= 2:
    if index == len(tree) or tree[index] == ';':
        break

    if tree[index] == '(':
        index_stack.append(index)
        index += 1
        continue

    closed_brace = tree[index] == ')'
    if closed_brace:
        index += 1
        start_index = index_stack.pop()
        start_index = index
    else:
        start_index = index

    match_full_name = whole_token_regex.match(tree, index)
    index += match_full_name.end() - index

    match_taxon = taxon_regex.match(match_full_name.group())
    if (match_taxon):
        # taxon_count += 1

        taxon = match_taxon.group(1)
        if taxon in taxa:
            # We've found a taxon, so remove it from the list, and create a node for it
            taxa.remove(taxon)
            nodes.append(
                {"tree_string": tree[start_index:index], "depth": len(index_stack)})

    if closed_brace:
        nodes_with_current_depth = [n for n in nodes if n["depth"] == len(index_stack) + 1]
        for node in nodes_with_current_depth:
            node["depth"] -= 1

        if len(nodes_with_current_depth) > 1:
            # We've found at least two nodes that match the current depth

            # Remove them from the list of nodes we're looking for
            nodes = [n for n in nodes if n not in nodes_with_current_depth]

            # Replace them by a new node that wraps them
            nodes.append(
                {"tree_string": f"({','.join([node['tree_string'] for node in nodes_with_current_depth])}){match_full_name.group()}",
                "depth": len(index_stack)})

    if tree[index] == ',':
        index += 1

if taxa:
    print(f"Could not find target taxon '{taxa[0]}' in the tree")
else:
    print(nodes[0]['tree_string'] + ";")

print(f"Taxon count: {taxon_count}")
