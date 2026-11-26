"""
Compare file_re with plain Python re on the log made by gen_log.py.

Usage: python bench.py "CASE NAME" DATA_DIR
DATA_DIR must contain big.log and big.log.gz (gzip -k big.log). Each case
runs in its own process so the peak memory figure is per case; see the
`cases` dict for the names.
"""
import sys, re, time, resource, gzip
from collections import deque
from file_re import file_re
D = sys.argv[2]
F, GZ = D + "/big.log", D + "/big.log.gz"
SPARSE = r"ERROR: (\w+) failed code=(\d+)"
DENSE = r"id=(\d+)"
ML = r"BEGIN TXN id=(\d+)\n(?:.*\n){0,3}END TXN"
MULTI = [SPARSE, r"BEGIN TXN id=(\d+)", r"ip=10\.0\.7\.(\d+)", r"timeout retry (\w+)", r"user=u(\d+)5\b"]

def py_full(p, path=F):
    with open(path, encoding="utf-8") as f: return len(re.findall(p, f.read()))
def py_line(p, path=F, op=open):
    c = re.compile(p); n = 0
    with op(path, "rt", encoding="utf-8") as f:
        for line in f:
            for _ in c.finditer(line): n += 1
    return n
def py_line_search(p):
    c = re.compile(p).search; n = 0
    with open(F, encoding="utf-8") as f:
        for line in f:
            if c(line): n += 1
    return n
def py_multi_line():
    cs = [re.compile(p).search for p in MULTI]; n = 0
    with open(F, encoding="utf-8") as f:
        for line in f:
            for c in cs:
                if c(line): n += 1
    return n
def py_multi_full():
    with open(F, encoding="utf-8") as f: t = f.read()
    return sum(len(re.findall(p, t)) for p in MULTI)
cases = {
 "sparse py full findall":      lambda: py_full(SPARSE),
 "sparse py line loop":         lambda: py_line(SPARSE),
 "sparse fr full findall":      lambda: len(file_re.findall(SPARSE, F)),
 "sparse fr line findall":      lambda: len(file_re.findall(SPARSE, F, max_span_lines=1)),
 "sparse fr line finditer":     lambda: sum(1 for _ in file_re.finditer(SPARSE, F, max_span_lines=1)),
 "sparse fr full finditer":     lambda: sum(1 for _ in file_re.finditer(SPARSE, F)),
 "dense py full findall":       lambda: py_full(DENSE),
 "dense py line loop":          lambda: py_line(DENSE),
 "dense fr full findall":       lambda: len(file_re.findall(DENSE, F)),
 "dense fr line findall":       lambda: len(file_re.findall(DENSE, F, max_span_lines=1)),
 "dense fr line finditer":      lambda: sum(1 for _ in file_re.finditer(DENSE, F, max_span_lines=1)),
 "ml py full findall":          lambda: py_full(ML),
 "ml fr full findall":          lambda: len(file_re.findall(ML, F)),
 "ml fr window5 findall":       lambda: len(file_re.findall(ML, F, max_span_lines=5)),
 "ml fr window20 findall":      lambda: len(file_re.findall(ML, F, max_span_lines=20)),
 "gz py line loop":             lambda: py_line(SPARSE, GZ, gzip.open),
 "gz fr line findall":          lambda: len(file_re.findall(SPARSE, GZ, max_span_lines=1)),
 "multi5 py line loop":         py_multi_line,
 "multi5 py full":              py_multi_full,
 "multi5 fr line x5 passes":    lambda: sum(len(file_re.findall(p, F, max_span_lines=1)) for p in MULTI),
 "multi5 fr full x5 passes":    lambda: sum(len(file_re.findall(p, F)) for p in MULTI),
}
name = sys.argv[1]
t = time.perf_counter(); n = cases[name](); dt = time.perf_counter() - t
print(f"{name:28s} {dt:8.2f}s  {resource.getrusage(resource.RUSAGE_SELF).ru_maxrss/1024:8.0f} MB  n={n}")
