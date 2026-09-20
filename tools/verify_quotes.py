#!/usr/bin/env python3
"""ノートの「引用」が、その行の出典 (原稿番号 #レス番号) の原稿に実在するか照合する。

    python3 tools/verify_quotes.py 世界観/02_人物/個人/新城直衛.md
    python3 tools/verify_quotes.py 世界観/02_人物/個人/          # ディレクトリも可

判定は「引用文が、その原稿のどこかに出てくるか」。レス番号の位置までは見ない
（レス番号は tools/resnum.py と check_notes.py の検査Hが見る）。

原稿側は行頭の話者ラベル（`名前「`）と鉤括弧・空白を落として1本に連結してから
比較する。ノート側が複数の台詞を1つの「」へまとめて書く慣例に合わせるため。

鳴る典型は3つ。
  1. 原文に無い句点・語を足した（「分かるね」→「分かるね。」）
  2. 自分の要約を「」で囲ってしまった  ← いちばん危険
  3. 出典の原稿番号そのものが違う
"""
import re, sys, os, glob

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_cache = {}

def corpus(g):
    if g in _cache:
        return _cache[g]
    f = [x for x in glob.glob(os.path.join(ROOT, '原稿', '*.txt'))
         if os.path.basename(x).startswith(g)]
    if not f:
        _cache[g] = None
        return None
    out = []
    for l in open(f[0], encoding='utf-8'):
        l = l.strip()
        if l.startswith('#'):
            continue          # レス番号マーカーは本文ではない
        # AA注記（［…］）は変換者の記述だが原稿の一部であり、引用元になり得るので残す。
        # 台詞のあいだに挟まっても、下の断片一致なら連結を妨げない。
        out.append(re.sub(r'^[^\s「（［【]*[「（]', '', l))
    _cache[g] = norm(''.join(out))
    return _cache[g]

_Z = str.maketrans('？！、。〜・：；（）［］「」『』', '?!,.~-:;()[]""\'\'')

def norm(t):
    """全角/半角の句読点差と括弧・空白を吸収する。

    ノート側（特に旧ログ）は `?` `!` の半角、原稿は全角を使うことが多い。
    ここを揃えないと、正しい引用が大量に誤検出される。"""
    return re.sub(r'[\s"\'()\[\]\*]', '', t.translate(_Z))

def all_ids():
    return sorted(os.path.basename(x)[:3]
                  for x in glob.glob(os.path.join(ROOT, '原稿', '*.txt')))

WIN = 12   # この長さの連続断片が原稿に在れば「引用として実在」とみなす

def windows(q):
    n = norm(q)
    if len(n) < WIN:
        return [n]
    return [n[i:i + WIN] for i in range(len(n) - WIN + 1)]

def locate(q):
    """引用が実際にどの原稿に在るかを全走査で返す。

    ノート（特に旧ログ）は複数の台詞を1つの「」へ連結し、`(愛染は)` のような
    補注を括弧で挟むことがある。そのため全文一致ではなく、長さ WIN の連続断片が
    1つでも在るかで判定する。連結・補注は許し、原文に無い文だけを落とす。"""
    ws = windows(q)
    return [g for g in all_ids()
            if (c := corpus(g)) and any(w in c for w in ws)]

def check(path, minlen=10):
    """(行番号, 行の出典, 引用, 実際に在った原稿) を返す。

    出典に挙がっていない原稿にだけ在れば出典の誤り、
    どこにも無ければ原文に無い文（要約を「」で囲った等）。"""
    out = []
    for no, line in enumerate(open(path, encoding='utf-8'), 1):
        gs = set(re.findall(r'\((\d{3})\s*#', line))
        if not gs:
            continue
        for q in re.findall(r'「([^」]{%d,})」' % minlen, line.replace('**', '')):
            found = locate(q)
            if set(found) & gs:
                continue
            out.append((no, sorted(gs), q, found))
    return out


def main():
    args = [a for a in sys.argv[1:] if not a.startswith('-')]
    if not args:
        print(__doc__); sys.exit(1)
    targets = []
    for a in args:
        targets += sorted(glob.glob(os.path.join(a, '**', '*.md'), recursive=True)) \
                   if os.path.isdir(a) else [a]
    total = 0
    for t in targets:
        ng = check(t)
        if ng:
            print(f"--- {os.path.relpath(t, ROOT)}")
            for no, gs, q, found in ng:
                where = ('実際は ' + '/'.join(found)) if found else '★どの原稿にも無い'
                print(f"  {no:>5}行  出典{'/'.join(gs)} → {where}")
                print(f"         「{q[:64]}」")
            total += len(ng)
    print(f"\n出典と噛み合わない引用: {total} 件 / 対象 {len(targets)} ファイル")

main()
