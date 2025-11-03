import hashlib
import json
from pathlib import Path

def md5(path):
    """Return the md5 hash of the file"""
    return hashlib.md5(Path(path).read_bytes()).hexdigest()

def exact_match(indir, outdir, length=None):
    """
    Remove exact duplicates from input directory, saves in output directory
    """
    indir, outdir = Path(indir), Path(outdir)
    outdir.mkdir(parents=True, exist_ok=True)
    
    seen = set()
    kept = []
    
    all_files = sorted(list(indir.glob("*.txt")))
    if length:
        all_files = all_files[:length]
    
    for path in all_files:
        md5_hash = md5(path)
        if md5_hash in seen:
            print(f"Duplicate found: {path.name}")
            continue
        seen.add(md5_hash)
        kept.append(path)
    
    print(f"{len(kept)} unique files out of {len(all_files)} total files")

    for path in kept:
        (outdir / path.name).write_text(path.read_text())

if __name__ == "__main__":
    exact_match(indir="data/init/wiki", outdir="data/exact/wiki")
    exact_match(indir="data/init/code", outdir="data/exact/code")