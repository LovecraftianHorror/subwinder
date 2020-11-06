#!/usr/bin/env python
import argparse
import json
from pathlib import Path
from typing import List


def _main() -> None:
    args = _parse_args()
    fake_media(args.entry_file, args.output_dir, args.entry)


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-e",
        "--entry",
        action="append",
        help="[Default: all] Then entry index to generate a media for",
        # Empty list is the magic value for all entries
        default=[],
    )
    parser.add_argument(
        "-o",
        "--output-dir",
        type=Path,
        help="[Default: current directory] Directory to store generated media in",
        default=Path.cwd(),
    )
    parser.add_argument("entry_file", type=Path, help="Location of the entry file")

    args = parser.parse_args()

    # Make sure all entries are ints
    for i in range(len(args.entry)):
        try:
            args.entry[i] = int(args.entry[i])
        except ValueError:
            raise ValueError(f'Entry should be an int, got "{args.entry[i]}"')

    return args


# TODO: take Path or str?
# TODO: test that the hashes are right in unit testing
def fake_media(entry_file: Path, output_dir: Path, entry_indicies: List[int] = []):
    HASH_SIZE = 8
    MAX_HASH = 2 ** (HASH_SIZE * 8) - 1
    MIN_FILE_SIZE = 128 * 1024

    # Attempt to read the entry file
    with entry_file.open() as f:
        entries = json.load(f)

    # Empty `entry_indicies` means all entries
    if len(entry_indicies) == 0:
        entry_indicies = list(range(len(entries)))

    for index in entry_indicies:
        # Make sure all entries are within bounds
        if index >= len(entries) or index < 0:
            raise ValueError(
                f"Entry {index} extends outside entries' bounds (0, {len(entries) - 1})"
            )

    # Generate the fake media for each of the entries
    output_paths = []
    for entry_index in entry_indicies:
        entry = entries[entry_index]
        output_file = output_dir / entry["name"]
        hash = int(entry["hash"], 16)
        size = entry["size"]

        if size < MIN_FILE_SIZE:
            raise ValueError(
                f"Desired file is below minimum filesize of {MIN_FILE_SIZE} bytes"
            )

        # Determine the value for the first 8 bytes that will fake the desired hash
        if size > hash:
            contents = MAX_HASH - size + hash
        else:
            contents = hash - size

        with output_file.open("wb") as file:
            file.write(contents.to_bytes(HASH_SIZE, byteorder="little"))
            # Use truncate to set the remaining file size. On file systems that support
            # it this will create a sparse file which takes less space on disk
            # Note: even if the filesystem supports sparse files, copying or moving
            #       the file may not keep it as a sparse file if the program used is not
            #       aware
            file.truncate(size)

        output_paths.append(output_file)

    # Return the paths to all the dummy files
    return output_paths


if __name__ == "__main__":
    _main()
