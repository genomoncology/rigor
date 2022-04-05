from collections import defaultdict
from pathlib import Path
from typing import Tuple, List, Dict

from . import get_logger, glob_paths, utils


def do_reformat(suite):
    for file_path in glob_paths(suite):
        process_reformat(file_path)


def process_reformat(file_path: str):
    logger = get_logger()
    logger.debug("Checking File", file_path=file_path)

    file_path = Path(file_path)
    assert file_path.exists(), f"File not found: {file_path}"

    file_obj = file_path.open("r")

    all_lines = []
    curr_table = []
    cleaned = 0
    for line in file_obj:
        text = line.strip()
        if text.startswith("|") and text.endswith("|"):
            curr_table.append(line)
        else:
            (this_cleaned, was_cleaned) = clean_table(curr_table)
            cleaned += int(was_cleaned)
            curr_table = []
            all_lines += this_cleaned
            all_lines.append(line)

    if cleaned:
        logger.info("Cleaned Tables", file_path=file_path, cleaned=cleaned)
        file_obj.close()
        file_obj = file_path.open("w")
        file_obj.writelines(all_lines)
        file_obj.close()

    else:
        logger.info("No Tables Cleaned", file_path=file_path)


def to_line(values: List[str], widths: Dict[int, int], indent: str) -> str:
    texts = []
    for idx, value in enumerate(values):
        value = "" if value is None else value
        right_padded = value.ljust(widths[idx])
        texts.append(right_padded)

    center = " | ".join(texts)
    return f"{indent}| {center} |\n"


def clean_table(curr_table: List[str]) -> Tuple[List[str], bool]:
    if len(curr_table) <= 1:
        return curr_table, False

    orig_text = "".join(curr_table)
    indent = (orig_text.index("|")) * " "

    header, rows = utils.parse_into_header_rows(orig_text, keep_escapes=True)
    widths = defaultdict(int)
    for row in [header] + rows:
        for idx, item in enumerate(row):
            widths[idx] = max(widths[idx], len(item or ""))

    new_table = [to_line(header, widths, indent)]
    for row in rows:
        new_table.append(to_line(row, widths, indent))

    was_cleaned = new_table != curr_table
    return new_table, was_cleaned
