"""
Oliver 2024
"""
import os.path
import re
from typing import List, Dict, Any, Tuple
import csv


def AND(*params) -> str:
    clause = " AND ".join(params)
    return clause


def OR(*params) -> str:
    clause = " OR ".join(params)
    return clause


def BETWEEN(a, b, c) -> str:
    clause = f"{a} BETWEEN {b} AND {c}"
    return clause


def process_dict(d: Dict[Any, Any] | None) -> Tuple[List[Any], List[Any]]:
    """
    dictionary helper that splits the key and values into lists
    :param d: a dictionary
    :return: tuple of key list and values list
    """
    if not d:
        return [], []
    keys = list(d.keys())
    vals = list(d.values())
    return keys, vals


def is_int(x: Any):
    return re.match(r"^[0-9]+$", str(x)) is not None


def is_real(x: Any):
    return re.match(r"^[0-9]+\.[0-9]+$", str(x)) is not None


def detect_type_csv(data) -> str:
    if is_int(data):
        return "integer"
    elif is_real(data):
        return "real"
    elif isinstance(data, bytes):
        return "blob"
    else:
        return "text"


def detect_type_json(data) -> str:
    if isinstance(data, int):
        return "integer"
    elif isinstance(data, float):
        return "real"
    elif isinstance(data, bytes):
        return "blob"
    else:
        return "text"


def extract_filename(fpath) -> str:
    return os.path.splitext(os.path.basename(fpath))[0]


def read_csv(filepath: str) -> Tuple[List[str], List[str]]:
    """

    :param filepath:
    :return:
    """
    with open(filepath, "r", encoding="utf-8", errors="replace") as csv_file:
        reader = csv.reader(csv_file, delimiter=',')
        headers = next(reader)
        rows = [x for x in reader]
        return headers, rows


def safe_name(text: str) -> str:
    return text.replace('-', '_').replace(' ', '_')
