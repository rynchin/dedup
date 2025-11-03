from pathlib import Path
import re, unicodedata
import keyword, tokenize
import io
import hashlib
import random
from collections import defaultdict

from methods.jaccard import (
    normalize_text, normalize_code,
    tokenize_text, tokenize_code,
    ngram_char_shingling, ngram_token_shingling,
    jaccard
)
from methods.lsh import hash64, encode_shingle, MinHash, LSH

def hamming_distance(a, b):
    return bin(a ^ b).bit_count()

class SimHash:
    def __init__(self, bits=64):
        assert bits == 64
        self.bits = bits
        
    def signature_from_iter(self, it):
        acc = [0] * self.bits
        for shingle in it:
            h = hash64(encode_shingle(shingle))
            for i in range(self.bits): # bitwise voting
                acc[i] += 1 if ((h >> i) & 1) else -1

        out = 0
        for i in range(self.bits):
            if acc[i] >= 0: # positive vote
                out |= (1 << i)
        return out

def split_blocks(code, num_blocks, bits):
    """Split code into num_blocks blocks, remainder for earlier blocks"""
    assert 0 < num_blocks <= bits
    val = bits // num_blocks
    rem = bits % num_blocks
    vals = [0] * num_blocks
    shift = 0
    for i in range(num_blocks):
        w = val + (1 if i < rem else 0) # length of block
        mask = ((1 << w) - 1) << shift
        vals[i] = (code & mask) >> shift # get value
        shift += w
    return vals

class SimHashBlock:
    """
    Filters for similar blocks in SimHash signatures

    Hamming threshold = t -> num_blocks = t + 1, so distance <= t means at least one block is the same
    """ 
    def __init__(self, t):
        assert 0 <= t < 64
        self.t = t
        self.num_blocks = t + 1
        
        # table per block
        self.tables = [defaultdict(list) for _ in range(self.num_blocks)]
        
        # block widths
        val = 64 // self.num_blocks
        rem = 64 % self.num_blocks
        self.block_widths = [val + (1 if i < rem else 0) for i in range(self.num_blocks)]

    def _blocks(self, code):
        return split_blocks(code, self.num_blocks, 64)

    def add(self, doc_id, code):
        blocks = self._blocks(code)
        for idx, block in enumerate(blocks): # add to each block table
            self.tables[idx][block].append(doc_id)
    
    def candidates(self, code):
        out = set()
        blocks = self._blocks(code)
        for idx, block in enumerate(blocks):
            for doc_id in self.tables[idx].get(block, []):
                out.add(doc_id)
        return out

def dedup_sim(indir, outdir, n=10, type="text", tau=0.5, t=3, k=128, r=4, seed=42, length=None):
    """
    Hierarchical SimHash + MinHash/LSH.
     - Build SimHash and MinHash signatures for each file
     - Gate with SimHash blocks (m=t+1), intersect with LSH candidates
    """
    indir, outdir = Path(indir), Path(outdir)
    outdir.mkdir(parents=True, exist_ok=True)

    norm_data = normalize_text if type == "text" else normalize_code
    
    simhash = SimHash(bits=64)
    blocks = SimHashBlock(t=t)

    minhash = MinHash(k=k, seed=seed)
    lsh = LSH(k=k, r=r)
    

    files = sorted(indir.glob("*.txt"), key=lambda x: x.stat().st_size, reverse=True) # largest files first
    if length:
        files = files[:length]
    
    kept_paths = []
    kept_shingles = []

    total_sim_candidates = 0 # candidates from SimHash blocks
    total_candidates = 0 # candidates from LSH
    total_pairs = 0 # exact Jaccard checks
    
    for path in files:
        text = path.read_text()
        text = norm_data(text)
        tokens = tokenize_text(text) if type == "text" else tokenize_code(text)
        sh = ngram_char_shingling(text, n) if type == "text" else ngram_token_shingling(tokens, n)
        
        # SimHash
        code = simhash.signature_from_iter(sh)
        sim_cands = blocks.candidates(code)
        total_sim_candidates += len(sim_cands)
        
        # MinHash
        sig = minhash.signature_from_iter(sh)
        lsh_cands = lsh.candidates(sig)
        
        # Take intersection
        candidates = sim_cands & lsh_cands
        total_candidates += len(candidates)
        
        keep = True
        if candidates:
            for cand_idx in candidates:
                total_pairs += 1
                if jaccard(sh, kept_shingles[cand_idx]) >= tau:
                    keep = False
                    break
        
        if keep:
            blocks.add(len(kept_paths), code) # add code to SimHash blocks
            lsh.add(len(kept_paths), sig) # add signature to LSH
            kept_shingles.append(sh)
            kept_paths.append(path)
        else:
            #print(f"Duplicate found: {path.name}")
            continue
    
    print(f"{len(kept_paths)} unique files out of {len(files)} total files")
    print(f"SimHash candidates: {total_sim_candidates}")
    print(f"Total candidates (intersection): {total_candidates}, Total pairs checked: {total_pairs}")
    
    for path in kept_paths:
        (outdir / path.name).write_text(path.read_text())
    
    return {
        "unique_count": len(kept_paths),
        "total_files": len(files),
        "simhash_candidates": total_sim_candidates,
        "candidates": total_candidates,
        "pairs_checked": total_pairs
    }
    
if __name__ == "__main__":
    dedup_sim(indir="data/exact/wiki", outdir="data/simhash/wiki", n=4, type="text", tau=0.30, t=7, k=336, r=3, length = 1000)
    dedup_sim(indir="data/exact/code", outdir="data/simhash/code", n=5, type="code", tau=0.45, t=7, k=192, r=3, length = 1000)