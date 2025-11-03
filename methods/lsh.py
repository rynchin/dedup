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

MAX64 = 2**64 - 1

def hash64(data): # bytes ->64 bit integer hash
    return int.from_bytes(hashlib.blake2b(data, digest_size=8).digest(), "big", signed=False)

def encode_shingle(x):
    """Add length prefix to shingle"""
    if isinstance(x, tuple): # code
        encode = []
        for token in x:
            b = token.encode("utf-8") # byte
            encode.append(str(len(b)).encode('ascii') + b':' + b)
        return b'|'.join(encode)
    return x.encode("utf-8")

def stream_char(text, k):
    for i in range(max(0, len(text) - k + 1)):
        yield text[i:i+k]

def stream_token(tokens, n):
    for i in range(max(0, len(tokens) - n + 1)):
        yield tuple(tokens[i:i+n])

# ------------------------------------------------------------ #
# Classes
# ------------------------------------------------------------ #

class MinHash:
    """
    Approximate Jaccard using MinHash
    Simulate k random permutations:
     - h_i(x) = Hash(seed_i || encode_shingle(x))
    """
    def __init__(self, k=128, seed=42):
        self.k = k # num of hash functions
        rand = random.Random(seed)
        #self.hashes = [rand.getrandbits(64).to_bytes(8, 'big') for _ in range(k)]
        self.a = [rand.getrandbits(64) | 1 for _ in range(k)] # coprime to MAX64
        self.b = [rand.getrandbits(64) for _ in range(k)]
    
    def signature_from_iter(self, it):
        """
        Keep min hash value across hashes for each document
        """
        signatures = [MAX64] * self.k # store min hash val
        a, b = self.a, self.b
        for shingle in it:
            x = hash64(encode_shingle(shingle)) # one Black2b per shingle
            for idx in range(self.k):
                h = (a[idx] * x + b[idx]) & MAX64
                if h < signatures[idx]:
                    signatures[idx] = h
        return tuple(signatures)

class LSH:
    """
    Divide data into b bands of r rows
     - Band match iff all rows match, prob = J^r
     - Candidate prob -> 1 - (1 - J^r)^b
    """
    def __init__(self, k=128, r=4):
        assert k % r == 0
        self.k = k
        self.r = r
        self.bands = [(i, i+r) for i in range(0, k, r)]
        self.tables = [defaultdict(list) for _ in self.bands]
        
    
    def band_hash(self, signature, start, end):
        """Hash band of signature given range"""
        band_bytes = b','.join(int(signature[i]).to_bytes(8, 'big') for i in range(start, end))
        return hash64(band_bytes)
    
    def candidates(self, signatures):
        """For each band, gather documents that share at least one band hash"""
        out = set()
        for (start, end), table in zip(self.bands, self.tables):
            band_hash = self.band_hash(signatures, start, end)
            for doc_id in table.get(band_hash, []):
                out.add(doc_id)
        return out

    def add(self, doc_id, signature):
        """Add document to table for each band"""
        for (start, end), table in zip(self.bands, self.tables):
            band_hash = self.band_hash(signature, start, end)
            table[band_hash].append(doc_id)

# ------------------------------------------------------------ #       
# Dedup 
# ------------------------------------------------------------ #

def dedup_lsh(indir, outdir, n=10, type="text", tau=0.5, k=128, r=4, seed=42, length=None):
    """
    LSH-MinHash dedup
     - Build MinHash signature for each file
     - Generate candidates (prob = 1 - (1-s^r)^b)
    """
    indir, outdir = Path(indir), Path(outdir)
    outdir.mkdir(parents=True, exist_ok=True)


    norm_data = normalize_text if type == "text" else normalize_code
    
    minhash = MinHash(k=k, seed=seed)
    lsh = LSH(k=k, r=r)

    files = sorted(indir.glob("*.txt"), key=lambda x: x.stat().st_size, reverse=True) # largest files first
    if length:
        files = files[:length]
    
    kept_paths = []
    kept_shingles = []
    total_candidates = 0
    total_pairs = 0

    for path in files: 
        text = path.read_text()
        text = norm_data(text)
        tokens = tokenize_text(text) if type == "text" else tokenize_code(text)
        sh = ngram_char_shingling(text, n) if type == "text" else ngram_token_shingling(tokens, n)
        sig = minhash.signature_from_iter(sh)

        # Query LSH among previous kept docs
        candidates = lsh.candidates(sig)
        total_candidates += len(candidates)
        
        keep = True
        if candidates:
            for cand_idx in candidates:
                total_pairs += 1
                if jaccard(sh, kept_shingles[cand_idx]) >= tau:
                    keep = False
                    break
        
        if keep:
            lsh.add(len(kept_paths), sig) # add signature to LSH
            kept_shingles.append(sh)
            kept_paths.append(path)
        else:
            #print(f"Duplicate found: {path.name}")
            continue
    
    print(f"{len(kept_paths)} unique files out of {len(files)} total files")
    print(f"Total candidates: {total_candidates}, Total pairs checked: {total_pairs}")
    
    for path in kept_paths:
        (outdir / path.name).write_text(path.read_text())
    
    return {
        "unique_count": len(kept_paths),
        "total_files": len(files),
        "candidates": total_candidates,
        "pairs_checked": total_pairs
    }
    
   
if __name__ == "__main__":
    dedup_lsh(indir="data/exact/wiki", outdir="data/lsh/wiki", n=4, type="text", tau=0.30, k=336, r=3, length = 1000)
    dedup_lsh(indir="data/exact/code", outdir="data/lsh/code", n=5, type="code", tau=0.45, k=192, r=3, length = 1000)
