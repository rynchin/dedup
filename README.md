## Deduplication Summary

**Datasets**

- WikiText-2-Raw-v1
- CodeSearchNet

---

### Exact Matching

Before deduplication, exact string matches were removed.

After this step:

- **WikiText-2 (1K):** 978 / 1000 files remained
- **CodeSearchNet (1K):** 1000 / 1000 files remained
- **WikiText-2 (10K):** 9,306 / 10,000 files remained
- **CodeSearchNet (10K):** 10,000 / 10,000 files remained

---

### 1K Files

| Metric              | Text | Code |
| :------------------ | :--: | :--: |
| Jaccard Runtime (s) | 12.7 | 3.7  |
| LSH Runtime (s)     | 8.8  | 1.8  |

**Results:**

- Text: Jaccard 930 / 978 vs LSH 930 / 978 (match)
- Code: Jaccard 938 / 1000 vs LSH 938 / 1000 (match)

---

### 10K Files

| Metric              |  Text   | Code  |
| :------------------ | :-----: | :---: |
| Jaccard Runtime (s) | 1,229.9 | 313.1 |
| LSH Runtime (s)     |  123.2  | 33.8  |

**Results:**

- Jaccard 8,381 / 9,306 vs LSH 8,387 / 9,306 (+6)
- Jaccard 8,662 / 10,000 vs LSH 8,662 / 10,000 (match)
