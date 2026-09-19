# -*- coding: utf-8 -*-
"""個人ファイルの版表記より後の原稿に、その人物が本当に出てくるかを走査する。

検査Eは「版表記が古い」としか言わないので、214件並んでいても、そのうち何件を
実際に読む必要があるのかが分からない。このスクリプトはそこを三段階に分ける。

    ① 話者として登場   … 原稿に `名前「台詞」` の形で出る。読んで突き合わせる
    ② 名前だけ出る     … 他人の台詞・地の文で言及される。その箇所だけ確認する
    ③ 登場なし         … 名前も台詞も無い。版表記を上げるだけで済む

    python3 tools/scan_appearances.py          # 三段階を表示するだけ
    python3 tools/scan_appearances.py --write  # ③ だけ版表記を上げて確認文を入れる

**① と ② は自動で書き換えない。** 原稿を読む判断が要るため。

原稿は AA→意味文変換なので、行頭が `名前「` か `名前（` になっている。これを
話者ラベルとして拾う。名前の部分一致だけで判定すると「ナギ」⊂「イザナギ」、
「黒」⊂「黒王」、「キョン」⊂「キョン子」のように取り違えるので、①は
**原稿側のラベルから個人ファイルを逆引きする**形にしてある。

短い名前（「電」→電話・電波・電探、「セル」→キャンセル、「わたし」→一人称）は
②で誤検出しやすい。この一覧は `世界観/02_人物/README.md` の
「全文走査で誤検出しやすい名前」の表から読む。スクリプト内に持たないのは、
ノート側を更新し忘れたときに気付けるようにするため。
"""
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
個人 = os.path.join(ROOT, '世界観', '02_人物', '個人')
原稿ディレクトリ = os.path.join(ROOT, '原稿')
人物README = os.path.join(ROOT, '世界観', '02_人物', 'README.md')

版表記 = re.compile(r'(現収録分001〜(\d+)時点([^。\n]*)。)')
行頭話者 = re.compile(r'^([^\s「（(【\[［#＃]{1,20})[「（]')
ラベル除外 = re.compile(r'^[・※\-—…‥。、\d]')
確認文 = '原稿{}〜{}は全文走査で名前・台詞ともに無いことを確認（2026-09-19）。'


def 読む(path):
    with open(path, encoding='utf-8', errors='replace') as f:
        return f.read()


def 誤検出しやすい名前():
    """`02_人物/README.md` の表から読む。1列目が名前。"""
    t = 読む(人物README)
    if '## 全文走査で誤検出しやすい名前' not in t:
        return set()
    節 = t.split('## 全文走査で誤検出しやすい名前', 1)[1].split('\n## ', 1)[0]
    名 = set()
    for 行 in 節.split('\n'):
        if not 行.startswith('|') or 行.startswith('|--'):
            continue
        セル = [x.strip() for x in 行.strip().strip('|').split('|')]
        if セル and セル[0] and セル[0] != '名前':
            名.add(セル[0].strip('`'))
    return 名


def 原稿を読む():
    本文, 話者 = {}, {}
    for 名 in sorted(os.listdir(原稿ディレクトリ)):
        m = re.match(r'(\d{3})_.*\.txt$', 名)
        if not m:
            continue
        n = int(m.group(1))
        t = 読む(os.path.join(原稿ディレクトリ, 名))
        本文[n] = t
        for 行 in t.split('\n'):
            mm = 行頭話者.match(行.rstrip())
            if mm:
                lab = mm.group(1).strip()
                if len(lab) >= 2 and not ラベル除外.match(lab):
                    話者.setdefault(lab, set()).add(n)
    return 本文, 話者


def 候補名(ファイル名):
    base = re.sub(r'[（(].*?[)）]', '', ファイル名)
    名 = {x.strip() for x in base.split('_') if len(x.strip()) >= 2}
    return 名 or {base}


def main():
    書く = '--write' in sys.argv
    本文, 話者 = 原稿を読む()
    最新 = max(本文)
    紛らわしい = 誤検出しやすい名前()

    # 話者ラベルを個人ファイルへ逆引きする。1つに定まらないラベルは採用せず、
    # 「手で判定」として別に出す。`ナギ`が`三千院ナギ`と`イザナギ`の両方に当たる類を、
    # 取り違えたまま数えないため。
    全ファイル = [f[:-3] for f in sorted(os.listdir(個人)) if f.endswith('.md')]
    ラベル対応, 曖昧 = {}, []
    for lab, nums in 話者.items():
        完全 = [f for f in 全ファイル if lab in 候補名(f)]
        当たり = 完全 or [f for f in 全ファイル if any(lab in c for c in 候補名(f))]
        if len(当たり) == 1:
            ラベル対応.setdefault(当たり[0], []).append(lab)
        elif len(当たり) > 1:
            曖昧.append((len(nums), lab, 当たり))

    話者あり, 言及のみ, 登場なし = [], [], []
    for f in sorted(os.listdir(個人)):
        if not f.endswith('.md'):
            continue
        path = os.path.join(個人, f)
        t = 読む(path)
        m = 版表記.search(t)
        if not m:
            continue
        n = int(m.group(2))
        if n >= 最新:
            continue
        名 = f[:-3]
        候補 = 候補名(名)

        ラベル = set()
        for lab in ラベル対応.get(名, ()):
            ラベル |= {x for x in 話者[lab] if x > n}
        if ラベル:
            話者あり.append((len(ラベル), n, 名, sorted(ラベル)))
            continue

        言及 = [k for k in sorted(本文) if k > n and any(c in 本文[k] for c in 候補)]
        if 言及:
            言及のみ.append((len(言及), n, 名, 言及,
                          bool(({名} | 候補) & 紛らわしい)))
        else:
            # m.group(3) は「（登場は番外10＝原稿102のみ）」のような但し書き。消さずに持ち回る。
            登場なし.append((n, 名, path, m.group(1), m.group(3)))

    合計 = len(話者あり) + len(言及のみ) + len(登場なし)
    print('版表記が原稿%d に追いついていない個人ファイル: %d 件' % (最新, 合計))
    print('  ① 話者として登場        : %3d 件  ← 読んで突き合わせる' % len(話者あり))
    print('  ② 名前だけ出る          : %3d 件  ← 言及箇所だけ確認する' % len(言及のみ))
    print('  ③ 登場なし              : %3d 件  ← 版表記を上げるだけ' % len(登場なし))

    if 話者あり:
        print()
        print('① 話者として登場')
        for c, n, 名, nums in sorted(話者あり, reverse=True):
            print('  %2d話  版001〜%-4s %-26s 原稿%s'
                  % (c, n, 名, ','.join(map(str, nums[:8])) + ('…' if len(nums) > 8 else '')))

    if 言及のみ:
        print()
        print('② 名前だけ出る（★＝誤検出しやすい名前として登録済み）')
        for c, n, 名, nums, 紛 in sorted(言及のみ, key=lambda x: -x[0]):
            print('  %s%2d話  版001〜%-4s %-26s 原稿%s'
                  % ('★' if 紛 else '  ', c, n, 名,
                     ','.join(map(str, nums[:8])) + ('…' if len(nums) > 8 else '')))

    if 曖昧:
        print()
        print('ラベルが複数の個人ファイルに当たる（どちらの人物か手で判定する）')
        for c, lab, 当たり in sorted(曖昧, reverse=True):
            print('  %2d話  %-16s → %s' % (c, lab, ' / '.join(当たり)))

    if not 書く:
        print()
        print('③ の %d 件を書き換えるには --write を付ける' % len(登場なし))
        return

    直した = 0
    for n, 名, path, 旧, 但し書き in 登場なし:
        t = 読む(path)
        # 行末の改行まで飲み込まないよう `\s*` は使わない。断り書きだけを消す。
        古い断り = re.search(r'原稿\d{3}以降との突き合わせは未実施。', t)
        新 = ('現収録分001〜%d時点%s。' % (最新, 但し書き)) + 確認文.format(n + 1, 最新)
        t = t.replace(旧, 新, 1)
        if 古い断り:
            t = t.replace(古い断り.group(0), '', 1)
        with open(path, 'w', encoding='utf-8') as f:
            f.write(t)
        直した += 1
    print()
    print('③ の %d 件へ版表記と確認文を書き込んだ' % 直した)


if __name__ == '__main__':
    main()
