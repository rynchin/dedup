from pathlib import Path
from datasets import load_dataset
import random

# seed
seed = 42
random.seed(seed)

def build_wiki(out_root="data", n=200):
    ds = load_dataset("Salesforce/wikitext", "wikitext-103-v1", split="train")
    wiki_samples = [x["text"] for x in random.sample([r for r in ds if len(r["text"].strip()) > 0], n)]

    file_path = Path(out_root) / "wiki"
    write_txts(wiki_samples, file_path, "wiki")

def build_code(out_root="data", n=200):
    ds = load_dataset("Nan-Do/code-search-net-python", split="train")
    code_samples = [x["code"] for x in random.sample([r for r in ds if len(r["code"].strip()) > 0], n)]

    file_path = Path(out_root) / "code"
    write_txts(code_samples, file_path, "code")

def write_txts(items, outdir, prefix):
    outdir = Path(outdir)
    outdir.mkdir(parents=True, exist_ok=True)
    for i, item in enumerate(items):
        (outdir / f"{prefix}_{i:05d}.txt").write_text(item)
    
if __name__ == "__main__":
    build_wiki(out_root="data/init", n=100000)
    build_code(out_root="data/init", n=100000)