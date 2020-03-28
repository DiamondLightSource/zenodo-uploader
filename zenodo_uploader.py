#!/usr/bin/env dials.python

import argparse
import requests
import os
import sys
import json
import pprint

from file_packing import packup, md5
from metadata import validate_metadata, print_metadata, make_metadata, read_metadata


def get_access_token(sandbox=False):
    """get upload key, strip white space."""

    if sandbox:
        return open(os.path.join(os.environ["HOME"], ".sandbox_id"), "r").read().strip()
    else:
        return open(os.path.join(os.environ["HOME"], ".zenodo_id"), "r").read().strip()


class ZenodoUploader(object):
    """tool to upload files to http://zenodo.org"""

    def __init__(self, file_list, metadata, token, sandbox=False):

        # validate the structure of the metadata - there will be critical
        # items which must be present for this to be a useful deposition

        metadata = {"metadata": metadata}

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
            }
        )

        self._file_list = file_list
        self._metadata = metadata
        self._token = token
        self._dep_id = None
        self._dep_url = None
        if sandbox:
            self._server = "https://sandbox.zenodo.org"
        else:
            self._server = "https://zenodo.org"

    def _create(self):
        """create new empty deposition"""
        r = requests.post(
            "%s/api/deposit/depositions" % self._server,
            params={"access_token": self._token},
            json={},
            headers={"Content-Type": "application/json"},
        )

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

        with open(filename, "rb") as fin:
            r = requests.put(
                "%s/%s" % (self._dep_url, os.path.split(filename)[-1]),
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
        for filename in self._file_list:
            self._upload(filename)
        self._publish()

        # and in the except, delete the partial upload as it is broken
        # - particularly to catch Ctrl-C

    def get_deposition(self):
        return "%s/deposit/%s" % (self._server, self._dep_id)


def uploader():
    """main() - parse args, make Zenodo uploader, execute, catch errors"""

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

    # file related stuff
    parser.add_argument(
        "-d", "--directory", help="directory to upload", action="append"
    )
    parser.add_argument("files", nargs="*", help="individual files")
    parser.add_argument(
        "-x",
        "--checksum",
        help="compute md5 checksum of uploaded files",
        action="store_true",
    )

    # what we are doing with the files
    parser.add_argument(
        "-a",
        "--archive",
        help="pack directory to named archive before upload",
        action="append",
    )
    args = parser.parse_args()

    # validate metadata - allow file read and update from command line
    # (with that priority)
    if args.metadata:
        metadata = read_metadata(args.metadata)
    else:
        metadata = {}

    # pull files or directory (&c.) from metadata file if that is where they are
    if not args.directory and "directory" in metadata:
        args.directory = metadata["directory"]
        del metadata["directory"]

    if not args.files and "files" in metadata:
        args.files = metadata["files"]
        del metadata["files"]

    if not args.archive and "archive" in metadata:
        args.archive = metadata["archive"]
        del metadata["archive"]

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

    # check that we can guess what format to use for archives
    if args.archive:
        for archive in args.archive:
            if not archive.endswith(".zip") and not archive.endswith(".tar.gz"):
                sys.exit("unknown archive type for %s" % archive)

    if not args.zenodo_id:
        args.zenodo_id = get_access_token(sandbox=args.sandbox)

    cl_metadata = make_metadata(
        args.title, args.description, args.creator, args.affiliation, args.keyword
    )

    metadata.update(cl_metadata)
    validate_metadata(metadata)

    # explain what we are going to do
    print("ID: %s" % args.zenodo_id)

    # prepare archives / files for upload
    uploads = []

    if args.archive:
        if args.files:
            uploads.append(packup(args.archive[0], args.files))
        else:
            for archive, directory in zip(args.archive, args.directory):
                files = [
                    os.path.join(directory, filename)
                    for filename in os.listdir(directory)
                    if os.path.isfile(os.path.join(directory, filename))
                ]
                uploads.append(packup(archive, files))

    elif args.directory:
        for directory in args.directory:
            uploads.extend(
                [
                    os.path.join(directory, filename)
                    for filename in os.listdir(directory)
                    if os.path.isfile(os.path.join(directory, filename))
                ]
            )
    else:
        uploads.extend(args.files)

    # metadata
    print_metadata(metadata)

    # files
    print("Upload consists of:")
    for upload in uploads:
        print(upload)
        if args.checksum:
            print("md5:%s" % md5(upload))

    # make and act on
    zenodo_uploader = ZenodoUploader(uploads, metadata, args.zenodo_id, args.sandbox)
    zenodo_uploader.upload()
    print("Upload complete for deposition %s" % str(zenodo_uploader.get_deposition()))


if __name__ == "__main__":
    uploader()
