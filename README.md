# zenodo-uploader
Automated Zenodo uploader using REST API

API details - https://developers.zenodo.org/

Requires Zenodo account & access token from
https://zenodo.org/account/settings/applications/tokens/new/

Usage
-----

```
usage: uploader.py [-h] [-z ZENODO_ID] [-s] [-m METADATA] [-T TITLE]
                   [-C CREATOR] [-A AFFILIATION] [-K KEYWORD] [-D DESCRIPTION]
                   [-d DIRECTORY] [-a ARCHIVE]
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
  -a ARCHIVE, --archive ARCHIVE
  pack directory to named archive before upload
```
