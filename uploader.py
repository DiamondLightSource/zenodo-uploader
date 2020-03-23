import argparse
import requests
import os
import sys
import json
import pprint


def get_access_token(sandbox=False):
    """get upload key, strip white space."""

    if sandbox:
        return open(os.path.join(os.environ["HOME"], ".sandbox_id"), "r").read().strip()
    else:
        return open(os.path.join(os.environ["HOME"], ".zenodo_id"), "r").read().strip()


class zenodo_uploader(object):
    """tool to upload files to http://zenodo.org"""

    def __init__(self, directory, metadata, sandbox=False):

        # validate the structure of the metadata - there will be critical
        # items which must be present for this to be a useful deposition

        if not "metadata" in metadata:
            raise ValueError("metadata key missing")

        valid = set(("title", "description", "creators", "keywords"))
        names = set(metadata["metadata"])

        if names - valid:
            raise ValueError("unknown metadata keys: %s" % (" ".join(names - valid)))
        if valid - names:
            raise ValueError("missing metadata keys: %s" % (" ".join(valid - names)))

        # add standard metadata

        metadata["metadata"].update(
            {
                "access_right": "open",
                "upload_type": "dataset",
                "communities": [{"identifier": "mx"}],
            }
        )

        self._directory = directory
        self._metadata = metadata
        self._token = get_access_token(mode)
        self._dep_id = None
        self._dep_url = None
        if sandbox:
            self._server = "https://sandbox.zenodo.org"
        else:
            self._server = "https://zenodo.org"

        for k in "title", "description", "creators", "keywords":
            print(metadata["metadata"][k])

    def _create(self):
        """create new empty deposition"""
        r = requests.post(
            "%s/api/deposit/depositions" % self._server,
            params={"access_token": self._token},
            json={},
            headers={"Content-Type": "application/json"},
        )

        pprint.pprint(r.json())
        if not r.status_code in (200, 201, 202):
            raise RuntimeError("in create: HTTP status %d" % r.status_code)

        r_json = r.json()
        self._dep_id = r_json["id"]
        self._dep_url = r_json["links"]["bucket"]

        print("Created deposition: id = %s" % self._dep_id)

    def _update(self):
        """push the metadata for this deposition"""

        r = requests.put(
            "%s/api/deposit/depositions/%s" % (self._server, self._dep_id),
            params={"access_token": self._token},
            data=json.dumps(self._metadata),
            headers={"Content-Type": "application/json"},
        )

        if not r.status_code in (200, 201, 202):
            raise RuntimeError("in create: HTTP status %d" % r.status_code)

        print("Uploaded metadata for: %s" % (self._metadata["metadata"]["title"]))

    def _upload(self, filename):
        """upload file using stream API"""

        print("Uploading: %s" % filename)

        with open(os.path.join(self._directory, filename), "rb") as fin:
            r = requests.put(
                "%s/%s" % (self._dep_url, filename),
                data=fin,
                params={"access_token": self._token},
            )

        if not r.status_code in (200, 201, 202):
            raise RuntimeError("in create: HTTP status %d" % r.status_code)

        print("Upload complete")

    def _publish(self):
        """complete the deposition process"""
        pass

    def upload(self):
        """process files for upload"""

        # FIXME wrap this in a try except

        self._create()
        self._update()
        for filename in os.listdir(self._directory):
            self._upload(filename)
        self._publish()

        # and in the except, delete the partial upload as it is broken
        # - particularly to catch Ctrl-C


def uploader():
    """main() - parse args, make Zenodo uploader, execute, catch errors"""

    parser = argparse.ArgumentParser()

    # zenodo / administrative matters
    parser.add_argument("-z", "--zenodo_id", help="zenodo upload key")
    parser.add_argument("-s", "--sandbox", help="use sandbox mode", action="store_true")

    # file related stuff
    parser.add_argument(
        "-d", "--directory", help="directory to upload", action="append"
    )
    parser.add_argument("files", nargs="*", help="individual files")

    # what we are doing with the files
    parser.add_argument(
        "-a",
        "--archive",
        help="pack directory to named archive before upload",
        action="append",
    )
    args = parser.parse_args()

    # validate inputs - must pass some files, only pass files _or_ directories
    if not args.directory and not args.files:
        sys.exit("must pass some files for upload")
    if args.directory and args.files:
        sys.exit("only pass files or directories")

    if args.archive:
        if args.files and len(args.archive) != 1:
            sys.exit(
                "if passing individual files and archive, only one archive allowed"
            )
        if args.directory and len(args.directory) != len(args.archive):
            sys.exit("number of archives must equal number of directories")

    if not args.zenodo_id:
        args.zenodo_id = get_access_token(sandbox=args.sandbox)

    print("ID: %s" % args.zenodo_id)
    if args.directory:
        for j, directory in enumerate(args.directory):
            archive = args.archive[j] if args.archive else None
            if archive:
                print("%s => %s" % (directory, archive))
            else:
                print("%s" % (directory))
    else:
        if args.archive:
            print("%s <=" % args.archive[0])
            for f in args.files:
                print("  %s" % f)


if __name__ == "__main__":
    uploader()

if __name__ == "__dumb__":

    metadata = {
        "metadata": {
            "title": "Test automated upload of Eiger data set 2",
            "description": """Example data set of cubic insulin recorded on Diamond Light source beamline I04 - being used here as a test upload using the Zenodo REST API. Probably should have things like a deposition ID in here as well as crystallisation condition smiles strings or something.""",
            "creators": [
                {"name": "Winter, Graeme", "affiliation": "Diamond Light Source"}
            ],
            "keywords": ["automated upload"],
        }
    }

    zu = zenodo_uploader(sys.argv[1], metadata, sandbox=True)
    zu.upload()
