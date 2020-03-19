import requests
import os
import sys
import json
import pprint


def action_upload(directory):
    # get upload key from somewhere

    ACCESS_TOKEN = (
        open(os.path.join(os.environ["HOME"], ".zenodo_id"), "r").read().strip()
    )

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

    # list the upload directory / file list for files to upload
    for filename in os.listdir(directory):
        print(filename)
        data = {"name": filename}
        files = {"file": open(os.path.join(directory, filename), "rb")}
        r = requests.post(
            "https://zenodo.org/api/deposit/depositions/%s/files" % d_id,
            params={"access_token": ACCESS_TOKEN},
            data=data,
            files=files,
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


action_upload(sys.argv[1])
