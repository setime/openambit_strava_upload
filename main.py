#!/bin/python


import argparse
from pathlib import Path
from typing import List

from src.convert_to_gpx import ConvertToGpx
from src.copy_from_openambit import CopyFromOpenAmbit
from src.upload_to_strava import UploadToStrava


def setup_data_dir(data_dir: Path):
    # Define the subdirectories
    sub_dirs = [
        data_dir.joinpath("assets"),
        data_dir.joinpath("data"),
        data_dir.joinpath("data/gpx"),
        data_dir.joinpath("data/movescount"),
    ]

    # Create the base directory and subdirectories if they do not exist
    for sub_dir in sub_dirs:
        sub_dir.mkdir(parents=True, exist_ok=True)
        # Create a .keep file in each directory
        keep_file = sub_dir.joinpath(".keep")
        keep_file.touch(exist_ok=True)


def checkInputFiles(files: List) -> bool:
    if files is not None:
        for file in files:
            if not Path(file).is_file():
                print(f"File{file} does not exists")
                return False
    return True


def main():
    parser = argparse.ArgumentParser(description="Handle openambit moves.")
    parser.add_argument(
        "-d",
        "--data",
        action="store",
        required=True,
        help="Director where to store the data",
    )
    parser.add_argument(
        "-c",
        "--copy",
        action="store_true",
        help="Copies the files which are downloaded by openambit here",
    )
    parser.add_argument(
        "-g",
        "--gpx",
        action="store_true",
        help="Converts openambit log files to gpx files",
    )
    parser.add_argument(
        "-u",
        "--upload",
        action="store_true",
        help="Uploads files to strava",
    )
    parser.add_argument(
        "-a",
        "--all",
        action="store_true",
        help="Does copy, gpx conversion and uploads to strava",
    )
    parser.add_argument(
        "-f",
        "--files",
        nargs="+",
        action="store",
        help="Files to upload to Strava",
    )

    args = parser.parse_args()

    upload_list = args.files
    if upload_list is None:
        upload_list = []

    # Check if the files which have been specified are valid
    if not checkInputFiles(upload_list):
        exit(-1)

    setup_data_dir(Path(args.data))

    data_dir = Path(args.data).joinpath("data")
    assets_dir = Path(args.data).joinpath("assets")

    copy_form_openambit = CopyFromOpenAmbit()
    convert_to_gpx = ConvertToGpx()
    upload_to_strava = UploadToStrava(data_dir=data_dir, assets_dir=assets_dir)

    if args.copy or args.all:
        copy_form_openambit.copy(data_dir)

    if args.gpx or args.all:
        upload_list = convert_to_gpx.convert(data_dir)

    if args.upload or args.all:
        upload_to_strava.upload(upload_list)


if __name__ == "__main__":
    main()
