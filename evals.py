from pathlib import Path
import time, shutil
from methods.jaccard import dedup_jaccard
from methods.lsh import dedup_lsh
from methods.simhash import dedup_sim

def kept_set(dirpath):
    return {p.name for p in Path(dirpath).glob("*.txt")}

def compare(baseline_dir, lsh_dir, hier_dir, label = ""):
    gt   = kept_set(baseline_dir)
    pred = kept_set(lsh_dir)
    hier = kept_set(hier_dir)

    agree = gt & pred
    only_gt = gt - pred # LSH dropped files
    only_pred = pred - gt # LSH extra files
    
    agree_hier = gt & hier
    only_gt_hier = gt - hier # Hier dropped files
    only_hier = hier - gt # Hier extra files

    print(f"{label}: baseline={len(gt)} | lsh={len(pred)} | agree={len(agree)} | only_baseline={len(only_gt)} | only_lsh={len(only_pred)}")
    print(f"hier: baseline={len(gt)} | hier={len(hier)} | agree={len(agree_hier)} | only_baseline={len(only_gt_hier)} | only_hier={len(only_hier)}")

def compare_lsh_hier(lsh_dir, hier_dir, label = ""):
    lsh = kept_set(lsh_dir)
    hier = kept_set(hier_dir)
    
    agree = lsh & hier
    only_lsh = lsh - hier # LSH extra files
    only_hier = hier - lsh # Hier extra files
    
    print(f"{label}: lsh={len(lsh)} | hier={len(hier)} | agree={len(agree)} | only_lsh={len(only_lsh)} | only_hier={len(only_hier)}")

def run_and_time(fn, **kwargs):
    t0 = time.perf_counter()
    fn(**kwargs)
    return time.perf_counter() - t0

def clean(path):
    p = Path(path)
    if p.exists():
        shutil.rmtree(p)
    p.mkdir(parents=True)
    
if __name__ == "__main__":
    # Text
    #clean("data/jaccard/wiki")
    #clean("data/lsh/wiki")
    clean("data/hier/wiki")

    #tj_text = run_and_time(dedup_jaccard, indir="data/exact/wiki", outdir="data/jaccard/wiki", n=4, type="text", tau=0.30)
    #tl_text = run_and_time(dedup_lsh, indir="data/exact/wiki", outdir="data/lsh/wiki", n=4, type="text", tau=0.30, k=336, r=3)
    th_text = run_and_time(dedup_sim, indir="data/exact/wiki", outdir="data/hier/wiki", n=4, type="text", tau=0.30, t=7, k=336, r=3)
    
    # Code
    #clean("data/jaccard/code"); 
    #clean("data/lsh/code")
    clean("data/hier/code")
    
    #tj_code = run_and_time(dedup_jaccard, indir="data/exact/code", outdir="data/jaccard/code", n=5, type="code", tau=0.45)
    #tl_code = run_and_time(dedup_lsh, indir="data/exact/code", outdir="data/lsh/code", n=5, type="code", tau=0.45, k=192, r=3)
    th_code = run_and_time(dedup_sim, indir="data/exact/code", outdir="data/hier/code", n=5, type="code", tau=0.45, t=7, k=192, r=3)
    
    
    # Compare
    #print(f"text: jaccard={tj_text:.2f}s | lsh={tl_text:.2f}s")
    #print(f"code: jaccard={tj_code:.2f}s | lsh={tl_code:.2f}s")
    
    # print(f"text: lsh={tl_text:.2f}s")
    # print(f"code: lsh={tl_code:.2f}s")
    print(f"text: hier={th_text:.2f}s")
    print(f"code: hier={th_code:.2f}s")

    #compare("data/jaccard/wiki", "data/lsh/wiki", "text")
    #compare("data/jaccard/code", "data/lsh/code", "code")
    # compare("data/exact/wiki", "data/lsh/wiki", "data/hier/wiki", "text")
    # compare("data/exact/code", "data/lsh/code", "data/hier/code", "code")
    compare_lsh_hier("data/lsh/wiki", "data/hier/wiki", "text")
    compare_lsh_hier("data/lsh/code", "data/hier/code", "code")