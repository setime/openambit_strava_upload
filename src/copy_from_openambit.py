import os
import shutil
from pathlib import Path


class CopyFromOpenAmbit:

    def _copy_files(self, src: Path, dst: Path):
        dst.mkdir(parents=True, exist_ok=True)

        # Iterate over all files in the source directory
        for source_file in src.iterdir():
            if source_file.is_file() and source_file.suffix == ".log":
                destination_file = dst.joinpath(source_file.name)
                shutil.copy(source_file, destination_file)

    def copy(self, data_dir:Path):
        src = Path.home().joinpath(".openambit")
        dst = data_dir.joinpath("movescount")
        print(f"Copy files\n\tfrom:\t{src}\n\tto:\t{dst}")
        self._copy_files(src, dst)
