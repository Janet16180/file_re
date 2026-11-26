"""Generate a synthetic log file. Usage: python gen_log.py OUT_PATH SIZE_MB"""
import random, sys
random.seed(1)
out = sys.argv[1]; target = int(sys.argv[2]) * 1024 * 1024
words = "alpha beta gamma delta request handler socket timeout retry cache index worker queue commit rollback".split()
n = 0
with open(out, "w") as f:
    i = 0
    while n < target:
        i += 1
        r = random.random()
        if r < 0.002:
            s = f"2026-04-17 12:00:{i%60:02d} BEGIN TXN id={i}\n  step one {random.choice(words)}\n  step two {random.choice(words)}\nEND TXN\n"
        elif r < 0.012:
            s = f"2026-04-17 12:00:{i%60:02d} ERROR: {random.choice(words)} failed code={random.randint(1,999)} user=u{i}\n"
        else:
            s = f"2026-04-17 12:00:{i%60:02d} INFO {' '.join(random.choices(words, k=8))} id={i} ip=10.0.{i%255}.{i%251}\n"
        f.write(s); n += len(s)
