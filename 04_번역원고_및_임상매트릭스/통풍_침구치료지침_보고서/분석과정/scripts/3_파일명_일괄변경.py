import csv, os, sys
S, D = sys.argv[1], sys.argv[2]
plan = list(csv.reader(open(os.path.join(S, "plan.tsv"), encoding="utf-8"), delimiter="\t"))
for n, o, t in plan:
    assert os.path.exists(os.path.join(D, o)), o
    assert not os.path.exists(os.path.join(D, t)) or o == t, t
log = open(os.path.join(D, "_rename_log.tsv"), "w", encoding="utf-8")
log.write("old_name\tnew_name\n")
ok = 0
for n, o, t in plan:
    os.rename(os.path.join(D, o), os.path.join(D, t)); ok += 1
    log.write(f"{o}\t{t}\n")
print("renamed", ok)
