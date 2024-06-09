#!/bin/python

from pathlib import Path
from typing import List

from .openambit2gpx import convert


class ConvertToGpx:

    def _convert(self, movescount_dir: Path, gpx_dir: Path)-> List:
        converted = []
        gpx_dir.mkdir(parents=True, exist_ok=True)

        gpx_files = [file for file in gpx_dir.iterdir() if file.is_file()]
        gpx_files_str = [str(file) for file in gpx_files]

        # Iterate over all files in the source directory
        print(f"Converted files:")
        for source_file in movescount_dir.iterdir():
            if source_file.is_file() and source_file.suffix == ".log":
                if not any(source_file.stem in s for s in gpx_files_str):
                    dist_file = gpx_dir.joinpath(f"{source_file.stem}.gpx")
                    print(f"\t{source_file} -> {dist_file}")
                    convert(source_file, dist_file)
                    converted.append(dist_file)
        return converted
                    
    def convert(self, data_dir: Path):
        movescount_dir = data_dir.joinpath("movescount")
        gpx_dir = data_dir.joinpath("gpx")

        return self._convert(movescount_dir, gpx_dir)
