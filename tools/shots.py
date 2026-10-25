"""Render Colab-style greyscale screenshots of notebook cells (code + outputs)."""
import base64, io, os, nbformat
from PIL import Image, ImageDraw, ImageFont
from pygments import lex
from pygments.lexers import PythonLexer
from pygments.token import Keyword, String, Comment, Number, Name, Operator

NB = '2667213_Rachel_Elizabeth_Joy_Diabetes_Regression.ipynb'
nb = nbformat.read(NB, 4)
os.makedirs('shots', exist_ok=True)
FD = '/usr/share/fonts/truetype/dejavu/'
S = 26
F = ImageFont.truetype(FD + 'DejaVuSansMono.ttf', S)
FB = ImageFont.truetype(FD + 'DejaVuSansMono-Bold.ttf', S)
FI = ImageFont.truetype(FD + 'DejaVuSansMono-Oblique.ttf', S) if os.path.exists(FD + 'DejaVuSansMono-Oblique.ttf') else F
FS = ImageFont.truetype(FD + 'DejaVuSans.ttf', 22)
LH = int(S * 1.45); CW = F.getbbox('M')[2]; PAD = 24; GUT = 70; W = 1900

def style(tok):
    if tok in Keyword or tok in Name.Builtin: return FB, (0, 0, 0)
    if tok in Comment: return FI, (110, 110, 110)
    if tok in String: return F, (70, 70, 70)
    if tok in Number: return F, (40, 40, 40)
    return F, (20, 20, 20)

def wrap(lines, maxc):
    out = []
    for l in lines:
        while len(l) > maxc: out.append(l[:maxc]); l = '    ' + l[maxc:]
        out.append(l)
    return out

def code_img(src, exec_no):
    lines = src.split('\n'); maxc = (W - GUT - 3 * PAD) // CW
    h = PAD * 2 + LH * len(wrap(lines, maxc))
    im = Image.new('RGB', (W, h), (245, 245, 245)); d = ImageDraw.Draw(im)
    d.rectangle([0, 0, W - 1, h - 1], outline=(200, 200, 200), width=2)
    d.text((14, PAD), f'[{exec_no}]', font=FS, fill=(120, 120, 120))
    y = PAD; x0 = GUT + PAD
    for line in lines:
        x = x0; col = 0
        for tok, val in lex(line, PythonLexer()):
            val = val.rstrip('\n')
            f, c = style(tok)
            for ch in val:
                if col >= maxc: y += LH; x = x0 + 4 * CW; col = 4
                d.text((x, y), ch, font=f, fill=c); x += CW; col += 1
        y += LH
    return im

def text_img(txt):
    maxc = (W - 2 * PAD - GUT) // CW
    lines = wrap(txt.rstrip('\n').split('\n'), maxc)
    im = Image.new('RGB', (W, PAD * 2 + LH * len(lines)), 'white'); d = ImageDraw.Draw(im)
    for i, l in enumerate(lines): d.text((GUT + PAD, PAD + i * LH), l, font=F, fill=(0, 0, 0))
    return im

def trim_text(im):
    from PIL import ImageOps
    bb = ImageOps.invert(im).getbbox()
    return im.crop((0, 0, min(W, bb[2] + GUT), im.height)) if bb else im

def outputs(cell, want_images=True, want_text=True):
    ims = []
    for o in cell.outputs:
        if o.output_type == 'stream' and want_text: ims.append(text_img(o.text))
        elif 'data' in o:
            if 'image/png' in o['data'] and want_images:
                p = Image.open(io.BytesIO(base64.b64decode(o['data']['image/png']))).convert('RGB')
                k = min(1, (W - 2 * PAD) / p.width); p = p.resize((int(p.width * k), int(p.height * k)))
                c = Image.new('RGB', (p.width + 2 * PAD, p.height + 2 * PAD), 'white'); c.paste(p, (PAD, PAD)); ims.append(c)
            elif 'text/plain' in o['data'] and want_text: ims.append(text_img(o['data']['text/plain']))
    return ims

def stack(ims, name, max_h=None):
    h = sum(i.height for i in ims); w = max(i.width for i in ims)
    out = Image.new('RGB', (w, h), 'white'); y = 0
    for i in ims: out.paste(i, ((w - i.width) // 2 if i.width < W else 0, y)); y += i.height
    ImageDraw.Draw(out).rectangle([0, 0, w - 1, h - 1], outline=(170, 170, 170), width=2)
    out.save(f'shots/{name}.png'); print(name, out.size)

def shot(name, idx, code=True, imgs=True, text=True, src_lines=None, text_filter=None):
    c = nb.cells[idx]; parts = []
    if code:
        src = c.source if src_lines is None else '\n'.join(c.source.split('\n')[src_lines[0]:src_lines[1]])
        parts.append(code_img(src, c.execution_count))
    outs = outputs(c, imgs, text)
    if text_filter: outs = [outs[i] for i in text_filter]
    if not code: outs = [trim_text(o) if o.width == W else o for o in outs]
    stack(parts + outs, name)

code_cells = [i for i, c in enumerate(nb.cells) if c.cell_type == 'code']
print({i: nb.cells[i].source.split('\n')[0][:60] for i in code_cells})

# ---- main report ----
shot('s01_load', 5)
shot('s02_target', 8, code=False)
shot('s03_corr', 9, code=False, text=False)
shot('s04_feat_hist', 10, code=False)
shot('s05_scatter', 11, code=False)
shot('s06_collinear', 12, code=False)
shot('s07_prep_code', 16, text=False)
shot('s08_split', 15)
shot('s09_tune_linear', 19)
shot('s10_tune_trees', 20)
shot('s11_results', 22)
shot('s12_compare', 23, code=False)
shot('s13_final_test', 25)
shot('s14_focus_code', 27)
shot('s15_paths', 28, code=False)
shot('s16_norms', 29, code=False)
shot('s17_lasso_drop', 30, code=False)
shot('s18_resid', 33, code=False)
shot('s19_importance', 34, code=False)
shot('s20_worst', 35, code=False)
# ---- appendix ----
shot('a1_setup', 2, imgs=False)
shot('a2_feature_check', 17)
shot('a3_paths_code', 28, imgs=False)
shot('a4_drop_code', 30, text=False)
shot('a5_resid_code', 33, imgs=False, text=False)
shot('a6_importance_code', 34, imgs=False)
shot('b2_describe', 6, text_filter=[0])
shot('b3_cvcurve', 31, code=False)
# run-all: title cell rendered + final cell
title = nb.cells[0].source.replace('**', '').replace('# ', '').replace('`', '')
t = text_img(title)
c = nb.cells[37]
stack([t, code_img(c.source, c.execution_count)] + outputs(c), 'b1_runall')
