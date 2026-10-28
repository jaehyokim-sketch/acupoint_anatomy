import csv, re, os, sys
S = sys.argv[1]
rows = []
for f in ("meta_01.tsv", "meta_25.tsv", "meta_49.tsv"):
    with open(os.path.join(S, f), encoding="utf-8") as fh:
        r = list(csv.reader(fh, delimiter="\t"))
    rows += [x for x in r if x and x[0].strip().isdigit()]
def clean(s):
    s = s.strip()
    s = s.replace("“", "").replace("”", "").replace('"', "").replace("《", "").replace("》", "")
    s = re.sub(r'[\/:*?<>|]', " ", s)
    s = re.sub(r"\s+", " ", s).strip(" .")
    return s
seen = {}
out = []
for x in rows:
    num, orig, year, jour, auth, title = x[:6]
    name = "_".join(clean(v) for v in (year, jour, auth, title))
    if len(name) > 180: name = name[:180]
    base = name; k = 2
    while name.lower() in seen:
        name = f"{base} ({k})"; k += 1
    seen[name.lower()] = 1
    out.append((num, orig, name + ".pdf"))
with open(os.path.join(S, "plan.tsv"), "w", encoding="utf-8", newline="") as fh:
    csv.writer(fh, delimiter="\t").writerows(out)
for n, o, t in out: print(n, t)
print(len(out))
