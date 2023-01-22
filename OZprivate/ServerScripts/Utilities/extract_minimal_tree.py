import argparse
import re

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument(
    "Tree_File", type=argparse.FileType('r'), help="A tree file in newick form")
args = parser.parse_args()
taxa = ["Primates"]
taxa = ["Piliocolobus_badius"]
taxa = ["Homininae"]
taxa = ["Vicugna", "Pan_paniscus"]
taxa = ["Camelidae"]
taxa = ["Bad"]
taxa = ["Sylvilagus_nuttallii", "Trichechus_manatus", "Pan_paniscus", "Canis_lupus",
        "Ornithorhynchus_anatinus", "Discoglossus_montalentii", "Heterodontus_japonicus"]
taxa = ["Vicugna", "Homininae"]
taxa = ["Rodentia", "Lagomorpha", "Primates", "Dermoptera", "Tupaia"]
taxa = ["Glires", "Primates", "Scandentia"]
taxa = ["Rodentia", "Lagomorpha", "Primates", "Dermoptera", "Tupaia"]

tree = args.Tree_File.read()

# We build the node list as we find them and process them
nodes = []

index = 0
index_stack = []

whole_token_regex = re.compile('[^(),;]*')
taxon_regex = re.compile('^(\w*)_ott\d*(:[\d\.]*)?')

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
        # start_index = index
    else:
        start_index = index

    match_full_name = whole_token_regex.match(tree, index)
    index += match_full_name.end() - index

    match_taxon = taxon_regex.match(match_full_name.group())
    if (match_taxon):
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
            # We've found at least two nodes that match the current depth, so remove them and wrap them in a new node
            # TODO: handle polytomies when creating the new node
            nodes = [n for n in nodes if n not in nodes_with_current_depth]
            nodes.append(
                {"tree_string": f"({nodes_with_current_depth[0]['tree_string']},{nodes_with_current_depth[1]['tree_string']}){match_full_name.group()}",
                "depth": len(index_stack)})

    if tree[index] == ',':
        index += 1

if taxa:
    print(f"Could not find target taxon '{taxa[0]}' in the tree")
else:
    print(nodes[0]['tree_string'] + ";")