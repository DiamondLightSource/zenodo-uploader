#!/usr/bin/env dials.python

import argparse
import requests
import os
import sys
import json
import pprint
import urllib

from metadata import make_metadata, read_metadata


def get_access_token(sandbox=False):
    """get upload key, strip white space."""

    if sandbox:
        return open(os.path.join(os.environ["HOME"], ".sandbox_id"), "r").read().strip()
    else:
        return open(os.path.join(os.environ["HOME"], ".zenodo_id"), "r").read().strip()


class ZenodoUpdater(object):
    """tool to upload files to http://zenodo.org"""

    def __init__(self, metadata, token, sandbox=False):

        self._metadata = metadata
        self._token = token
        self._dep_id = None
        self._dep_url = None
        self._dep_metadata = None
        if sandbox:
            self._server = "https://sandbox.zenodo.org"
        else:
            self._server = "https://zenodo.org"

    def _find(self):
        """find this deposition"""

        title = self._metadata["title"]

        r = requests.get(
            '%s/api/records/?page=1&size=2&q=title:"%s"'
            % (self._server, urllib.parse.quote(title))
        )

        if not r.status_code in (200, 201, 202):
            pprint.pprint(r.json())
            raise RuntimeError("in find: HTTP status %d" % r.status_code)

        response = r.json()["hits"]

        if not response["total"] == 1:
            raise RuntimeError("%d results found for %s" % (response["total"], title))
        result = response["hits"][0]

        self._dep_id = result["id"]
        self._dep_url = "%s/api/deposit/depositions/%d" % (self._server, result["id"])
        self._dep_metadata = result["metadata"]

        print("Located deposition: id = %d" % self._dep_id)

    def _update(self):
        """push the metadata for this deposition"""

        # first merge update metadata with existing metadata - will
        # overwrite existing values where updates exist

        metadata = self._dep_metadata
        metadata.update(self._metadata)

        # delete useless things
        for k in (
            "access_right",
            "access_right_category",
            "communities",
            "doi",
            "license",
            "publication_date",
            "related_identifiers",
            "relations",
            "resource_type",
        ):
            del metadata[k]

        metadata = {"metadata": metadata}
        metadata["metadata"].update({"access_right": "open", "upload_type": "dataset"})

        r = requests.put(
            "%s/api/deposit/depositions/%s" % (self._server, self._dep_id),
            params={"access_token": self._token},
            data=json.dumps(metadata),
            headers={"Content-Type": "application/json"},
        )

        if not r.status_code in (200, 201, 202):
            pprint.pprint(r.json())
            raise RuntimeError("in update: HTTP status %d" % r.status_code)

        print("Uploaded metadata for: %s" % (self._metadata["title"]))

    def _publish(self):
        """complete the deposition process"""

        r = requests.post(
            "%s/api/deposit/depositions/%s/actions/publish"
            % (self._server, self._dep_id),
            params={"access_token": self._token},
        )
        if not r.status_code in (200, 201, 202):
            pprint.pprint(r.json())
            raise RuntimeError("in publish: HTTP status %d" % r.status_code)

        # FIXME grab the DOI from here

        print("Update published")

    def update(self):
        """process metadata for update"""

        # FIXME wrap this in a try except

        self._find()
        self._update()
        self._publish()

        # and in the except, delete the partial upload as it is broken
        # - particularly to catch Ctrl-C

    def get_deposition(self):
        return "%s/deposit/%s" % (self._server, self._dep_id)


def updater():
    """main() - parse args, make Zenodo updater, execute, catch errors"""

    parser = argparse.ArgumentParser()

    # zenodo / administrative matters
    parser.add_argument("-z", "--zenodo_id", help="zenodo upload key")
    parser.add_argument("-s", "--sandbox", help="use sandbox mode", action="store_true")

    # upload metadata - title, authors, keywords, description, metafile
    parser.add_argument("-m", "--metadata", help="json metadata file")
    parser.add_argument("-T", "--title", help="upload title")
    parser.add_argument(
        "-C", "--creator", help="creator name e.g. Public, Joe Q.", action="append"
    )
    parser.add_argument(
        "-A", "--affiliation", help="creator affiliation", action="append"
    )
    parser.add_argument("-K", "--keyword", help="keyword to associate", action="append")
    parser.add_argument("-D", "--description", help="description")
    args = parser.parse_args()

    # validate metadata - allow file read and update from command line
    # (with that priority)
    if args.metadata:
        metadata = read_metadata(args.metadata)
    else:
        metadata = {}

    if "directory" in metadata:
        del metadata["directory"]

    if "files" in metadata:
        del metadata["files"]

    if "archive" in metadata:
        del metadata["archive"]

    if not args.zenodo_id:
        args.zenodo_id = get_access_token(sandbox=args.sandbox)

    cl_metadata = make_metadata(
        args.title, args.description, args.creator, args.affiliation, args.keyword
    )

    metadata.update(cl_metadata)

    # explain what we are going to do
    print("ID: %s" % args.zenodo_id)

    import pprint

    pprint.pprint(metadata)

    # make and act on
    zenodo_updater = ZenodoUpdater(metadata, args.zenodo_id, args.sandbox)
    zenodo_updater.update()
    print("Update complete for deposition %s" % str(zenodo_updater.get_deposition()))


if __name__ == "__main__":
    updater()
