#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
URL = "https://openml.org/data/v1/download/1673544/creditcard.arff"
MD5 = "178bcf9bb1f31a3dfe12d0e577884add"
OUT = ROOT / "data/workload/amounts_cents.txt"
HEADER = [
    "# Amount column of OpenML dataset 1597 'creditcard', in integer cents, file order, no row excluded.",
    f"# Source: {URL} (MD5 {MD5}).",
    "# Dataset by the Machine Learning Group, ULB, and Worldline. Licence: Open Database License (ODbL) v1.0;",
    "# contents: Database Contents License (DbCL) v1.0. This extract is offered under the same licence.",
    "# Written by scripts/fetch_amounts.py.",
]


# Read the Amount column of an ARFF file as integer cents
def amounts_cents(lines) -> list[int]:
    attrs, out, data = [], [], False
    for line in lines:
        s = line.strip()
        if not s or s.startswith("%"):
            continue
        if not data:
            if s.lower().startswith("@attribute"):
                attrs.append(s.split()[1].strip("'\""))
            elif s.lower() == "@data":
                data, col = True, attrs.index("Amount")
            continue
        out.append(round(float(s.split(",")[col]) * 100))
    return out


# Download or read the dataset, check its MD5 and write the amounts file
def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--arff", help="local copy of creditcard.arff (default: download)")
    args = ap.parse_args(argv)
    raw = Path(args.arff).read_bytes() if args.arff else urllib.request.urlopen(URL).read()
    if hashlib.md5(raw).hexdigest() != MD5:
        raise SystemExit("MD5 mismatch: not the OpenML 1597 file")
    cents = amounts_cents(raw.decode("utf-8").splitlines())
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text("\n".join(HEADER + [str(c) for c in cents]) + "\n")
    print(f"{len(cents)} amounts -> {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
