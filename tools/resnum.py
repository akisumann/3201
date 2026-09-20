#!/usr/bin/env python3
"""原稿の「行番号」から、その行が属するレス番号 (#NNN) を引く。

grep -n の出力をそのまま出典に書いてしまう事故を防ぐための道具。
    python3 tools/resnum.py 原稿/046_番外4_新城編.txt 629 632 157
    grep -n "実の息子" 原稿/046_*.txt | python3 tools/resnum.py -
"""
import re, sys, os

def markers(path):
    out = []
    for i, line in enumerate(open(path, encoding='utf-8'), 1):
        t = line.rstrip('\n')
        m = re.match(r'^#\s*(\d+)\s*$', t)
        if m:
            out.append((i, m.group(1)))
            continue
        # 原稿071以降には `#316-327` `#84～93` という範囲形式のマーカーがある（計976本／40原稿）。
        # 区切りはハイフンと全角チルダの2種類
        m = re.match(r'^#\s*(\d+)\s*[-−–—〜～]\s*(\d+)\s*$', t)
        if m:
            out.append((i, f"{m.group(1)}-{m.group(2)}"))
    return out

def lookup(path, lineno):
    ms = markers(path)
    cur = None
    for i, n in ms:
        if i <= lineno:
            cur = n
        else:
            break
    return cur

def main():
    a = sys.argv[1:]
    if a and a[0] == '-':
        for line in sys.stdin:
            m = re.match(r'^([^:]+):(\d+):(.*)$', line.rstrip('\n'))
            if not m:
                continue
            p, ln, txt = m.group(1), int(m.group(2)), m.group(3)
            print(f"{os.path.basename(p)}  行{ln} → #{lookup(p, ln)}  {txt[:60]}")
        return
    if len(a) < 2:
        print(__doc__); sys.exit(1)
    p = a[0]
    for ln in a[1:]:
        print(f"行{ln} → #{lookup(p, int(ln))}")

main()
