import csv
import sys
import os
import json


def make_upload_metadata(csv_input, data_locations):
    """example of how to make the upload metadata files"""

    # read a metadata file containing data we need
    text = open(csv_input, "rb").read().decode("ascii", errors="ignore").split("\n")
    r = csv.reader(text)

    # build a data location database - this is a hash table between a data set
    # key from the CSV above and the directory on disk

    loc_db = {}
    for record in open(data_location):
        key = os.path.split(record)[-1].lower().strip()
        loc_db[key] = record.strip()

    # author information etc.

    DLS = "Diamond Light Source"
    SGC = "SGC-Oxford"

    authors = {"Doe, John R.": DLS, "Other, Andrea N.": "Other laboratory"}

    # iterate through the spreadsheet, making a metadata json file for each
    # row in the file

    for row in r:
        if not len(row):
            continue

        # how we interpret the csv will be case by case
        if row[5] != "Deposited":
            continue

        set_id = row[0].lower()
        smiles = row[2]
        compound = row[4]
        pdb_id = row[6]

        # make metadata.json files - this is the merge step

        title = (
            "Raw diffraction data for structure of SARS-CoV-2 main protease with %s (ID: %s / PDB: %s)"
            % (compound, set_id, pdb_id)
        )

        description = """Raw diffraction data for %s / PDB ID %s (see: https://www.ebi.ac.uk/pdbe/entry/pdb/%s) - SARS-CoV-2 main protease in complex with %s (SMILES:%s) collected as part of an XChem crystallographic fragment screening campaign. The deposited structure was automatically processed with standard Diamond tools and PanDDA, however the raw data are being made available to allow reanalysis by any interested party. 

For more details see: https://www.diamond.ac.uk/covid-19/for-scientists/Main-protease-structure-and-XChem.html
""" % (
            set_id,
            pdb_id,
            pdb_id,
            compound,
            smiles,
        )

        # if you want to make .zip files from CBF files use this - if you
        # want to include > 1 directory you can have > 1 zip file but these
        # have to match 1:1
        archive = ["%s.zip" % set_id]
        directory = [loc_db[set_id]]

        # alt: if you have HDF5 can just give the directory and it will upload
        # or an explicit file list

        # make the metadata dictionary - N.B. by default authors in alphabetical
        # order (case *insensitive*)
        metadata = {
            "directory": directory,
            "archive": archive,
            "title": title,
            "description": description,
            "creators": [
                {"name": name, "affiliation": authors[name]}
                for name in sorted(authors, key=str.casefold)
            ],
            "communities": [{"identifier": "mx", "identifier": "covid-19"}],
            "keywords": [
                "COVID-19",
                "SARS-CoV-2 main protease",
                "automated upload",
                "PDB:%s" % pdb_id,
            ],
        }
        with open("%s.json" % set_id, "w") as f:
            json.dump(metadata, f)

        print(set_id)


if __name__ == "__main__":
    csv_input = sys.argv[1]
    data_locations = sys.argv[2]
    make_upload_metadata(csv_input, data_locations)
