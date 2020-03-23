# zenodo-uploader
Automated Zenodo uploader using REST API

API details - https://developers.zenodo.org/

Requires Zenodo account & access token from
https://zenodo.org/account/settings/applications/tokens/new/

Usage
-----

```
usage: zenodo_uploader.py [-h] [-z ZENODO_ID] [-s] [-m METADATA] [-T TITLE]
                          [-C CREATOR] [-A AFFILIATION] [-K KEYWORD]
                          [-D DESCRIPTION] [-d DIRECTORY] [-x] [-a ARCHIVE]
                          [files [files ...]]

positional arguments:
  files                 individual files

optional arguments:
  -h, --help            show this help message and exit
  -z ZENODO_ID, --zenodo_id ZENODO_ID
                        zenodo upload key
  -s, --sandbox         use sandbox mode
  -m METADATA, --metadata METADATA
                        json metadata file
  -T TITLE, --title TITLE
                        upload title
  -C CREATOR, --creator CREATOR
                        creator name e.g. Public, Joe Q.
  -A AFFILIATION, --affiliation AFFILIATION
                        creator affiliation
  -K KEYWORD, --keyword KEYWORD
                        keyword to associate
  -D DESCRIPTION, --description DESCRIPTION
                        description
  -d DIRECTORY, --directory DIRECTORY
                        directory to upload
  -x, --checksum        compute md5 checksum of uploaded files
  -a ARCHIVE, --archive ARCHIVE
                        pack directory to named archive before upload
```

Options - metadata
- -T - title - allowed exactly once, upload title
- -C - creator, multiple, as "Doe, John R."
- -A - affiliation - either one for all creators or one per creator
- -K - keyword - multiple
- -D - description - long form prose describing the deposition
- -m - metadata file - can pass above as a JSON formatted file

Options - file
- -d - directory - multiple allowed
- -a - archive - (optional) if using -d must be equal number, else if
  using FILES only one - will pack the data into .tar.gz or .zip files
  before uploading
- FILES - list of files to be deposited (if no directories passed)
- -x - check sum (with md5) files before upload to allow comparison
option

Options - zenodo specific
- -z - zenodo upload ID
- -s - sandbox (requires diffent ID, used for development)
