# Deduplication at Scale

Benchmarking scalable deduplication techniques across text and code datasets.

| Method      | Scale | Text Runtime (s) | Code Runtime (s) | Recall | Speed-up |
| :---------- | :---: | ---------------: | ---------------: | :----: | :------: |
| Jaccard     |  1K   |             12.7 |              3.7 |  100%  |    1×    |
| MinHash–LSH |  10K  |            123.2 |             33.8 | ≈100%  |  10–40×  |
| SimHash–LSH | 100K  |           1452.9 |            447.9 |  >98%  | 80–100×  |

## Methods

- [exact.py](methods/exact.py) — exact duplicate removal via MD5 hashing
- [jaccard.py](methods/jaccard.py) — Jaccard similarity deduplication
- [lsh.py](methods/lsh.py) — MinHash-LSH deduplication
- [simhash.py](methods/simhash.py) — hierarchical SimHash + LSH deduplication

## Results

See [complete breakdown](docs/experiments.md).
