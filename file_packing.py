import os
import zipfile
import tarfile
import tempfile


def packup_zip(output_filename, files):
    """make a zip file from list of files"""

    with zipfile.ZipFile(output_filename, "w", zipfile.ZIP_DEFLATED) as fout:
        for filename in files:
            fout.write(filename, arcname=os.path.split(filename)[-1])


def packup_tar_gz(output_filename, files):
    """make a gzipped tar file from list of files"""

    with tarfile.open(output_filename, "w:gz") as fout:
        for filename in files:
            fout.write(filename, arcname=os.path.split(filename)[-1])


def packup(archive_name, files):
    """make a temporary archive in new temporary directory named archive_name, 
    containing files in list (with directories removed) format as fmt in 
    (zip, tar.gz)"""

    if archive_name.endswith(".zip"):
        fmt = "zip"
    elif archive_name.endswith(".tar.gz"):
        fmt = "tar.gz"
    else:
        raise ValueError("unknown format %s" % fmt)

    tmpdir = tempfile.mkdtemp()
    archive = os.path.join(tmpdir, archive_name)
    if fmt == "zip":
        packup_zip(archive, files)
    elif fmt == "tar.gz":
        packup_tar_gz(archive, files)

    return archive


if __name__ == "__main__":
    srcdir = os.path.dirname(os.path.abspath(__file__))
    files = [os.path.join(srcdir, f) for f in os.listdir(srcdir) if f.endswith(".py")]
    tmpdir = tempfile.mkdtemp()
    zip_out = os.path.join(tmpdir, "file_packing.zip")
    packup_zip(zip_out, files)
    print(zip_out)
