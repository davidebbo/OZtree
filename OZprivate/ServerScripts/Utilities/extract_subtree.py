#!/usr/bin/env -S python3 -u
"""
"""

import argparse
import logging
import sys

from dendropy import Node, Tree

def mem():
    import resource
    rusage_denom = 1024.
    if sys.platform == 'darwin':
        # ... it seems that in OSX the output is different units ...
        # perhaps update to try psutils instead
        rusage_denom = rusage_denom * rusage_denom
    mem = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / rusage_denom
    return mem

def test_dendropy(tree_file, taxon):
    tree = Tree.get(stream=args.treefile, schema='newick', preserve_underscores=True, suppress_leaf_node_taxa=True, suppress_internal_node_taxa=True)
    # subtree = tree.extract_tree_with_taxa(taxa=taxon)
    # subtree = tree.extract_tree_with_taxa_labels(labels=taxon)
    # taxa_to_retain = set([t for t in tree.taxon_namespace
    #         if t.label.startswith(taxon)])
    # subtree = tree.extract_tree_with_taxa(taxa=taxa_to_retain)

    # node_filter_fn = lambda nd: nd.is_internal() or nd.taxon.label.startswith(taxon)
    # subtree = tree.extract_tree(node_filter_fn=node_filter_fn)

    # node_filter_fn = lambda nd: nd.taxon is None or nd.taxon.label.startswith(taxon)
    # subtree = tree.extract_tree(node_filter_fn=node_filter_fn)

    # print(subtree)

    print("Done")

def test_read_all_bytes(tree_file):
    count = 0
    while (tree_file.read(1)):
        continue
        count += 1

    print(f"Count={count}")

def test_read_as_one_string(tree_file):
    s = tree_file.read()
    
    index = 0
    for c in s:
        # continue
        index += 1

    print(f"Count={index}")

def test_fast(tree_file, output_file, taxon):

    def peek():
        c = tree_file.read(1)
        tree_file.seek(tree_file.tell()-1)
        return c

    def read_char():
        return tree_file.read(1)
        # try:
        #     c = tree_file.read(1)
        # except UnicodeDecodeError:
        #     # Replace bad character with _
        #     c = '_'
        # return c

    def parse_token():
        token = ""
        while (c := read_char()) not in (',', ')', ';'):
            if not c:
                raise Exception("File should end with ';'")
            token += c
        tree_file.seek(tree_file.tell()-1)
        return token

    def parse_node():
        start_index = tree_file.tell()

        if tree_file.read(1) != '(':
            raise Exception("Missing '(' at start of node")

        while True:
            if peek() == '(':
                if (result := parse_node()) != None:
                    return result
            else:
                parse_token()

            c = tree_file.read(1)
            if c == ',':
                continue

            if c == ')':
                if parse_token().startswith(taxon):
                    return (start_index, f.tell() - start_index)
                return None
            
    if (result := parse_node()) != None:
        tree_file.seek(result[0])
        output_file.write(tree_file.read(result[1]))
        output_file.write(';')
    else:
        print('Not found!')

def test_fast_one_string(tree_file, output_file, taxon):

    newick_string = ""
    index = 0
    length = 0

    def peek():
        nonlocal index
        if index == length:
            return ''
        return newick_string[index]

    def read_char():
        nonlocal index
        if index == length:
            return ''
        index += 1
        return newick_string[index-1]

    def parse_token():
        nonlocal index
        token = ""
        while (c := read_char()) not in (',', ')', ';'):
            if not c:
                raise Exception("File should end with ';'")
            token += c
        index -= 1
        return token

    def parse_node():
        nonlocal index
        start_index = index

        if read_char() != '(':
            raise Exception("Missing '(' at start of node")

        polynomie_count = 0
        while True:
            token=""
            if peek() == '(':
                if (result := parse_node()) != None:
                    return result
            else:
                token = parse_token()

            c = read_char()
            if c == ',':
                polynomie_count += 1
                continue
            elif c == ')':
                if polynomie_count >= 8000:
                    print(f"{token}: {polynomie_count}")
                if parse_token().startswith(taxon):
                    return (start_index, index - start_index)
                return None

    newick_string = tree_file.read()
    length = len(newick_string)

    if (result := parse_node()) != None:
        output_file.write(newick_string[result[0]:result[0] + result[1]])
        output_file.write(';')
    else:
        print('Not found!')


def main(args):
    logging.info("Starting")

    # test_fast(args.treefile, args.outfile, args.taxon)
    # test_fast_one_string(args.treefile, args.outfile, args.taxon)
    # test_read_all_bytes(args.treefile)
    # test_read_as_one_string(args.treefile)
    test_dendropy(args.treefile, args.taxon)

    print(f"Mem usage {mem():.1f} Mb")
    logging.info("Done")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Convert a newick file with OpenTree labels into refined trees and CSV tables, while mapping Open Tree of Life Taxonomy IDs to other ids (including EoL & Wikidata)')
    parser.add_argument('treefile', type=argparse.FileType('r'), nargs='?', default=sys.stdin, help='The tree file in newick form')
    parser.add_argument('outfile', type=argparse.FileType('w'), nargs='?', default=sys.stdout, help='The output tree file')
    # parser.add_argument('--indent_spaces', '-i', default=2, type=int, required=True, help='the number of spaces for each indentation level')
    parser.add_argument('--taxon', '-t', required=True, help='the taxon to search for')

    args = parser.parse_args()
    main(args)
    