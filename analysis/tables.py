from __future__ import annotations

import math

import pandas as pd

SOURCE_LABEL = {
    "live": "AWS measurement",
    "moto": "moto functional check - NOT an AWS measurement (capacity and latency are not AWS numbers)",
    "local": "local run - NOT an AWS measurement",
}


# Long label that says where the data came from
def source_label(source: str | None) -> str:
    return SOURCE_LABEL.get(source or "", f"{source} - NOT an AWS measurement")


# Render a cell
def fmt(v, digits: int = 4) -> str:
    if v is None:
        return "**N/A**"
    try:
        missing = math.isnan(v)
    except TypeError:
        missing = False
    if missing:
        return "**N/A**"
    if isinstance(v, float):
        return f"{v:.{digits}g}"
    return str(v)


# Render a data frame as a Markdown table
def md_table(df: pd.DataFrame, digits: int = 4) -> str:
    cols = [str(c) for c in df.columns]
    lines = ["| " + " | ".join(cols) + " |", "|" + "---|" * len(cols)]
    for row in df.itertuples(index=False):
        lines.append("| " + " | ".join(fmt(v, digits) for v in row) + " |")
    return "\n".join(lines)
