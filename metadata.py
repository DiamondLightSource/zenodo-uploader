import json


def validate_metadata(metadata):
    valid = set(("title", "description", "creators", "keywords"))
    names = set(metadata)

    if names - valid:
        raise ValueError("unknown metadata keys: %s" % (" ".join(names - valid)))
    if valid - names:
        raise ValueError("missing metadata keys: %s" % (" ".join(valid - names)))


def print_metadata(metadata):
    print("Title: %s" % metadata["title"])
    print("Creators:")
    for creator in metadata["creators"]:
        print("%s (%s)" % (creator["name"], creator["affiliation"]))
    print("Description:")
    print(metadata["description"])
    print("Keywords: %s" % (", ".join(metadata["keywords"])))


def make_metadata(title, description, creators, affiliations, keywords):
    if affiliations is None:
        affiliations = []
    if creators is None:
        creators = []
    if not len(affiliations) in (1, len(creators)):
        raise ValueError("ill-defined affiliations")
    metadata = {"title": title, "description": description, "keywords": keywords}
    if len(affiliations) == 1:
        affiliations *= len(creators)
    metadata["creators"] = [
        {"name": creator, "affiliation": affiliation}
        for creator, affiliation in zip(creators, affiliations)
    ]
    for key in ("title", "description", "keywords", "creators"):
        if not metadata[key]:
            del (metadata[key])
    return metadata


def read_metadata(metadata_file):
    with open(metadata_file, "r") as f:
        metadata = json.load(f)
    return metadata


if __name__ == "__main__":
    metadata_str = """{"title": "This is the title", "description": "This is the description. It can be long. It probably has multiple lines.", "creators": [{"name": "Winter, Graeme", "affiliation": "Diamond Light Source"}], "keywords": ["automated upload tool"]}"""

    metadata = json.loads(metadata_str)
    validate(metadata)
    print_metadata(metadata)
