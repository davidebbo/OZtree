import argparse
import json
import math
import os
import time
import requests
import sys

import urllib.request
from getEOL_crops import subdir_name, get_credit, get_file_from_json_struct, convert_rating
from db_helper import connect_to_database, read_configuration_file
from farmhash import FarmHash32

# to get globals from ../../../models/_OZglobals.py
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), os.path.pardir, os.path.pardir, os.path.pardir, "models")))
from _OZglobals import src_flags, eol_inspect_via_flags, image_status_labels

def main():
    default_appconfig_file = "../../../private/appconfig.ini"

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--database', '-db', default=None, help='name of the db containing eol ids, in the same format as in web2py, e.g. sqlite://../databases/storage.sqlite or mysql://<mysql_user>:<mysql_password>@localhost/<mysql_database>. If not given, the script looks for the variable db.uri in the file {} (relative to the script location)'.format(default_appconfig_file))
    parser.add_argument('--output_dir', '-o', default=None, help="The location to save the cropped pictures (e.g. 'FinalOutputs/img'). If not given, defaults to ../../../static/FinalOutputs/img (relative to the script location). Files will be saved under output_dir/{src_flag}/{3-digits}/fn.jpg")
    parser.add_argument(
        "taxon_data_file",
        type=argparse.FileType("r"),
        help="The tree file in newick form",
    )
    args = parser.parse_args()

    if args.database is None:
        args.database, args.EOL_API_key = read_configuration_file(default_appconfig_file, args.database, None)

    if args.output_dir is None:
        args.output_dir = os.path.join( # up 3 levels from script, then down
            os.path.dirname(os.path.abspath(__file__)), 
            os.pardir,
            os.pardir,
            os.pardir,
            'static',
            'FinalOutputs',
            'img')

    db_connection, datetime_now, subs = connect_to_database(args.database, None, None)
    db_curs = db_connection.cursor()
    db_curs.execute("SELECT ott,name FROM OneZoom.ordered_leaves WHERE ott is not null;")

    # Get the results in a dictionary, keyed by ott
    taxon_by_ott = dict(db_curs.fetchall())

    # print the first 10 items from the dictionary
    for ott in list(taxon_by_ott.keys())[:10]:
        print(ott, taxon_by_ott[ott])

    db_curs.execute("SELECT ott FROM OneZoom.images_by_ott;")

    # Get the results in a set
    ott_with_images = set([r[0] for r in db_curs.fetchall()])

    # Find all the otts that don't have images
    ott_without_images = set(taxon_by_ott.keys()) - ott_with_images

    # print the first 10 items from the set
    for ott in list(ott_without_images)[:10]:
        print(ott, taxon_by_ott[ott])

    # Read the json data file
    taxon_data = json.load(args.taxon_data_file)

    for ott in ott_without_images:
        if taxon_by_ott[ott] in taxon_data:
            taxon = taxon_by_ott[ott]
            data = taxon_data[taxon]
            if "redirect" in data:
                data = taxon_data[data["redirect"]]
            if "image" in data:
                image_name = data["image"]
                print(f"{ott}\t{taxon}\t{image_name}")

                url = f"https://api.wikimedia.org/core/v1/commons/file/{image_name}"
                print(url)

                # See https://meta.wikimedia.org/wiki/User-Agent_policy
                headers = {
                    "User-Agent": "OneZoomBot/0.1 (https://www.onezoom.org/; mail@onezoom.org) get-wiki-images/0.1"
                }
                r = requests.get(url, headers=headers)
                if r.status_code == 200:
                    image_data = r.json()
                    image_url = image_data["preferred"]["url"]
                    print(image_url)

                    image_hash = FarmHash32(image_name) - int(math.pow(2, 31))

                    output_dir = os.path.join(args.output_dir, 
                        str(src_flags['wiki']), subdir_name(image_hash))

                    # Create the output directory if it doesn't exist
                    if not os.path.exists(output_dir):
                        os.makedirs(output_dir)

                    # Download the image
                    file_path = f"{output_dir}/{image_hash}.jpg"
                    if not os.path.exists(file_path):
                        urllib.request.urlretrieve(image_url, file_path)

                    wikimedia_url = f"https://commons.wikimedia.org/wiki/{image_name}"
                    sql = "INSERT INTO images_by_ott (ott, src, src_id, url, rating, rating_confidence, best_any, best_verified, best_pd, overall_best_any, overall_best_verified, overall_best_pd, rights, licence, updated) VALUES ({0}, {0}, {0}, {0}, {0}, {0}, {0}, {0}, {0}, {0}, {0}, {0}, {0}, {0}, {1});".format(subs, datetime_now)
                    db_curs.execute(sql, (ott, src_flags['wiki'], image_hash, 
                                            wikimedia_url, 
                                            25000,
                                            None,
                                            1,
                                            1,
                                            1,
                                            1, 1, 1,
                                            "None", "TODO"))
                    db_connection.commit()

                    # Sleep for 1 second to avoid being rate limited
                    time.sleep(1)
                elif r.status_code == 404:
                    print("Not found")
                elif r.status_code == 429:
                    print("Rate limited")
                    time.sleep(60)
                else:
                    print(f"Error: {r.status_code}")
                    print(r.text)
                    





if __name__ == "__main__":
    main()
