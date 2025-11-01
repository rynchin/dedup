from pathlib import Path
import re, unicodedata
import keyword, tokenize
import io

def normalize_text(text):
    """NFKC normalization + collapse spaces"""
    text = unicodedata.normalize("NFKC", text).lower()
    text = re.sub(r"\s+", " ", text) # normalize spaces
    return text.strip()
    
def normalize_code(code):
    """NFKC normalization + collapse spaces + remove comments"""
    code = unicodedata.normalize("NFKC", code)
    code = re.sub(r"[ \t]+", " ", code) # normalize spaces
    code = re.sub(r"(?m)^\s*#.*$", "", code) # remove comments
    return code.strip()

# TODO: strip inline comments not just block comments
# def strip_inline_comments(code):

def tokenize_text(text):
    text = unicodedata.normalize("NFKC", text).lower()
    text = re.sub(r"[^\w]+", " ", text)
    return [w.lower() for w in text.split() if w]

def tokenize_code(code):
    code = unicodedata.normalize("NFKC", code)
    tokens = []
    try:
        for tok in tokenize.generate_tokens(io.StringIO(code).readline):
            if tok.type == tokenize.COMMENT or tok.type == tokenize.NL: # skip comments and newlines
                continue
            if tok.type == tokenize.NEWLINE:
                tokens.append("NL")
            elif tok.type == tokenize.INDENT:
                tokens.append("IND")
            elif tok.type == tokenize.DEDENT:
                tokens.append("DED")
            elif tok.type == tokenize.NAME and keyword.iskeyword(tok.string):
                tokens.append(f"KW_{tok.string}")
            elif tok.type == tokenize.NAME:
                tokens.append("ID")
            elif tok.type == tokenize.STRING:
                tokens.append("STR")
            elif tok.type == tokenize.NUMBER:
                tokens.append("NUM")
            elif tok.string.strip():
                tokens.append(tok.string.strip())
    except tokenize.TokenError:
        return []
    return tokens

def jaccard(a, b):
    #print(len(a & b) / len(a | b) if len(a | b) > 0 else 0.0)
    return len(a & b) / len(a | b) if len(a | b) > 0 else 0.0

def ngram_token_shingling(tokens, n=4):
    """
    n-gram token shingling of a text, returns set 
    default = 4
    """
    if len(tokens) < n:
        return set()
    return {tuple(tokens[i:i+n]) for i in range(len(tokens)-n+1)}

def ngram_char_shingling(text, k=5):
    """
    k-gram character shingling of a text, returns set
    default = 5
    """
    if len(text) < k:
        return set()
    return {text[i:i+k] for i in range(len(text)-k+1)}

def dedup_jaccard(indir, outdir, n=10, type="text", tau=0.5):
    """
    Deduplicate files using Jaccard similarity
    """
    # TODO: speed up comparisons, currently O(n^2)
    # approximate with minhash lsh?
    indir, outdir = Path(indir), Path(outdir)
    outdir.mkdir(parents=True, exist_ok=True)
    
    norm_data = normalize_text if type == "text" else normalize_code
    
    kept = []
    kept_shingles = []
    
    for path in sorted(indir.glob("*.txt"), key=lambda x: x.stat().st_size, reverse=True): # largest files first
        text = path.read_text()
        text = norm_data(text)
        tokens = tokenize_text(text) if type == "text" else tokenize_code(text)
        sh = ngram_char_shingling(text, n) if type == "text" else ngram_token_shingling(tokens, n)
        if any(jaccard(sh, kept_sh) >= tau for kept_sh in kept_shingles):
            print(f"Duplicate found: {path.name}")
            continue
        kept_shingles.append(sh)
        kept.append(path)
    
    print(f"{len(kept)} unique files out of {len(list(indir.glob('*.txt')))} total files")
    
    for path in kept:
        (outdir / path.name).write_text(path.read_text())

if __name__ == "__main__":
    dedup_jaccard(indir="data/exact/wiki", outdir="data/jaccard/wiki", n=4, type="text", tau=0.30)
    dedup_jaccard(indir="data/exact/code", outdir="data/jaccard/code", n=5, type="code", tau=0.45)