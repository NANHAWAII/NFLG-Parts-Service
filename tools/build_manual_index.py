#!/usr/bin/env python3
"""
Build a searchable parts index from an NFLG Spare Parts Manual PDF.

    pip install pymupdf
    python build_manual_index.py "NFJ1175 Spare Parts Manual.pdf" NFJ1175 > ../data/manual-index/NFJ1175.json

Output: {"model","source","pages","figures":[{fig,name,illus,page}],
         "parts":[{pn,rev,en,zh,qty,fig,item,page,ref}]}
`page` is the PDF page number (1-based), so the portal can open <manual>.pdf#page=N.
Parsing is layout-based (word x/y positions); NFLG manuals share one template.
"""
import json, re, sys
import pymupdf

FIG_RE = re.compile(r'^\d{2}-\d{2}(-\d{2})?$')
PN_RE = re.compile(r'^\d{10}$')

def group_lines(words, tol=3):
    lines = {}
    for w in words:
        key = None
        for k in lines:
            if abs(k - w['top']) <= tol: key = k; break
        lines.setdefault(key if key is not None else w['top'], []).append(w)
    return lines

def parse(pdf_path, model):
    pdf = pymupdf.open(pdf_path)
    figures, parts = [], []
    for pi, page in enumerate(pdf):
        pno = pi + 1
        words = [{'x0': w[0], 'top': w[1], 'text': w[4]} for w in page.get_text('words')]
        if not words: continue
        text = {w['text'] for w in words}
        # ---- figure header ----
        fig = illus = None; name_words = []
        for w in words:
            if FIG_RE.match(w['text']) and 90 < w['top'] < 105: fig = w['text']
            if w['text'].upper().startswith('M') and '-NF' in w['text'].upper() and 75 < w['top'] < 90: illus = w['text']
        if not fig: continue
        # name: words on the Name line (top ~55-65) between "Name :" and "Machine"
        machine_x = min([w['x0'] for w in words if w['text'] == 'Machine' and 50 < w['top'] < 70] or [9999])
        for w in words:
            if 50 < w['top'] < 70 and w['x0'] < machine_x and w['text'] not in ('Name', ':', '名称', '机型'):
                name_words.append(w)
        name = ' '.join(w['text'] for w in sorted(name_words, key=lambda w: (round(w['top']/5), w['x0']))).strip()
        hdr = {w['text']: w['x0'] for w in words if 110 < w['top'] < 125 and w['text'] in ('Item', 'Part', 'Rev', 'Description', 'Qty')}
        if not illus and 'Part' not in hdr: continue   # table-of-contents pages also carry figure-like numbers
        if not any(f['fig'] == fig for f in figures):
            figures.append({'fig': fig, 'name': name, 'illus': illus, 'page': pno})
        # ---- column anchors from header row ----
        if 'Part' not in hdr or 'Description' not in hdr: continue
        x_item, x_part, x_rev, x_desc, x_qty = hdr.get('Item', hdr['Part'] - 35), hdr['Part'], hdr.get('Rev', hdr['Part'] + 112), hdr['Description'], hdr.get('Qty', 530)
        # ---- part rows ----
        anchors = [w for w in words if PN_RE.match(w['text']) and abs(w['x0'] - x_part) < 8 and w['top'] > 130]
        for a in anchors:
            t = a['top']
            near = lambda w, lo, hi: lo <= w['top'] - t <= hi
            item = next((w['text'] for w in words if abs(w['x0'] - x_item) < 12 and near(w, -4, 4) and w['text'].isdigit()), '')
            rev = next((w['text'] for w in words if abs(w['x0'] - x_rev) < 8 and near(w, -4, 4) and w['text'].isdigit()), '')
            qty = next((w['text'] for w in words if w['x0'] > x_qty - 15 and near(w, -4, 4) and w['text'].isdigit()), '')
            desc = [w for w in words if x_desc - 5 <= w['x0'] < x_qty - 15 and near(w, -13, 13) and not w['text'].startswith('详细请见')]
            # visual lines: cluster tops within 4pt so EN/ZH words on one line sort left-to-right
            lines = []
            for w in sorted(desc, key=lambda w: w['top']):
                if lines and abs(lines[-1][0] - w['top']) <= 4: lines[-1][1].append(w)
                else: lines.append([w['top'], [w]])
            desc = [w for _, ws in lines for w in sorted(ws, key=lambda w: w['x0'])]
            s = ' '.join(w['text'] for w in desc)
            en, _, zh = s.partition('::')
            if not _:  # no separator: split on first CJK char
                m = re.search(r'[一-鿿]', s)
                en, zh = (s[:m.start()], s[m.start():]) if m else (s, '')
            # ZH line may sit above the EN line: strip stray CJK from en and move to zh
            cjk = re.findall(r'[一-鿿][^\sA-Za-z]*', en)
            if cjk and not zh.strip(): zh = ''.join(cjk)
            en = re.sub(r'[一-鿿][^\sA-Za-z]*', '', en)
            ref = next((w['text'].replace('详细请见', '') for w in words if w['text'].startswith('详细请见') and near(w, 0, 30) and abs(w['x0'] - x_desc) < 8), '')
            parts.append({'pn': a['text'], 'rev': rev, 'en': ' '.join(en.split()), 'zh': ' '.join(zh.split()),
                          'qty': qty, 'fig': fig, 'item': item, 'page': pno, 'ref': ref})
    return {'model': model, 'source': pdf_path.split('/')[-1], 'pages': len(pdf), 'figures': figures, 'parts': parts}

if __name__ == '__main__':
    if len(sys.argv) < 3: sys.exit(__doc__)
    json.dump(parse(sys.argv[1], sys.argv[2]), sys.stdout, ensure_ascii=False, separators=(',', ':'))
