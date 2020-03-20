import requests
import os
import sys
import json
import pprint


def get_access_token():
    """get upload key, strip white space."""

    return open(os.path.join(os.environ["HOME"], ".zenodo_id"), "r").read().strip()


class zenodo_uploader(object):
    """tool to upload files to http://zenodo.org"""

    def __init__(self, directory, metadata):

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
        self._token = get_access_token()
        self._dep_id = None
        self._dep_url = None

        for k in "title", "description", "creators", "keywords":
            print(metadata["metadata"][k])

    def _create(self):
        """create new empty deposition"""
        headers = {"Content-Type": "application/json"}
        r = requests.post(
            "https://zenodo.org/api/deposit/depositions",
            params={"access_token": self._token},
            json={},
            headers=headers,
        )

        # FIXME check status code - r.status_code

        r_json = r.json()
        self._dep_id = r_json["id"]
        self._dep_url = r_json["links"]["bucket"]

        # FIXME some logging would be cute about here

    def _update(self):
        """push the metadata for this deposition"""

        r = requests.put(
            "https://zenodo.org/api/deposit/depositions/%s" % self._dep_id,
            params={"access_token": self._token},
            data=json.dumps(self._metadata),
            headers=headers,
        )

        # FIXME check status code - r.status_code
        # FIXME some logging would be cute about here

    def upload(self):
        """process files for upload"""

        # FIXME wrap this in a try except

        self._create()
        self._update()

        # and in the except, delete the partial upload as it is broken
        # - particularly to catch Ctrl-C


def action_upload(directory):

    ACCESS_TOKEN = get_access_token()

    headers = {"Content-Type": "application/json"}
    r = requests.post(
        "https://zenodo.org/api/deposit/depositions",
        params={"access_token": ACCESS_TOKEN},
        json={},
        headers=headers,
    )

    print(r.status_code)
    print(r.json())

    d_id = r.json()["id"]

    bucket_url = r.json()["links"]["bucket"]

    # list the upload directory / file list for files to upload
    for filename in os.listdir(directory):
        print(filename)

        # use new stream-based API
        with open(os.path.join(directory, filename), "rb") as fin:
            r = requests.put(
                "%s/%s" % (bucket_url, filename),
                data=fin,
                params={"access_token": ACCESS_TOKEN},
            )
        pprint.pprint(r.json())

    # now add some metadata

    metadata = {
        "metadata": {
            "title": "Test automated upload of Eiger data set",
            "upload_type": "dataset",
            "description": """Example data set of cubic insulin recorded on Diamond Light source beamline I04 - being used here as a test upload using the Zenodo REST API. Probably should have things like a deposition ID in here as well as crystallisation condition smiles strings or something.""",
            "creators": [
                {"name": "Winter, Graeme", "affiliation": "Diamond Light Source"}
            ],
            "keywords": ["automated upload"],
            "access_right": "open",
            "communities": [{"identifier": "mx"}],
        }
    }

    r = requests.put(
        "https://zenodo.org/api/deposit/depositions/%s" % d_id,
        params={"access_token": ACCESS_TOKEN},
        data=json.dumps(metadata),
        headers=headers,
    )

    print(r.status_code)
    pprint.pprint(r.json())


# action_upload(sys.argv[1])

if __name__ == "__main__":

    metadata = {
        "metadata": {
            "title": "Test automated upload of Eiger data set",
            "description": """Example data set of cubic insulin recorded on Diamond Light source beamline I04 - being used here as a test upload using the Zenodo REST API. Probably should have things like a deposition ID in here as well as crystallisation condition smiles strings or something.""",
            "creators": [
                {"name": "Winter, Graeme", "affiliation": "Diamond Light Source"}
            ],
            "keywords": ["automated upload"],
        }
    }

    zu = zenodo_uploader(".", metadata)
