# -*- coding: utf-8 -*-
"""個人ファイルの「未突き合わせ」の断り書きを一括で付ける。

新しい原稿が入ると、版表記が `現収録分001〜NNN時点の整理。` のままのファイルは
その時点で「NNN+1 以降は未確認」という状態になる。検査Eはこれを鳴らすので、
実際に突き合わせるまでの間、断り書きを機械的に付けるのがこのスクリプト。

    python3 tools/stamp_unchecked.py          # 付ける対象を表示するだけ
    python3 tools/stamp_unchecked.py --write  # 実際に書き込む

断り書きは「原稿NNN以降との突き合わせは未実施。」という**終わりを書かない形**で入れる。
「原稿NNN〜119」のように終わりを書くと、新しい原稿が来るたびに全ファイルを
書き換えることになるため。

突き合わせが済んだファイルは、この一文を消して版表記の数字を最新へ直す。
この一文は「その原稿に登場しない」という意味ではなく「まだ確認していない」という意味。
"""
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
P = os.path.join(ROOT, '世界観', '02_人物', '個人')
G = os.path.join(ROOT, '原稿')

# 「現収録分001〜102時点の整理（登場は番外10のみ）。」のように括弧書きが入る例があるので、
# 最初の句点までをひとまとまりとして見る。
版表記 = re.compile(r'(現収録分001〜(\d+)時点[^。\n]*。)')


def 最新原稿():
    n = [int(m.group(1)) for f in os.listdir(G)
         for m in [re.match(r'^(\d{3})_', f)] if m and f.endswith('.txt')]
    if not n:
        sys.exit('原稿が見つからない')
    return max(n)


def main():
    書く = '--write' in sys.argv
    最新 = 最新原稿()
    print('最新の原稿: %03d' % 最新)
    対象 = []
    for f in sorted(os.listdir(P)):
        if not f.endswith('.md'):
            continue
        p = os.path.join(P, f)
        t = open(p, encoding='utf-8').read()
        m = 版表記.search(t)
        if not m:
            print('  版表記が無い（手で確認）:', f)
            continue
        n = int(m.group(2))
        if n >= 最新:
            continue
        断り = '原稿%03d以降との突き合わせは未実施。' % (n + 1)
        if 断り in t:
            continue
        # 既に古い断り書きが付いている場合は触らない（人が見る）
        古い = re.search(r'原稿\d{3}以降との突き合わせは未実施。', t)
        if 古い:
            print('  断り書きの数字が合わない（手で確認）: %s (版表記001〜%d / %s)'
                  % (f, n, 古い.group(0)))
            continue
        対象.append((p, f, n, m.group(1), 断り))

    if not 対象:
        print('付ける対象なし')
        return 0
    for _, f, n, _, 断り in 対象:
        print('  %s (001〜%d) ← %s' % (f, n, 断り))
    print('対象 %d 件' % len(対象))
    if not 書く:
        print('表示のみ。実際に書き込むには --write を付ける')
        return 0
    for p, _, _, 版, 断り in 対象:
        t = open(p, encoding='utf-8').read()
        assert t.count(版) == 1
        open(p, 'w', encoding='utf-8').write(t.replace(版, 版 + 断り, 1))
    print('%d 件へ書き込んだ' % len(対象))
    return 0


if __name__ == '__main__':
    sys.exit(main())
