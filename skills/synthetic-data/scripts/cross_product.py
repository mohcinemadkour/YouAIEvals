"""Build every combination of dimension values from dimensions.json.

Usage:
    python cross_product.py synthetic_data/dimensions.json synthetic_data/tuples_generated.json [--sample N] [--seed 0]

Writes a JSON list of tuples in the review app's format
({"id", "values", "source": "cross-product", "status": "pending"}).
With --sample, draws N combinations so that every value of every dimension
appears at least once (when N allows), then fills the rest at random.
Standard library only. Filter invalid combinations afterwards, then merge
the survivors into tuples.json (keep the existing tuples and their reviews).
"""
import argparse
import itertools
import json
import random


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("dimensions")
    ap.add_argument("out")
    ap.add_argument("--sample", type=int, default=0)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--id-prefix", default="g")
    args = ap.parse_args()

    with open(args.dimensions) as f:
        dims = json.load(f)["dimensions"]
    names = [d["name"] for d in dims]
    combos = list(itertools.product(*[d["values"] for d in dims]))
    print(f"{len(combos)} combinations across {len(names)} dimensions")

    if args.sample and args.sample < len(combos):
        rng = random.Random(args.seed)
        rng.shuffle(combos)
        chosen, seen = [], set()
        for c in combos:  # first pass: cover every (dimension, value) pair
            pairs = set(zip(names, c))
            if not pairs <= seen:
                chosen.append(c)
                seen |= pairs
            if len(chosen) >= args.sample:
                break
        picked = set(chosen)
        chosen += [c for c in combos if c not in picked][: max(0, args.sample - len(chosen))]
        combos = chosen
        print(f"sampled {len(combos)}")

    tuples = [{"id": f"{args.id_prefix}{i:03d}", "values": dict(zip(names, c)),
               "source": "cross-product", "status": "pending"} for i, c in enumerate(combos, 1)]
    with open(args.out, "w") as f:
        json.dump(tuples, f, indent=2, ensure_ascii=False)
    print(f"wrote {args.out}")


if __name__ == "__main__":
    main()
