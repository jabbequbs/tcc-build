#! python3

import argparse
import os
import pathlib
import sys
import tarfile
import zipfile

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("archive")
    parser.add_argument("destination")
    args = parser.parse_args()

    if args.archive.lower().endswith(".zip"):
        zArchive = zipfile.ZipFile(args.archive)
        members = [m.filename for m in zArchive.infolist() if not m.is_dir()]
    elif args.archive.lower().endswith(".tar.gz") or args.archive.lower().endswith(".tar.bz2"):
        zArchive = tarfile.open(args.archive)
        members = [m.name for m in zArchive.getmembers() if m.isfile()]
    else:
        sys.exit("Unknown archive type")

    for filename in members:
        if filename[0] in ("/", "\\") or ".." in filename:
            raise Exception(f"Dangerous filename: {filename}")
    zArchive.extractall(args.destination)

    # raise archive members to a common parent
    dest = pathlib.Path(args.destination)
    while True:
        children = list(dest.iterdir())
        if len(children) == 1 and children[0].is_dir():
            parent = children[0].rename(dest / "_")
            for child in parent.iterdir():
                child.rename(dest / child.name)
            parent.rmdir()
        else:
            break

if __name__ == '__main__':
    main()
