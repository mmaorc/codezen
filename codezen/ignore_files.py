from pathlib import Path
from typing import List, Optional

import pathspec


def load_ignore_file(path: Path) -> Optional[pathspec.PathSpec]:
    try:
        with open(path, "r") as file:
            lines = file.read().splitlines()
            spec = pathspec.GitIgnoreSpec.from_lines(lines)
            return spec
    except FileNotFoundError:
        return None


def filter_files(files: list[Path], ignore_patterns: pathspec.PathSpec) -> List[Path]:
    matched_files = set(ignore_patterns.match_files(files))
    return [file for file in files if file not in matched_files]
