import sys, os, pymupdf, json
src, out = sys.argv[1], sys.argv[2]
files = sorted(f for f in os.listdir(src) if f.lower().endswith('.pdf'))
idx = {}
for i, f in enumerate(files, 1):
    try:
        d = pymupdf.open(os.path.join(src, f))
        t = "\n".join(d[p].get_text() for p in range(min(2, len(d))))
        meta = d.metadata
    except Exception as e:
        t, meta = f"ERR {e}", {}
    idx[i] = f
    with open(os.path.join(out, f"{i:02d}.txt"), "w", encoding="utf-8") as fh:
        fh.write(f"FILE: {f}\nMETA: {meta}\n----\n{t[:3500]}")
json.dump(idx, open(os.path.join(out, "index.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print(len(files))
