import argparse
import re

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument(
    "Tree_File", type=argparse.FileType('r'), help="A tree file in newick form")
args = parser.parse_args()
taxas = ["Vicugna"]
taxas = ["Primates"]
taxas = ["Camelidae"]
taxas = ["Piliocolobus_badius"]
taxas = ["Bad"]
taxas = ["Homininae"]
taxas = ["Vicugna","Pan_paniscus"]
taxas = ["Ochotona_curzoniae","Pan_paniscus"]

tree = args.Tree_File.read()
nodes = {taxa:{"depth":-1} for taxa in taxas}

index = 0
index_stack = []

# Camelus_ott510767:9.464505

whole_token_regex = re.compile('[^(),;]*')
taxon_regex = re.compile('^(\w*)_ott\d*(:[\d\.]*)?')

while True:
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
    else:
        start_index = index

    match_full_name = whole_token_regex.match(tree, index)
    index += match_full_name.end() - index

    match_taxon = taxon_regex.match(match_full_name.group())
    if (match_taxon):
        taxon = match_taxon.group(1)
        if taxon in nodes:
            nodes[taxon]["tree_string"] = tree[start_index:index]
            nodes[taxon]["depth"] = len(index_stack)
            print(f"Found {taxon} at depth {len(index_stack)} and position {index}")
            print(nodes[taxon]["tree_string"])

    if closed_brace:
        lowered = []
        for node in nodes.items():
            if node[1]["depth"] == len(index_stack)+1:
                node[1]["depth"] -= 1
                lowered.append(node)
                pass
        if len(lowered) > 1:
            print(f"({lowered[0][1]['tree_string']},{lowered[1][1]['tree_string']}){match_full_name.group()}")
            break

    if tree[index] == ',':
        index += 1
