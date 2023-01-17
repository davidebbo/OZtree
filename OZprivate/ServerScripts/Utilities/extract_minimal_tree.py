import argparse
import re

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument(
    "Tree_File", type=argparse.FileType('r'), help="A tree file in newick form")
args = parser.parse_args()
taxa = ["Vicugna"]
taxa = ["Primates"]
taxa = ["Camelidae"]
taxa = ["Piliocolobus_badius"]
taxa = ["Bad"]
taxa = ["Homininae"]
taxa = ["Vicugna","Pan_paniscus"]
taxa = ["Sylvilagus_nuttallii", "Trichechus_manatus", "Pan_paniscus", "Canis_lupus", "Ornithorhynchus_anatinus", "Discoglossus_montalentii", "Heterodontus_japonicus"]

tree = args.Tree_File.read()

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
    else:
        start_index = index

    match_full_name = whole_token_regex.match(tree, index)
    index += match_full_name.end() - index

    match_taxon = taxon_regex.match(match_full_name.group())
    if (match_taxon):
        taxon = match_taxon.group(1)
        if taxon in taxa:
            taxa.remove(taxon)
            nodes.append({"tree_string": tree[start_index:index], "depth": len(index_stack)})

    if closed_brace:
        lowered = [n for n in nodes if n["depth"] == len(index_stack)+1]
        for node in lowered:
            node["depth"] -= 1
            
        if len(lowered) > 1:
            nodes = [n for n in nodes if n not in lowered]
            nodes.append({"tree_string": f"({lowered[0]['tree_string']},{lowered[1]['tree_string']}){match_full_name.group()}", "depth": len(index_stack)})

    if tree[index] == ',':
        index += 1

if taxa:
    print(f"Could not find target taxon '{taxa[0]}' in the tree")
else:
    print(nodes[0]['tree_string'] + ";")
