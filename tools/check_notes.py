# -*- coding: utf-8 -*-
"""
世界観ノートの点検スクリプト

    python3 tools/check_notes.py

作業の前と、コミットの前に実行する。記憶や前回の会話ではなく、
その時点の実ファイルを数えて報告する。

このスクリプトは「間違いを見つける」だけで、何も書き換えない。
報告された項目は人が判断して直す。

許可リストはスクリプト内に持たず、ノート側の表から読む。
  - 統合で消えた旧ファイル名 → 世界観/02_人物/README.md の「→」の行
  - 統合してはいけない似た名前の組 → 同 README の「似た名前でも統合してはいけない組」の表
ノートを直せば検査も追随する。逆に、表を更新し忘れると検査が鳴る。
"""
import os, re, sys, collections

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
W = os.path.join(ROOT, '世界観')
G = os.path.join(ROOT, '原稿')
P = os.path.join(W, '02_人物', '個人')
S = os.path.join(W, '07_読書スナップショット')

問題 = []
参考 = []

def NG(検査, 内容):
    問題.append('[%s] %s' % (検査, 内容))

def 見出し(s):
    print('\n' + s)
    print('-' * 60)

def md一覧():
    for d, _, fs in os.walk(W):
        for f in sorted(fs):
            if f.endswith('.md'):
                yield os.path.join(d, f)

def 読む(p):
    return open(p, encoding='utf-8').read()


# ===== A. 原稿の連番・命名・README表 =====
def 放棄した連番():
    """`原稿/README.md` の「放棄した連番」の表から読む。

    整形前の途中版を誤って受け取ったときなど、その連番を一旦取り下げることがある。
    実ファイルは無いが、世界観ノート側の記述と版表記はその番号のまま残す運用なので、
    欠番として鳴らさず、版表記の上限としては有効な番号として扱う。
    許可リストをスクリプト内に持たないのは、ノート側を消し忘れたときに気付けるようにするため。
    """
    rd = 読む(os.path.join(G, 'README.md'))
    if '## 放棄した連番' not in rd:
        return {}
    節 = rd.split('## 放棄した連番', 1)[1].split('\n## ', 1)[0]
    出 = {}
    for 行 in 節.split('\n'):
        if not 行.startswith('|') or 行.startswith('|--'):
            continue
        セル = [x.strip() for x in 行.strip().strip('|').split('|')]
        if セル and re.fullmatch(r'\d{3}', セル[0]):
            出[int(セル[0])] = セル[1] if len(セル) > 1 else ''
    return 出


def 検査A(放棄=None):
    放棄 = 放棄 or {}
    見出し('A. 原稿の連番と 原稿/README.md の表')
    files = sorted(f for f in os.listdir(G) if f.endswith('.txt'))
    nums = {}
    for f in files:
        m = re.match(r'^(\d{3})_(.+)\.txt$', f)
        if not m:
            NG('A', '命名規則から外れたファイル: %s' % f); continue
        n = int(m.group(1))
        if n in nums:
            NG('A', '連番の重複: %03d (%s / %s)' % (n, nums[n], f))
        nums[n] = f
    if not nums:
        NG('A', '原稿が1件も見つからない'); return None
    lo, hi = min(nums), max(nums)
    上限 = max([hi] + list(放棄))
    欠番 = [i for i in range(lo, 上限 + 1) if i not in nums and i not in 放棄]
    if 欠番:
        見本 = ['%03d' % i for i in 欠番[:20]]
        NG('A', '連番の欠番 %d 件: %s%s' % (len(欠番), '、'.join(見本), ' ほか' if len(欠番) > 20 else ''))
    # 放棄した連番があれば、そこが空いているので次に受け取るのはその番号。
    # 放棄した連番の実ファイルが戻ってきたら、表から行を消すまで運用が噛み合わない。
    # 「README の表に無い原稿」という一般的な文言では何をすべきか分からないので、
    # ここで名指しして手順を出す。
    戻った = sorted(set(放棄) & set(nums))
    for n in 戻った:
        NG('A', '放棄した連番 %03d の実ファイルがある。'
                '`原稿/README.md` の「放棄した連番」の表から %03d の行を消し、'
                '本表へ1行足すこと（消すまで「次の連番」が %03d のままになる）' % (n, n, n))
    有効な放棄 = {k: v for k, v in 放棄.items() if k not in nums}
    次 = min(有効な放棄) if 有効な放棄 else 上限 + 1
    print('原稿 %d 件 / 範囲 %03d〜%03d / 次の連番は %03d' % (len(nums), lo, hi, 次))
    for n in sorted(有効な放棄):
        print('  放棄した連番 %03d（受領待ち） … %s' % (n, 有効な放棄[n][:56]))

    rd = 読む(os.path.join(G, 'README.md'))
    rows = {}
    for m in re.finditer(r'^\|\s*(\d{3})\s*\|\s*`([^`]+)`', rd, re.M):
        rows[int(m.group(1))] = m.group(2)
    print('原稿/README.md の表: %d 行' % len(rows))
    for n in sorted(set(nums) - set(rows)):
        NG('A', 'README の表に無い原稿: %03d %s' % (n, nums[n]))
    for n in sorted(set(rows) - set(nums) - set(放棄)):
        NG('A', '実ファイルが無い README 行: %03d' % n)
    for n, fn in sorted(rows.items()):
        if n in nums and nums[n] != fn:
            NG('A', 'README のファイル名が実物と違う: %03d 表=%s 実=%s' % (n, fn, nums[n]))
    # 版表記・年表・あらすじの上限は、放棄した連番も含めた番号で見る。
    # ノート側の記述はその番号のまま残す運用のため。
    return 上限


# ===== B. ノート内の .md 参照が実在するか =====
def 統合表():
    """02_人物/README.md から「旧名 → 新名」を読む"""
    rd = 読む(os.path.join(W, '02_人物', 'README.md'))
    消えた名 = set()
    for m in re.finditer(r'^- `([^`]+\.md)`\s*→\s*`([^`]+\.md)`', rd, re.M):
        消えた名.add(os.path.basename(m.group(1)))
    return 消えた名

def 検査B(消えた名):
    見出し('B. ノート内のファイル参照')
    実在 = {os.path.basename(p) for p in md一覧()}
    切れ = {}
    for p in md一覧():
        for m in re.finditer(r'`([^`\n]*?\.md)`', 読む(p)):
            t = m.group(1)
            if '<' in t or '>' in t:
                continue  # `02_人物/個人/<人物名>.md` のような書式説明
            b = os.path.basename(t)
            if b in 実在 or b in 消えた名:
                continue
            切れ.setdefault(t, set()).add(os.path.relpath(p, ROOT))
    print('統合で消えた旧名として許可: %d 件' % len(消えた名))
    if not 切れ:
        print('リンク切れ なし')
    for t, ps in sorted(切れ.items()):
        NG('B', '実在しないファイルを参照: `%s` ← %s' % (t, '、'.join(sorted(ps)[:3])))


# ===== C. 人物ファイルの重複候補 =====
def 別人表():
    """02_人物/README.md の「似た名前でも統合してはいけない組」を読む"""
    rd = 読む(os.path.join(W, '02_人物', 'README.md'))
    m = re.search(r'###\s*似た名前でも統合してはいけない組(.*?)(?=\n## |\Z)', rd, re.S)
    組 = set()
    if not m:
        NG('C', '02_人物/README.md に「似た名前でも統合してはいけない組」の表が見つからない')
        return 組
    for row in re.finditer(r'^\|\s*`([^`]+)`\s*\|\s*`([^`]+)`\s*\|', m.group(1), re.M):
        a, b = row.group(1), row.group(2)
        組.add(frozenset((a, b)))
    return 組

def 検査C(組):
    見出し('C. 人物ファイルの重複候補（名前の包含関係）')
    名 = sorted(f[:-3] for f in os.listdir(P) if f.endswith('.md'))
    print('個人ファイル %d 件 / 別人と確認済みの組 %d 組' % (len(名), len(組)))
    見つかった = set()
    for a in 名:
        for b in 名:
            if a != b and a in b:
                見つかった.add(frozenset((a, b)))
    for pair in sorted(見つかった, key=lambda x: sorted(x)):
        if pair not in 組:
            x, y = sorted(pair)
            NG('C', '重複候補（表に無い組）: `%s` ⊂ `%s` — 同一人物なら統合、別人なら README の表へ追記' % (x, y))
    for pair in sorted(組, key=lambda x: sorted(x)):
        x, y = sorted(pair)
        if (x + '.md') not in os.listdir(P) or (y + '.md') not in os.listdir(P):
            参考.append('[C] 表にあるが個人ファイルが揃っていない組: `%s` / `%s`（片方がモブ扱い・未作成・統合済みなら表の行を見直す）' % (x, y))
    if not any(s.startswith('[C]') for s in 問題):
        print('表に無い重複候補 なし')


# ===== D. 用語集 =====
def 検査D():
    見出し('D. 用語集')
    合計 = 0
    用語 = collections.defaultdict(list)
    for f in sorted(os.listdir(os.path.join(W, '01_用語集'))):
        if not f.endswith('.md') or f == 'README.md':
            continue
        p = os.path.join(W, '01_用語集', f)
        件 = 0
        for i, l in enumerate(読む(p).split('\n'), 1):
            if not l.startswith('|'):
                continue
            c = [x.strip() for x in l.strip().strip('|').split('|')]
            if not c or c[0] == '用語' or set(c[0]) <= set('-'):
                continue
            if len(c) != 4:
                NG('D', '%s:%d 列数が4でない(%d列): %s' % (f, i, len(c), l[:40]))
            件 += 1
            用語[c[0].replace('**', '').strip()].append(f)
        print('  %-24s %4d 項目' % (f, 件))
        合計 += 件
    print('用語集 合計 %d 項目' % 合計)
    for k, v in sorted(用語.items()):
        if len(v) > 1:
            NG('D', '用語名の重複: 「%s」 %s' % (k, v))

    # 用語集以外の表も列ずれを見る。ヘッダより多い列は Markdown が捨てるため、
    # 書いた内容が表示されない（2026-09-19に用語集25行・地理114行でこれが起きていた）
    for 相対 in ['03_地理.md', '05_社会・制度.md', '04_歴史・年表.md']:
        p2 = os.path.join(W, 相対)
        if not os.path.exists(p2):
            continue
        列数 = None
        ずれ = 0
        for i, l in enumerate(読む(p2).split('\n'), 1):
            if not l.startswith('|'):
                continue
            c = [x.strip() for x in l.strip().strip('|').split('|')]
            if set(c[0]) <= set('-'):
                continue
            # 見出し行（次が区切り行）を列数の基準にする
            if 列数 is None or c[0] in ('地名', '地区', '用語', '時期', '年代', '項目'):
                列数 = len(c)
                continue
            if len(c) != 列数:
                ずれ += 1
                if ずれ <= 3:
                    NG('D', '%s:%d 列数が見出しと違う(見出し%d列/この行%d列): %s' % (相対, i, 列数, len(c), c[0][:24]))
        if ずれ > 3:
            NG('D', '%s ほか %d 行で同じ列ずれ' % (相対, ずれ - 3))
    return 合計


# ===== E. 個人ファイルの版表記 =====
def 検査E(最新原稿):
    見出し('E. 個人ファイルの版表記')
    n古 = n新 = 0
    分布 = {}
    for f in sorted(os.listdir(P)):
        if not f.endswith('.md'):
            continue
        t = 読む(os.path.join(P, f))
        m = re.search(r'現収録分001〜(\d+)時点', t)
        if not m:
            NG('E', '冒頭の版表記が無い: %s' % f); continue
        n = int(m.group(1))
        if n > 最新原稿:
            NG('E', '版表記が収録より新しい: %s (001〜%d だが最新は %d)' % (f, n, 最新原稿))
        # 版表記の行そのものは除く（断り書きの「原稿102〜119」を本文と誤認しないため）
        本文 = '\n'.join(l for l in t.split('\n') if '現収録分001〜' not in l)
        より後 = sorted({int(x) for x in re.findall(r'原稿(\d{3})', 本文)} - set(range(0, n + 1)))
        if より後:
            NG('E', '版表記より後の原稿に触れている: %s (表記 001〜%d / 本文に %s)' % (f, n, より後[:5]))
        分布[n] = 分布.get(n, 0) + 1
        if n >= 最新原稿:
            n新 += 1
        else:
            n古 = n古 + 1
            # 断り書きは「原稿NNN以降」の開いた形で書く。
            # 「原稿NNN〜119」のように終わりを書くと、新しい原稿が来るたび
            # 全ファイルを書き換える羽目になるため。
            if ('原稿%03d以降との突き合わせは未実施' % (n + 1)) not in t:
                NG('E', '未突き合わせの断り書きが無い: %s '
                        '(001〜%d のまま。「原稿%03d以降との突き合わせは未実施。」を'
                        '版表記と同じ行へ足す。tools/stamp_unchecked.py で一括可)'
                   % (f, n, n + 1))
    print('版表記が最新(001〜%d): %d 件 / 未突き合わせ: %d 件' % (最新原稿, n新, n古))
    for n in sorted(分布):
        print('  001〜%03d 時点 … %3d 件%s' % (n, 分布[n], '' if n >= 最新原稿 else ' (未突き合わせ)'))


# ===== F. 説明文に書かれた数と実数 =====
def 検査F(個人数, 用語数, 原稿数, 次の連番=None):
    見出し('F. CLAUDE.md・README に書かれた数と実数')
    実数 = {'個人ファイル': 個人数, '用語集の項目': 用語数, '原稿': 原稿数}
    for k, v in 実数.items():
        print('  %s: %d' % (k, v))
    c = 読む(os.path.join(ROOT, 'CLAUDE.md'))
    for m in re.finditer(r'`個人/`（(\d+)ファイル）', c):
        if int(m.group(1)) != 個人数:
            NG('F', 'CLAUDE.md の個人ファイル数が実数と違う: 記載%s / 実数%d' % (m.group(1), 個人数))
    for m in re.finditer(r'（(\d+)項目、用語名の重複ゼロ）', c):
        if int(m.group(1)) != 用語数:
            NG('F', 'CLAUDE.md の用語集項目数が実数と違う: 記載%s / 実数%d' % (m.group(1), 用語数))
    # 放棄した連番があると「次の連番」は原稿数+1 とは限らない（空いた番号が先）。
    期待 = 次の連番 if 次の連番 else 原稿数 + 1
    for m in re.finditer(r'次の連番は(\d+)', c):
        if int(m.group(1)) != 期待:
            NG('F', 'CLAUDE.md の「次の連番」が実数と違う: 記載%s / 実数%d' % (m.group(1), 期待))


# ===== G. 99_未確定の項目数 =====
def 検査G():
    見出し('G. 99_未確定 の項目数')
    for f in ['00_未回収の伏線.md', '01_矛盾・要注意.md', '02_解決済み.md', '03_話者表記.md']:
        p = os.path.join(W, '99_未確定', f)
        if not os.path.exists(p):
            NG('G', 'ファイルが無い: %s' % f); continue
        L = 読む(p).split('\n')
        print('  %-20s 項目 %d' % (f, sum(1 for l in L if l.startswith('- **'))))
    p = os.path.join(W, '99_未確定', '00_未回収の伏線.md')
    L = 読む(p).split('\n')
    i = [k for k, l in enumerate(L) if l.startswith('## 旧 ')]
    if i:
        cur = None
        c = collections.Counter()
        for k, l in enumerate(L):
            if l.startswith('### '):
                cur = l[4:]
            if k > i[0] and l.startswith('- **') and cur:
                c[cur] += 1
        print('  旧99移行分の内訳:')
        for s, n in c.items():
            print('    %-50s %d' % (s, n))


# ===== H. 出典 (原稿番号 #レス番号) が原稿と噛み合うか =====
def 検査H():
    """
    ノートの `030 #559` のような出典を、実際の原稿ファイルのレス番号マーカー
    (`^#数字$` の行) と突き合わせる。

    2026-09-18に、原稿029〜041の範囲で **話数を原稿番号として書いてしまった**
    出典が450件見つかった（原稿030以降は「原稿番号−1」が話数のためずれる）。
    同じ取り違えが再発しないよう常時監視する。
    """
    見出し('H. 出典の原稿番号')
    本 = {}
    範囲 = {}
    for f in sorted(os.listdir(G)):
        m = re.match(r'^(\d{3})_', f)
        if not (m and f.endswith('.txt')):
            continue
        # 原稿133は `# 643` と空白入りで書かれている。原稿は無改変で保存するので
        # こちら側で両方を拾う。空白を許さないと133の出典が一件も検証されない。
        本文 = 読む(os.path.join(G, f))
        ns = [int(x) for x in re.findall(r'^#\s*(\d+)\s*$', 本文, re.M)]
        # 原稿071以降には `#316-327` という範囲形式のマーカーがある（345本）。
        # 展開しないと、その範囲を指す出典が全部「範囲外」として鳴る。
        for a_, b_ in re.findall(r'^#\s*(\d+)\s*-\s*(\d+)\s*$', 本文, re.M):
            a_, b_ = int(a_), int(b_)
            if 0 < b_ - a_ < 500:
                ns.extend(range(a_, b_ + 1))
        n = int(m.group(1))
        本[n] = {str(x) for x in ns}
        範囲[n] = (min(ns), max(ns)) if ns else None

    PAT = re.compile(r'(?<![\d/])(\d{3})((?:\s*|\s*新スレ\s*)#)(\d+)')
    一致 = 範囲内 = 0
    ずれ = []
    範囲外 = []
    for p in md一覧():
        t = 読む(p)
        for m in PAT.finditer(t):
            n, r = int(m.group(1)), m.group(3)
            if n not in 本:
                continue
            if r in 本[n]:
                一致 += 1
            elif (n + 1) in 本 and r in 本[n + 1]:
                ずれ.append((os.path.relpath(p, ROOT), n, r))
            else:
                rg = 範囲[n]
                # 新スレでレス番号が折り返す原稿(lo>hi)は範囲判定しない
                if rg and rg[0] <= rg[1] and rg[0] <= int(r) <= rg[1]:
                    範囲内 += 1
                else:
                    範囲外.append((os.path.relpath(p, ROOT), n, r))
    合計 = 一致 + 範囲内 + len(ずれ) + len(範囲外)
    print('出典 %d 件 / マーカーと一致 %d / 範囲内で妥当 %d' % (合計, 一致, 範囲内))
    print('範囲外（作者コメなど原稿外のレスを指している可能性） %d 件' % len(範囲外))
    for p, n, r in ずれ[:10]:
        NG('H', '出典が1つ前の原稿を指している: %s の %03d #%s は 原稿%03d のレス（話数と原稿番号の取り違え）' % (p, n, r, n + 1))
    if len(ずれ) > 10:
        NG('H', 'ほか %d 件の同種のずれ' % (len(ずれ) - 10))
    if not ずれ:
        print('原稿番号のずれ なし')


# ===== I. 00_概要_旧記録.md にしか無い引用（照合の進み具合） =====
def 検査I():
    """
    保全ファイル `00_概要_旧記録.md` の引用「…」のうち、他のノートのどこにも
    断片（8文字）すら無いものを数える。

    **これは「失われかけている情報の数」ではない。**2026-09-19に、この検査が
    挙げた分のうち36件（第1部関連27件＋第2部・第3部から9件）を個別に確認した
    ところ、**すべて事実としては他ノートに入っていた**。言い回しが違うだけで
    検出されている（例:「12才で親に並ぶ呪具師」と「12歳で父に並ぶ呪具師」、
    「来月が告示日、再来月が投票日」と「来月告示・再来月投票」）。

    したがってこの数は「旧記録にしか無い“言い回し”の数」。0を目指す必要は
    なく、旧記録は台詞の保管庫として残す。件数が**増えた**ときだけ、他ノート
    からの削除を疑って確認する。異常ではないので NG にはしない。
    """
    見出し('I. 00_概要_旧記録.md にしか無い言い回し')
    自分 = os.path.join(W, '00_概要_旧記録.md')
    if not os.path.exists(自分):
        print('保全ファイルは無い（移行完了なら正常）')
        return
    他 = [p for p in md一覧() if os.path.abspath(p) != os.path.abspath(自分)]
    全文 = re.sub(r'\s+', '', '\n'.join(読む(p) for p in 他))
    G8 = {全文[i:i + 8] for i in range(len(全文) - 7)}
    t = 読む(自分)
    節 = None
    未移行 = collections.Counter()
    総数 = 0
    for l in t.split('\n'):
        if l.startswith('## '):
            節 = l[3:]
        if not l.startswith('- **') or not 節:
            continue
        for x in dict.fromkeys(re.findall(r'[「『]([^「」『』\n]{8,60})[」』]', l)):
            総数 += 1
            if x in 全文:
                continue
            xs = re.sub(r'\s+', '', x)
            if not ({xs[i:i + 8] for i in range(len(xs) - 7)} & G8):
                未移行[節] += 1
    print('旧記録の引用 %d 件中、他ノートに8文字の断片も無いもの %d 件' % (総数, sum(未移行.values())))
    print('※ 事実の欠落数ではなく言い回しの差。増えたときだけ確認する')
    for s2, n in 未移行.most_common():
        print('  %3d  %s' % (n, s2[:52]))


# ===== J. 年表・あらすじが追えている原稿番号 =====
def 出典の原稿番号(行):
    """表の行の最終列から原稿番号だけを取り出す（#レス番号は捨てる）"""
    セル = 行.strip().strip('|').split('|')[-1]
    セル = re.sub(r'#\d+(?:-\d+)?', '', セル)
    return [int(x) for x in re.findall(r'\d{3}', セル)]


def 検査J(最新原稿):
    見出し('J. 年表・あらすじの収録範囲')
    本文 = 読む(os.path.join(W, '04_歴史・年表.md'))
    if '## 本編' not in 本文:
        NG('J', '04_歴史・年表.md に「## 本編」の節が無い'); return
    本編 = 本文[本文.index('## 本編'):]
    本編 = 本編[:本編.index('\n## ', 1)] if '\n## ' in 本編[1:] else 本編
    最大 = 0
    for ブロック in re.split(r'^### ', 本編, flags=re.M)[1:]:
        題 = ブロック.split('\n', 1)[0].strip()
        行 = [x for x in ブロック.split('\n')
              if x.startswith('| ') and not x.startswith('| 時期 |')]
        番号 = [n for x in 行 for n in 出典の原稿番号(x)]
        if 番号:
            最大 = max(最大, max(番号))
            print('  %-34s %3d行 / 原稿%03d〜%03d' % (題, len(行), min(番号), max(番号)))
        else:
            print('  %-34s %3d行' % (題, len(行)))
    print('年表の本編が収録している最新の原稿: %03d' % 最大)
    if 最新原稿 and 最大 < 最新原稿:
        NG('J', '年表が原稿%03dまでしか無い（原稿は%03dまである）。'
                '新しい話を年表へ入れ忘れている' % (最大, 最新原稿))

    d = os.path.join(W, '06_あらすじ')
    あ = 0
    for f in sorted(os.listdir(d)):
        if not f.endswith('.md') or f == 'README.md':
            continue
        番号 = [int(x) for x in re.findall(r'原稿(\d{3})', 読む(os.path.join(d, f)))]
        if 番号:
            あ = max(あ, max(番号))
            print('  %-34s 原稿%03d〜%03d' % (f, min(番号), max(番号)))
    print('あらすじが言及している最新の原稿: %03d' % あ)
    if 最新原稿 and あ < 最新原稿:
        NG('J', 'あらすじが原稿%03dまでしか無い（原稿は%03dまである）' % (あ, 最新原稿))


# ===== K. 個人ファイルの ## 見出し =====
時系列っぽい = re.compile(r'第\d+[部話章]|原稿\d{3}|\d+年前|番外|決戦|事件|襲撃|会議|防衛戦'
                     r'|^初期|^過去|^その後|^戦後|^最期|^末路|^蘇生後|^討伐|^決着')


def 見出しの例外():
    """02_人物/README.md の「`##` 見出しの例外」の表から読む"""
    rd = 読む(os.path.join(W, '02_人物', 'README.md'))
    許可 = set()
    for m in re.finditer(r'^\|\s*`([^`]+\.md)`\s*\|\s*`## ([^`]+)`', rd, re.M):
        許可.add((m.group(1), m.group(2).strip()))
    return 許可


def 検査K():
    見出し('K. 個人ファイルの ## 見出し')
    許可 = 見出しの例外()
    print('話題別と確認済みの例外: %d 件' % len(許可))
    n = 0
    使われた = set()
    for f in sorted(os.listdir(P)):
        if not f.endswith('.md'):
            continue
        for m in re.finditer(r'(?m)^## (.+)$', 読む(os.path.join(P, f))):
            題 = m.group(1).strip()
            if not 時系列っぽい.search(題):
                continue
            if (f, 題) in 許可:
                使われた.add((f, 題))
                continue
            n += 1
            NG('K', '出来事名に見える ## 見出し: %s の `## %s`'
                    '（`## 時系列記録` の下へ `### ` で入れるか、'
                    '話題別なら 02_人物/README.md の例外の表へ足す）' % (f, 題))
    for k in sorted(許可 - 使われた):
        NG('K', '例外の表に書いてあるが実物が無い: %s の `## %s`' % k)
    if not n:
        print('出来事名に見える ## 見出し なし')


def スナップショット対応表():
    """`07_読書スナップショット/README.md` の対応表から
    {ファイル名: (開始原稿, 終了原稿)} を読む。
    許可リストをスクリプト内に持たないのは、ノート側を更新し忘れたときに
    鳴らすため（「似た名前でも統合してはいけない組」と同じ設計）。"""
    p = os.path.join(S, 'README.md')
    if not os.path.exists(p):
        return {}
    t = 読む(p)
    見出し名 = '## ★ ファイル名と収録原稿の対応表'
    if 見出し名 not in t:
        return {}
    節 = t.split(見出し名, 1)[1].split('\n## ', 1)[0]
    出 = {}
    for 行 in 節.split('\n'):
        if not 行.startswith('|') or 行.startswith('|--'):
            continue
        セル = [x.strip() for x in 行.strip().strip('|').split('|')]
        if len(セル) < 2:
            continue
        m = re.match(r'^`(\d{3}(?:-\d{3})?\.md)`$', セル[0])
        if not m:
            continue
        r = re.search(r'(\d{3})(?:〜(\d{3}))?', セル[1].replace('*', ''))
        if not r:
            continue
        a = int(r.group(1))
        b = int(r.group(2) or r.group(1))
        出[m.group(1)] = (a, b)
    return 出


def 検査L(最新原稿):
    見出し('L. 読書スナップショットの収録範囲')
    表 = スナップショット対応表()
    if not 表:
        NG('L', '`07_読書スナップショット/README.md` に'
                '「★ ファイル名と収録原稿の対応表」が見つからない')
        return
    実物 = set(f for f in os.listdir(S)
               if re.match(r'^\d{3}(-\d{3})?\.md$', f))
    print('対応表 %d 行 / 実ファイル %d 件' % (len(表), len(実物)))
    for f in sorted(実物 - set(表)):
        NG('L', 'スナップショットが対応表に無い: %s'
                '（07_読書スナップショット/README.md の表へ行を足す）' % f)
    for f in sorted(set(表) - 実物):
        NG('L', '対応表にあるが実ファイルが無い: %s' % f)

    覆う = {}
    for f, (a, b) in 表.items():
        if f not in 実物:
            continue
        for n in range(a, b + 1):
            覆う.setdefault(n, []).append(f)
    上限 = 最新原稿 or (max(覆う) if 覆う else 0)
    欠け = [n for n in range(1, 上限 + 1) if n not in 覆う]
    if 欠け:
        NG('L', 'どのスナップショットにも入っていない原稿: %s'
                % ', '.join('%03d' % n for n in 欠け))
    else:
        print('原稿001〜%03d は対応表で漏れなく覆われている' % 上限)
    重なり = sorted(n for n, v in 覆う.items() if len(v) > 1)
    if 重なり:
        print('複数のファイルに入っている原稿: %s（早い時点のチェックポイントは残す方針）'
              % ', '.join('%03d' % n for n in 重なり))


def main():
    放棄 = 放棄した連番()
    最新原稿 = 検査A(放棄)
    消えた名 = 統合表()
    検査B(消えた名)
    検査C(別人表())
    用語数 = 検査D()
    if 最新原稿:
        検査E(最新原稿)
    個人数 = len([f for f in os.listdir(P) if f.endswith('.md')])
    原稿数 = len([f for f in os.listdir(G) if f.endswith('.txt') and re.match(r'^\d{3}_', f)])
    残る放棄 = [n for n in 放棄
                if not os.path.exists(os.path.join(G, '%03d_' % n)) and
                not any(f.startswith('%03d_' % n) for f in os.listdir(G))]
    次の連番 = min(残る放棄) if 残る放棄 else 原稿数 + 1
    検査F(個人数, 用語数, 原稿数, 次の連番)
    検査G()
    検査H()
    検査I()
    検査J(最新原稿)
    検査K()
    検査L(最新原稿)

    見出し('結果')
    if 参考:
        for s in 参考:
            print('参考:', s)
    if not 問題:
        print('問題なし')
        return 0
    print('要確認 %d 件' % len(問題))
    for s in 問題:
        print(' ', s)
    return 1

if __name__ == '__main__':
    sys.exit(main())
