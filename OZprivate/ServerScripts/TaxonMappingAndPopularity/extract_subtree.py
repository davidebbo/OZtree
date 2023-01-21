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

def test_dendropy(tree_filename):
    try:
        tree = Tree.get_from_path(
            tree_filename,
            schema="newick",
            preserve_underscores=True,
            suppress_leaf_node_taxa=True)
    except:
        sys.exit("Problem reading tree from " + tree_filename)
    logging.info(" > read tree from " + tree_filename)

def test_read_all_bytes(tree_filename):
    count = 0
    with open(tree_filename) as f:
        while (f.read(1)):
            continue
            count += 1

    print(f"Count={count}")

def test_read_as_one_string(tree_filename):
    with open(tree_filename) as f:
        s = f.read()
    
    index = 0
    for c in s:
        # continue
        index += 1

    print(f"Count={index}")

def test_fast(taxon, tree_filename, output_filename):

    def peek():
        c = f.read(1)
        f.seek(f.tell()-1)
        return c

    def read_char():
        return f.read(1)
        # try:
        #     c = f.read(1)
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
        f.seek(f.tell()-1)
        return token

    def parse_node():
        start_index = f.tell()

        if f.read(1) != '(':
            raise Exception("Missing '(' at start of node")

        while True:
            if peek() == '(':
                if (result := parse_node()) != None:
                    return result
            else:
                parse_token()

            match f.read(1):
                case ',':
                    polynomie_count += 1
                    if polynomie_count > 5:
                        print(f"{token}: {polynomie_count}")
                    continue
                case ')':
                    if parse_token().startswith(taxon):
                        return (start_index, f.tell() - start_index)
                    return None

    with open(tree_filename) as f:
        if (result := parse_node()) != None:
            f.seek(result[0])
            with open(output_filename, "w") as output_file:
                output_file.write(f.read(result[1]))
                output_file.write(';')
        else:
            print('Not found!')

def test_fast_one_string(taxon, tree_filename, output_filename):

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

            match read_char():
                case ',':
                    polynomie_count += 1
                    continue
                case ')':
                    if polynomie_count >= 50:
                        print(f"{token}: {polynomie_count}")
                    if parse_token().startswith(taxon):
                        return (start_index, index - start_index)
                    return None

    with open(tree_filename) as f:
        newick_string = f.read()
    length = len(newick_string)

    if (result := parse_node()) != None:
        with open(output_filename, "w") as output_file:
            output_file.write(newick_string[result[0]:result[0] + result[1]])
            output_file.write(';')
    else:
        print('Not found!')



def main(args):
    logging.info("Starting")
    print(args.inputFile)
    print(args.outputFile)

    # test_fast(args.taxon, args.inputFile, args.outputFile)
    test_fast_one_string(args.taxon, args.inputFile, args.outputFile)
    # test_read_all_bytes(args.inputFile)
    # test_read_as_one_string(args.inputFile)
    # test_dendropy(args.inputFile)

    print(f"Mem usage {mem():.1f} Mb")
    logging.info("Done")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Convert a newick file with OpenTree labels into refined trees and CSV tables, while mapping Open Tree of Life Taxonomy IDs to other ids (including EoL & Wikidata)')
    parser.add_argument('taxon', 
        help='The name of the taxon we search for')
    parser.add_argument('inputFile', 
        help='The input file in newick format')
    parser.add_argument('outputFile', 
        help='The output file where the extracted subtree should be saved')

    args = parser.parse_args()
    main(args)
    