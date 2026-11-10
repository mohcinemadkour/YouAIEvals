"""Build every combination of dimension values from dimensions.yaml.

Usage:
    python cross_product.py synthetic_data/dimensions.yaml synthetic_data/tuples_all.csv [--sample N] [--seed 0]

With --sample, draws N combinations stratified so every value of every
dimension appears at least once (when N allows), then fills the rest at random.
Requires PyYAML (pip install pyyaml).
"""
import argparse
import csv
import itertools
import random

import yaml


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("dimensions")
    ap.add_argument("out")
    ap.add_argument("--sample", type=int, default=0)
    ap.add_argument("--seed", type=int, default=0)
    args = ap.parse_args()

    with open(args.dimensions) as f:
        spec = yaml.safe_load(f)
    dims = spec["dimensions"]
    names = [d["name"] for d in dims]
    combos = list(itertools.product(*[d["values"] for d in dims]))
    print(f"{len(combos)} combinations across {len(names)} dimensions")

    if args.sample and args.sample < len(combos):
        rng = random.Random(args.seed)
        rng.shuffle(combos)
        chosen, seen = [], set()
        # First pass: cover every (dimension, value) pair at least once.
        for c in combos:
            pairs = set(zip(names, c))
            if not pairs <= seen:
                chosen.append(c)
                seen |= pairs
            if len(chosen) >= args.sample:
                break
        # Second pass: fill the remaining slots at random.
        rest = [c for c in combos if c not in set(chosen)]
        chosen += rest[: max(0, args.sample - len(chosen))]
        combos = chosen
        print(f"sampled {len(combos)}")

    with open(args.out, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(names)
        w.writerows(combos)
    print(f"wrote {args.out}")


if __name__ == "__main__":
    main()
