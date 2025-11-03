# Deduplication at Scale

Benchmarking scalable deduplication techniques across text and code datasets.

**Environment:** Single-machine CPU demo for pretraining data hygiene.

| Method      | Scale | Text Runtime (s) | Code Runtime (s) | Agreement vs Baseline | Speed-up |
| :---------- | :---: | ---------------: | ---------------: | :-------------------: | :------: |
| Jaccard     |  1K   |             12.7 |              3.7 |         100%          |    1×    |
| MinHash–LSH |  10K  |            123.2 |             33.8 |         ≈100%         |  10–40×  |
| SimHash–LSH | 100K  |           1452.9 |            447.9 |         >98%          | 80–100×  |

Baseline = exact Jaccard at 1K/10K, plain LSH at 100K.

**Configs**

- Preprocessing: exact MD5 dedup.
- Shingles: Text=char-4; Code=token-5.
- Thresholds (Jaccard): Text τ=0.30; Code τ=0.45.
- MinHash–LSH: Text k=336, r=3 rows/band (bands=112); Code k=192, r=3 (bands=64).
- Hierarchical: SimHash 64-bit, t=7 → LSH → exact Jaccard.
- Metrics: 1K/10K = agreement vs exact Jaccard; 100K = agreement vs plain LSH.

## Methods

- [exact.py](methods/exact.py) — exact duplicate removal via MD5 hashing
- [jaccard.py](methods/jaccard.py) — Jaccard similarity deduplication
- [lsh.py](methods/lsh.py) — MinHash-LSH deduplication
- [simhash.py](methods/simhash.py) — hierarchical SimHash + LSH deduplication

## Setup

Environment:

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

Build data:

```bash
python dataset.py
```

Exact dedup:

```bash
python methods/exact.py
```

Evaluate:

```bash
python evals.py
```

## Results

See [complete breakdown](docs/experiments.md).
