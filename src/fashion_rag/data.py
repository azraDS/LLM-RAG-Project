"""Reading and writing the JSON-lines product files."""
import json
from pathlib import Path

import pandas as pd


def read_jsonl(path: Path) -> list[dict]:
    with open(path, "r") as f:
        return [json.loads(line) for line in f]


def write_jsonl(path: Path, rows: list[dict]) -> None:
    with open(path, "w") as f:
        for row in rows:
            f.write(json.dumps(row) + "\n")


def load_dataframe(path: Path) -> pd.DataFrame:
    return pd.DataFrame(read_jsonl(path))
