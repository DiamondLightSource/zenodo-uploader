import requests
import os
import sys
import json
import pprint


def get_access_token(mode="production"):
    """get upload key, strip white space."""

    if mode == "production":
        return open(os.path.join(os.environ["HOME"], ".zenodo_id"), "r").read().strip()
    elif mode == "sandbox":
        return open(os.path.join(os.environ["HOME"], ".sandbox_id"), "r").read().strip()


class zenodo_uploader(object):
    """tool to upload files to http://zenodo.org"""

    def __init__(self, directory, metadata, mode="production"):

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
        if mode == "production":
            self._server = "https://zenodo.org"
        elif mode == "sandbox":
            self._server = "https://sandbox.zenodo.org"

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


if __name__ == "__main__":

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

    zu = zenodo_uploader(sys.argv[1], metadata, mode="sandbox")
    zu.upload()
