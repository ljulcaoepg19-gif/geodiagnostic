"""
GeoDiagnostic v1.0.0 — Reporte Técnico Profesional
Autor: Lenin E. Julca — ljulcao_epg19@unc.edu.pe
Tipografía: STIX General (fuente científica con soporte completo de tildes)
"""
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import cm
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY, TA_RIGHT
from reportlab.platypus import (Paragraph, Spacer, PageBreak, Table,
                                 TableStyle, BaseDocTemplate,
                                 Frame, PageTemplate, NextPageTemplate,
                                 KeepTogether)
from reportlab.graphics.shapes import (Drawing, Rect, String, Line,
                                        Circle, PolyLine, Polygon)
from reportlab.graphics import renderPDF
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase.pdfmetrics import registerFontFamily
from datetime import datetime
import os, math

# ── Registrar fuentes STIX con soporte completo de tildes ─────────────────────
_STIX = '/usr/local/lib/python3.12/dist-packages/matplotlib/mpl-data/fonts/ttf'
_MONO = '/usr/share/fonts/truetype/dejavu'
try:
    pdfmetrics.registerFont(TTFont('STIX',    f'{_STIX}/STIXGeneral.ttf'))
    pdfmetrics.registerFont(TTFont('STIX-B',  f'{_STIX}/STIXGeneralBol.ttf'))
    pdfmetrics.registerFont(TTFont('STIX-I',  f'{_STIX}/STIXGeneralItalic.ttf'))
    pdfmetrics.registerFont(TTFont('STIX-BI', f'{_STIX}/STIXGeneralBolIta.ttf'))
    pdfmetrics.registerFont(TTFont('Mono',    f'{_MONO}/DejaVuSansMono.ttf'))
    registerFontFamily('STIX', normal='STIX', bold='STIX-B',
                       italic='STIX-I', boldItalic='STIX-BI')
    FN = 'STIX'; FNB = 'STIX-B'; FNI = 'STIX-I'; FNBI = 'STIX-BI'
except Exception:
    FN = 'Helvetica'; FNB = 'Helvetica-Bold'
    FNI = 'Helvetica-Oblique'; FNBI = 'Helvetica-BoldOblique'

# ── Paleta de colores ─────────────────────────────────────────────────────────
CV   = colors.HexColor('#1B5E20')
CVM  = colors.HexColor('#2E7D32')
CVL  = colors.HexColor('#388E3C')
CVC  = colors.HexColor('#E8F5E9')
CVF  = colors.HexColor('#F1F8F2')
CAZ  = colors.HexColor('#0D47A1')
CAZM = colors.HexColor('#1565C0')
CAZC = colors.HexColor('#E3F2FD')
CAZF = colors.HexColor('#F5F9FF')
CNR  = colors.HexColor('#E65100')
CNRC = colors.HexColor('#FFF3E0')
CRO  = colors.HexColor('#B71C1C')
CROC = colors.HexColor('#FFEBEE')
CAM  = colors.HexColor('#F57F17')
CAMC = colors.HexColor('#FFF8E1')
CGR  = colors.HexColor('#212121')
CGRM = colors.HexColor('#424242')
CGRL = colors.HexColor('#757575')
CGRC = colors.HexColor('#F5F5F5')
CGRF = colors.HexColor('#FAFAFA')
BL   = colors.white

COLORES_DW = {
    'Agua':'#419BDF','Árboles':'#397D49','Césped/Pasto':'#88B053',
    'Veg. inundada':'#7A87C6','Cultivos':'#E49635','Arbustos':'#DFC35A',
    'Construido':'#C4281B','Suelo desnudo':'#A59B8F','Nieve/Hielo':'#B39FE1',
}

AUTOR   = 'Lenin E. Julca'
CORREO  = 'ljulcao_epg19@unc.edu.pe'
YAPE    = '+51 976 742 241'
VERSION = 'GeoDiagnostic v1.0.0'

# ── Estilos tipográficos ──────────────────────────────────────────────────────
def _E():
    return {
        'titulo': ParagraphStyle('titulo', fontName=FNB, fontSize=15,
            textColor=CV, spaceBefore=10, spaceAfter=4, leading=19),
        'h2':     ParagraphStyle('h2', fontName=FNB, fontSize=12,
            textColor=CAZ, spaceBefore=8, spaceAfter=3, leading=16),
        'h3':     ParagraphStyle('h3', fontName=FNB, fontSize=11,
            textColor=CGRM, spaceBefore=6, spaceAfter=3, leading=14),
        'body':   ParagraphStyle('body', fontName=FN, fontSize=11,
            textColor=CGR, spaceBefore=2, spaceAfter=4, leading=16,
            alignment=TA_JUSTIFY),
        'nota':   ParagraphStyle('nota', fontName=FNI, fontSize=9.5,
            textColor=CGRL, spaceBefore=2, spaceAfter=3, leading=13,
            leftIndent=8),
        'tabla_h':ParagraphStyle('tabla_h', fontName=FNB, fontSize=10,
            textColor=BL, leading=13),
        'tabla_v':ParagraphStyle('tabla_v', fontName=FN, fontSize=10,
            textColor=CGR, leading=14),
        'tabla_vb':ParagraphStyle('tabla_vb', fontName=FNB, fontSize=10,
            textColor=CAZ, leading=14),
        'kpi_val':ParagraphStyle('kpi_val', fontName=FNB, fontSize=20,
            textColor=CGR, leading=24, alignment=TA_CENTER),
        'kpi_lbl':ParagraphStyle('kpi_lbl', fontName=FN, fontSize=9.5,
            textColor=CGRL, leading=13, alignment=TA_CENTER),
        'kpi_est':ParagraphStyle('kpi_est', fontName=FNB, fontSize=9,
            textColor=CV, leading=11, alignment=TA_CENTER),
        'centro': ParagraphStyle('centro', fontName=FN, fontSize=10,
            textColor=CGR, alignment=TA_CENTER),
        'fig_cap':ParagraphStyle('fig_cap', fontName=FNI, fontSize=9,
            textColor=CGRL, alignment=TA_CENTER, spaceBefore=2, spaceAfter=6),
    }

# ── Cabecera de sección estilo técnico ────────────────────────────────────────
_fig_num = [0]
_tab_num = [0]

def cabecera_seccion(num, titulo, fuente=''):
    d = Drawing(15*cm, 26)
    # fondo número
    d.add(Rect(0, 0, 1.1*cm, 26, fillColor=CAZ, strokeColor=None))
    d.add(String(0.55*cm, 7, str(num),
                 fontSize=12, fontName=FNB, fillColor=BL, textAnchor='middle'))
    # fondo título
    d.add(Rect(1.1*cm, 0, 15*cm-1.1*cm, 26, fillColor=CV, strokeColor=None))
    d.add(String(1.4*cm, 7, titulo,
                 fontSize=11, fontName=FNB, fillColor=BL, textAnchor='start'))
    if fuente:
        d.add(String(15*cm-0.2*cm, 7, fuente,
                     fontSize=7.5, fontName=FNI, fillColor=colors.HexColor('#A5D6A7'),
                     textAnchor='end'))
    return d

def fig_caption(texto):
    _fig_num[0] += 1
    return Paragraph(f'<i>Figura {_fig_num[0]}. {texto}</i>', _E()['fig_cap'])

def tab_caption(texto):
    _tab_num[0] += 1
    return Paragraph(f'<i>Tabla {_tab_num[0]}. {texto}</i>', _E()['fig_cap'])

# ── Tabla estilo booktabs ─────────────────────────────────────────────────────
def tabla_booktabs(filas_data, headers=None, col_w=None, num_cols_right=0):
    """filas_data: lista de listas de strings. headers: lista de strings."""
    E = _E()
    rows = []
    if headers:
        rows.append([Paragraph(h, E['tabla_h']) for h in headers])
    for i, fila in enumerate(filas_data):
        row = []
        for j, c in enumerate(fila):
            st = E['tabla_vb'] if (j >= len(fila)-num_cols_right and num_cols_right>0) else E['tabla_v']
            row.append(Paragraph(str(c), st))
        rows.append(row)
    if not rows: return Spacer(1, 0.2*cm)
    if col_w is None:
        n = len(rows[0])
        col_w = [15*cm/n]*n
    t = Table(rows, colWidths=col_w, repeatRows=1 if headers else 0)
    cmds = [
        # Estilo booktabs
        ('LINEABOVE',    (0,0), (-1,0),  1.2, CGR),
        ('LINEBELOW',    (0,0), (-1,0),  0.5, CGRL),
        ('LINEBELOW',    (0,-1),(-1,-1), 1.0, CGR),
        ('GRID',         (0,1), (-1,-2), 0.3, colors.HexColor('#E0E0E0')),
        ('ROWBACKGROUNDS',(0,1),(-1,-1), [BL, CGRF]),
        ('VALIGN',       (0,0), (-1,-1), 'MIDDLE'),
        ('LEFTPADDING',  (0,0), (-1,-1), 7),
        ('RIGHTPADDING', (0,0), (-1,-1), 7),
        ('TOPPADDING',   (0,0), (-1,-1), 5),
        ('BOTTOMPADDING',(0,0), (-1,-1), 5),
    ]
    if headers:
        cmds.append(('BACKGROUND', (0,0), (-1,0), colors.HexColor('#0D3B1F')))
    t.setStyle(TableStyle(cmds))
    return t

def tabla_kv_pro(datos, col_w=None):
    """tabla kv con col izq verde + col der blanca."""
    E = _E()
    col_w = col_w or [6.5*cm, 8.5*cm]
    rows  = []
    for i, (k, v) in enumerate(datos.items()):
        if str(k).startswith('_'): continue
        rows.append([
            Paragraph(str(k), E['tabla_h']),
            Paragraph(str(v), E['tabla_v'])
        ])
    if not rows: return Spacer(1, 0.2*cm)
    t = Table(rows, colWidths=col_w)
    cmds = [
        ('LINEABOVE',     (0,0),(-1,0),  1.0, CV),
        ('LINEBELOW',     (0,-1),(-1,-1),1.0, CV),
        ('GRID',          (0,0),(-1,-1), 0.3, colors.HexColor('#CFD8DC')),
        ('VALIGN',        (0,0),(-1,-1), 'MIDDLE'),
        ('TOPPADDING',    (0,0),(-1,-1), 5),
        ('BOTTOMPADDING', (0,0),(-1,-1), 5),
        ('LEFTPADDING',   (0,0),(-1,-1), 8),
        ('ROWBACKGROUNDS',(1,0),(1,-1),  [BL, CGRF]),
    ]
    for i in range(len(rows)):
        cmds.append(('BACKGROUND', (0,i),(0,i), CV if i%2==0 else CVM))
    t.setStyle(TableStyle(cmds))
    return t

# ── Tarjeta KPI ───────────────────────────────────────────────────────────────
def kpi_card(valor, label, estado, color_sem, ancho=3.5*cm, alto=2.2*cm):
    E = _E()
    d = Drawing(ancho, alto)
    # Fondo
    d.add(Rect(0, 0, ancho, alto, fillColor=BL,
               strokeColor=color_sem, strokeWidth=1.5, rx=4))
    # Barra superior de color semáforo
    d.add(Rect(0, alto-0.3*cm, ancho, 0.3*cm,
               fillColor=color_sem, strokeColor=None, rx=4))
    # Valor grande
    d.add(String(ancho/2, alto*0.5,  str(valor),
                 fontSize=16, fontName=FNB, fillColor=CGR, textAnchor='middle'))
    # Label
    d.add(String(ancho/2, alto*0.25, label[:20],
                 fontSize=7.5, fontName=FN, fillColor=CGRL, textAnchor='middle'))
    # Estado
    d.add(String(ancho/2, alto*0.08, estado,
                 fontSize=7, fontName=FNB, fillColor=color_sem, textAnchor='middle'))
    return d

# ── Gráfico barras profesional ────────────────────────────────────────────────
def grafico_barras(datos, titulo, subtitulo='', ancho=14*cm, alto=6*cm, eje_y_label=''):
    """datos: [(label, valor, color_hex), ...]"""
    if not datos: return Spacer(1, 0.5*cm)
    PAL = ['#1B5E20','#0D47A1','#B71C1C','#E65100','#4A148C','#006064','#F57F17','#880E4F']
    d      = Drawing(ancho, alto + 2.8*cm)
    BX     = 68; BH = alto - 50
    BW_tot = ancho - BX - 12
    n      = len(datos)
    bw     = min(BW_tot / max(n, 1) * 0.65, 38)
    gap    = BW_tot / max(n, 1) * 0.35
    vals   = [float(v) for _, v, *_ in datos]
    mx     = max(vals) if vals else 1
    mn     = min(vals) if vals else 0

    # Si hay negativos (ej. BSI) → cero centrado
    tiene_neg = mn < -0.01
    if tiene_neg:
        span = max(abs(mx), abs(mn)) * 1.25 or 1
        BY   = 32 + BH * abs(mn) / (abs(mx) + abs(mn) or 1)
    else:
        span = mx * 1.15 if mx > 0 else 1
        BY   = 32

    def bh_from_val(v):
        if tiene_neg:
            return BH * float(v) / (abs(mx) + abs(mn) or 1)
        else:
            return BH * float(v) / span

    # Líneas guía
    guide_tks = [-0.75,-0.5,-0.25,0,0.25,0.5,0.75,1.0] if tiene_neg else [0.25,0.5,0.75,1.0]
    for tk in guide_tks:
        if tiene_neg:
            y  = BY + BH * tk
            tv = (abs(mx)+abs(mn)) * tk
        else:
            y  = BY + BH * tk
            tv = span * tk
        if 28 < y < BY + BH + 4:
            d.add(Line(BX, y, BX+BW_tot, y,
                       strokeColor=colors.HexColor('#E0E0E0'), strokeWidth=0.5))
            lbl = f'{tv:.2f}' if abs(tv)<1 else (f'{tv:.1f}' if abs(tv)<100 else f'{int(tv)}')
            d.add(String(BX-5, y-3.5, lbl,
                         fontSize=6.5, fontName=FN, fillColor=CGRL, textAnchor='end'))

    d.add(Line(BX, 32, BX, 32+BH, strokeColor=CGRL, strokeWidth=0.6))
    d.add(Line(BX, BY, BX+BW_tot, BY, strokeColor=CGRL, strokeWidth=0.6))
    if tiene_neg:
        d.add(Line(BX, BY, BX+BW_tot, BY,
                   strokeColor=colors.HexColor('#90A4AE'), strokeWidth=1.0))

    for i, item in enumerate(datos):
        lbl = item[0]; val = float(item[1])
        col  = colors.HexColor(item[2]) if len(item)>2 else colors.HexColor(PAL[i%len(PAL)])
        bx_i = BX + i*(bw+gap) + gap/2
        bh_i = bh_from_val(val)
        rect_y = BY if val >= 0 else BY + bh_i
        rect_h = max(abs(bh_i), 1)
        d.add(Rect(bx_i, rect_y, bw, rect_h, fillColor=col, strokeColor=None, rx=2))

        vs = f'{val:.2f}' if abs(val)<1 else (f'{val:.1f}' if abs(val)<100 else f'{int(val)}')
        nudge  = max(5, rect_h*0.10)
        lbl_y  = rect_y + rect_h + nudge if val >= 0 else rect_y - nudge - 8
        d.add(String(bx_i+bw/2, lbl_y, vs,
                     fontSize=7, fontName=FNB, fillColor=CGRM, textAnchor='middle'))
        d.add(String(bx_i+bw/2, 18, lbl[:14],
                     fontSize=6.5, fontName=FN, fillColor=CGRM, textAnchor='middle'))

    d.add(String(ancho/2, alto+24, titulo,
                 fontSize=9.5, fontName=FNB, fillColor=CGR, textAnchor='middle'))
    if subtitulo:
        d.add(String(ancho/2, alto+13, subtitulo,
                     fontSize=7.5, fontName=FNI, fillColor=CGRL, textAnchor='middle'))
    if eje_y_label:
        d.add(String(8, 32+BH/2, eje_y_label,
                     fontSize=7, fontName=FNI, fillColor=CGRL, textAnchor='middle'))
    return d

# ── Gráfico líneas con área sombreada + puntos ────────────────────────────────
def grafico_lineas(datos, titulo, subtitulo='', ancho=14*cm, alto=5.5*cm,
                   color='#1565C0', color_area='#E3F2FD', eje_y_label=''):
    if not datos or len(datos) < 2: return Spacer(1, 0.5*cm)
    MESES = ['Ene','Feb','Mar','Abr','May','Jun','Jul','Ago','Sep','Oct','Nov','Dic']
    d    = Drawing(ancho, alto + 2*cm)
    BX   = 62; BY = 30; BH = alto - 25
    BW   = ancho - BX - 10
    n    = len(datos)
    vals = [float(v) for v in datos]
    mx   = max(vals) if vals else 1
    mn_v = min(vals) if vals else 0
    rng  = mx - mn_v if mx != mn_v else 1

    # Líneas guía
    for tk in [0, 0.25, 0.5, 0.75, 1.0]:
        y  = BY + BH * tk
        tv = mn_v + rng * tk
        d.add(Line(BX, y, BX + BW, y,
                   strokeColor=colors.HexColor('#EEEEEE'), strokeWidth=0.5))
        lbl = f'{tv:.1f}' if abs(tv) < 100 else f'{int(tv)}'
        d.add(String(BX - 5, y - 3.5, lbl,
                     fontSize=6.5, fontName=FN, fillColor=CGRL, textAnchor='end'))

    # Coordenadas de los puntos
    pts = []
    for i, v in enumerate(vals):
        x = BX + i * BW / (n - 1)
        y = BY + BH * (float(v) - mn_v) / rng
        pts.append((x, y))

    # Área sombreada bajo la curva
    poly_pts = [BX, BY]
    for x, y in pts:
        poly_pts += [x, y]
    poly_pts += [BX + BW, BY]
    d.add(Polygon(poly_pts, fillColor=colors.HexColor(color_area),
                  strokeColor=None))

    # Línea de la curva
    line_pts = []
    for x, y in pts:
        line_pts += [x, y]
    d.add(PolyLine(line_pts, strokeColor=colors.HexColor(color),
                   strokeWidth=1.8))

    # Puntos en cada mes
    for i, (x, y) in enumerate(pts):
        d.add(Circle(x, y, 3.2, fillColor=BL,
                     strokeColor=colors.HexColor(color), strokeWidth=1.2))
        # Etiqueta eje X
        lbl = MESES[i] if i < len(MESES) else str(i+1)
        d.add(String(x, BY - 10, lbl,
                     fontSize=6.5, fontName=FN, fillColor=CGRM, textAnchor='middle'))

    # Ejes
    d.add(Line(BX, BY, BX, BY + BH, strokeColor=CGRL, strokeWidth=0.6))
    d.add(Line(BX, BY, BX + BW, BY, strokeColor=CGRL, strokeWidth=0.6))

    # Título
    d.add(String(ancho/2, alto + 13, titulo,
                 fontSize=9.5, fontName=FNB, fillColor=CGR, textAnchor='middle'))
    if subtitulo:
        d.add(String(ancho/2, alto + 4, subtitulo,
                     fontSize=7.5, fontName=FNI, fillColor=CGRL, textAnchor='middle'))
    return d

# ── Gráfica multiserie — evolución mensual de los 7 índices espectrales ───────
def grafico_multiserie_indices(res, titulo, subtitulo='', ancho=14*cm, alto=6*cm):
    """
    res: dict de resultados['vegetacion'] con claves NDVI_Mes_01..12, etc.
    Dibuja 7 líneas de colores (una por índice) sobre 12 meses.
    """
    INDICES = ['NDVI','EVI','SAVI','NDWI','NDMI','NBR','BSI']
    COLORES = ['#1B5E20','#0D47A1','#388E3C','#1565C0','#6A1B9A','#00695C','#BF360C']
    MESES   = ['Ene','Feb','Mar','Abr','May','Jun','Jul','Ago','Sep','Oct','Nov','Dic']
    LEGEND_W = 2.8*cm
    d        = Drawing(ancho, alto + 2.5*cm)
    BX = 55; BY = 28; BH = alto - 22
    BW = ancho - BX - LEGEND_W - 8

    # Recopilar datos mensuales por índice
    series = {}
    for idx in INDICES:
        vals = []
        for m in range(1, 13):
            v = res.get(f'{idx}_Mes_{m:02d}', None)
            vals.append(float(v) if v is not None else None)
        series[idx] = vals

    # Rango global (ignorar None)
    all_v = [v for vs in series.values() for v in vs if v is not None]
    if not all_v:
        return Spacer(1, 0.5*cm)
    mn_g = min(all_v); mx_g = max(all_v)
    rng  = mx_g - mn_g if mx_g != mn_g else 1
    mn_g -= rng * 0.08
    mx_g += rng * 0.08
    rng   = mx_g - mn_g

    def ys(v):
        return BY + BH * (float(v) - mn_g) / rng

    # Líneas guía + línea de cero si aplica
    for tk in [0, 0.25, 0.5, 0.75, 1.0]:
        y  = BY + BH * tk
        tv = mn_g + rng * tk
        d.add(Line(BX, y, BX+BW, y,
                   strokeColor=colors.HexColor('#EEEEEE'), strokeWidth=0.5))
        lbl = f'{tv:.2f}' if abs(tv) < 1 else f'{tv:.1f}'
        d.add(String(BX-4, y-3.5, lbl,
                     fontSize=6, fontName=FN, fillColor=CGRL, textAnchor='end'))
    # Línea de cero destacada
    if mn_g < 0 < mx_g:
        y0 = ys(0)
        d.add(Line(BX, y0, BX+BW, y0,
                   strokeColor=colors.HexColor('#90A4AE'), strokeWidth=0.8))

    # Ejes
    d.add(Line(BX, BY, BX, BY+BH, strokeColor=CGRL, strokeWidth=0.6))
    d.add(Line(BX, BY, BX+BW, BY, strokeColor=CGRL, strokeWidth=0.6))

    # Etiquetas eje X
    for i, mes in enumerate(MESES):
        x = BX + i * BW / 11
        d.add(String(x, BY-10, mes,
                     fontSize=6.5, fontName=FN, fillColor=CGRM, textAnchor='middle'))

    # Dibujar una línea por índice
    for idx, col_hex in zip(INDICES, COLORES):
        col  = colors.HexColor(col_hex)
        vals = series[idx]
        pts  = []
        for i, v in enumerate(vals):
            if v is not None:
                x = BX + i * BW / 11
                y = ys(v)
                pts.append((x, y))

        # Dibujar segmentos (omite los None sin romper)
        seg = []
        for i, v in enumerate(vals):
            if v is not None:
                seg.append((BX + i*BW/11, ys(v)))
            else:
                if len(seg) >= 2:
                    lp = []
                    for px, py in seg:
                        lp += [px, py]
                    d.add(PolyLine(lp, strokeColor=col, strokeWidth=1.4))
                seg = []
        if len(seg) >= 2:
            lp = []
            for px, py in seg:
                lp += [px, py]
            d.add(PolyLine(lp, strokeColor=col, strokeWidth=1.4))

        # Puntos
        for x, y in pts:
            d.add(Circle(x, y, 2.2, fillColor=BL,
                         strokeColor=col, strokeWidth=1.0))

    # Leyenda lateral derecha
    ley_x = BX + BW + 8
    ley_y = BY + BH - 4
    for idx, col_hex in zip(INDICES, COLORES):
        col = colors.HexColor(col_hex)
        d.add(Rect(ley_x, ley_y, 10, 6, fillColor=col, strokeColor=None, rx=1))
        d.add(String(ley_x+13, ley_y, idx,
                     fontSize=7, fontName=FNB, fillColor=CGR, textAnchor='start'))
        ley_y -= 11

    # Título
    d.add(String(ancho/2, alto+22, titulo,
                 fontSize=9.5, fontName=FNB, fillColor=CGR, textAnchor='middle'))
    if subtitulo:
        d.add(String(ancho/2, alto+12, subtitulo,
                     fontSize=7.5, fontName=FNI, fillColor=CGRL, textAnchor='middle'))
    return d

# ── Gráfico barras horizontales con color por clase ───────────────────────────
def barras_horizontales(datos, titulo, ancho=14*cm):
    """datos: [(label, valor, color_hex), ...]"""
    if not datos: return Spacer(1, 0.5*cm)
    n = len(datos); bh = 14; gap = 5
    alto = (n * (bh + gap) + 48) / 28.35 * cm
    d    = Drawing(ancho, alto)
    BX   = 105; BW = ancho - BX - 55
    vals = [abs(float(v)) for _, v, *_ in datos]
    mx   = max(vals) if vals else 1

    d.add(String(ancho/2, alto - 10, titulo,
                 fontSize=9.5, fontName=FNB, fillColor=CGR, textAnchor='middle'))
    # Línea guía al 50%
    x50 = BX + BW * 0.5
    d.add(Line(x50, 14, x50, alto - 18,
               strokeColor=colors.HexColor('#E0E0E0'), strokeWidth=0.5))

    for i, item in enumerate(datos):
        lbl = item[0]; val = abs(float(item[1]))
        col = colors.HexColor(item[2]) if len(item) > 2 else CV
        y   = alto - 26 - i * (bh + gap)
        bwi = max(BW * val / mx, 2)
        d.add(Rect(BX, y, bwi, bh, fillColor=col, strokeColor=None, rx=2))
        d.add(String(BX - 5, y + bh/2 - 3.5, lbl[:20],
                     fontSize=7.5, fontName=FN, fillColor=CGRM, textAnchor='end'))
        vs = f'{val:.2f}%' if val < 1 else (f'{val:.1f}%' if val < 100 else f'{int(val)}%')
        d.add(String(BX + bwi + 4, y + bh/2 - 3.5, vs,
                     fontSize=7.5, fontName=FNB, fillColor=CGRM, textAnchor='start'))
    return d

# ── Gráfico boxplot de índices espectrales ────────────────────────────────────
def boxplot_indices(res, indices, ancho=14*cm, alto=5*cm):
    """Muestra min-p25-media-p75-max para cada índice."""
    if not res: return Spacer(1, 0.5*cm)
    d   = Drawing(ancho, alto + 2*cm)
    BX  = 55; BY = 25; BH = alto - 20
    BW  = ancho - BX - 15
    n   = len(indices)
    slot= BW / max(n, 1)

    # Eje de referencia en 0
    y0 = BY + BH * 0.5
    d.add(Line(BX, y0, BX + BW, y0,
               strokeColor=colors.HexColor('#BDBDBD'), strokeWidth=0.5))

    # Determinar rango global
    all_vals = []
    for idx in indices:
        for k in ['min','p25','medio','p75','max']:
            v = res.get(f'{idx} {k}', 0) or 0
            all_vals.append(float(v))
    mn_g = min(all_vals) if all_vals else -1
    mx_g = max(all_vals) if all_vals else 1
    rng  = mx_g - mn_g if mx_g != mn_g else 1

    def ys(v):
        return BY + BH * (float(v) - mn_g) / rng

    PAL_IDX = ['#1B5E20','#0D47A1','#388E3C','#1565C0','#6A1B9A','#00695C','#BF360C']

    for i, idx in enumerate(indices):
        cx   = BX + (i + 0.5) * slot
        col  = colors.HexColor(PAL_IDX[i % len(PAL_IDX)])
        vmin = float(res.get(f'{idx} min',  0) or 0)
        vp25 = float(res.get(f'{idx} p25',  0) or 0)
        vmed = float(res.get(f'{idx} medio',0) or 0)
        vp75 = float(res.get(f'{idx} p75',  0) or 0)
        vmax = float(res.get(f'{idx} max',  0) or 0)
        bw2  = min(slot * 0.35, 18)

        # Bigotes
        d.add(Line(cx, ys(vmin), cx, ys(vp25), strokeColor=col, strokeWidth=1))
        d.add(Line(cx, ys(vp75), cx, ys(vmax), strokeColor=col, strokeWidth=1))
        # Tapas bigotes
        d.add(Line(cx-bw2*0.4, ys(vmin), cx+bw2*0.4, ys(vmin), strokeColor=col, strokeWidth=1))
        d.add(Line(cx-bw2*0.4, ys(vmax), cx+bw2*0.4, ys(vmax), strokeColor=col, strokeWidth=1))
        # Caja P25-P75
        y_box = ys(vp25); h_box = ys(vp75) - ys(vp25)
        if h_box < 1: h_box = 1
        d.add(Rect(cx-bw2, y_box, bw2*2, h_box,
                   fillColor=colors.HexColor(PAL_IDX[i % len(PAL_IDX)] + '40'),
                   strokeColor=col, strokeWidth=1))
        # Mediana
        d.add(Line(cx-bw2, ys(vmed), cx+bw2, ys(vmed),
                   strokeColor=col, strokeWidth=2))
        # Punto media
        d.add(Circle(cx, ys(vmed), 2.5, fillColor=BL, strokeColor=col, strokeWidth=1))
        # Etiqueta
        d.add(String(cx, BY - 11, idx,
                     fontSize=7, fontName=FNB, fillColor=CGRM, textAnchor='middle'))

    # Eje Y con escala
    d.add(Line(BX, BY, BX, BY + BH, strokeColor=CGRL, strokeWidth=0.5))
    for tk in [0, 0.25, 0.5, 0.75, 1.0]:
        y  = BY + BH * tk
        tv = mn_g + rng * tk
        d.add(Line(BX-4, y, BX, y, strokeColor=CGRL, strokeWidth=0.5))
        d.add(String(BX-6, y-3.5, f'{tv:.2f}',
                     fontSize=6, fontName=FN, fillColor=CGRL, textAnchor='end'))

    d.add(String(ancho/2, alto + 13, 'Distribución espacial de índices espectrales (min–P25–media–P75–max)',
                 fontSize=9, fontName=FNB, fillColor=CGR, textAnchor='middle'))
    d.add(String(ancho/2, alto + 5, 'Caja: rango intercuartil (P25–P75) · Línea: mediana · Punto: media · Bigotes: min–max',
                 fontSize=7, fontName=FNI, fillColor=CGRL, textAnchor='middle'))
    return d

# ── Tabla heatmap mensual ─────────────────────────────────────────────────────
def tabla_heatmap_meses(valores, unidad, titulo, color_max='#0D47A1', color_min='#E3F2FD'):
    """valores: lista de 12 floats (Ene..Dic)"""
    E = _E()
    if not valores or len(valores) < 12: return Spacer(1, 0.2*cm)
    MESES = ['Ene','Feb','Mar','Abr','May','Jun','Jul','Ago','Sep','Oct','Nov','Dic']
    mx = max(valores) if max(valores) != 0 else 1
    mn = min(valores)
    rng = mx - mn if mx != mn else 1

    def interp_color(v):
        t = (v - mn) / rng
        # De azul muy claro a azul oscuro
        r1,g1,b1 = int(color_min[1:3],16), int(color_min[3:5],16), int(color_min[5:7],16)
        r2,g2,b2 = int(color_max[1:3],16), int(color_max[3:5],16), int(color_max[5:7],16)
        r = int(r1 + (r2-r1)*t); g = int(g1 + (g2-g1)*t); b = int(b1 + (b2-b1)*t)
        return colors.Color(r/255, g/255, b/255)

    # Fila de meses
    hdrs = [Paragraph(f'<b>{m}</b>', ParagraphStyle('mh', fontName=FNB, fontSize=8,
            textColor=BL, alignment=TA_CENTER)) for m in MESES]
    vals = [Paragraph(f'<b>{v:.1f}</b>', ParagraphStyle(f'mv{i}', fontName=FNB, fontSize=9,
            textColor=BL if (valores[i]-mn)/rng > 0.5 else CGR,
            alignment=TA_CENTER)) for i, v in enumerate(valores)]
    cw   = [15*cm/12] * 12
    t    = Table([hdrs, vals], colWidths=cw)
    cmds = [
        ('BACKGROUND', (0,0),(-1,0), colors.HexColor('#0D3B1F')),
        ('TOPPADDING',    (0,0),(-1,-1), 5),
        ('BOTTOMPADDING', (0,0),(-1,-1), 5),
        ('ALIGN',         (0,0),(-1,-1), 'CENTER'),
        ('VALIGN',        (0,0),(-1,-1), 'MIDDLE'),
        ('BOX',           (0,0),(-1,-1), 0.5, CGRL),
        ('LINEABOVE',     (0,0),(-1,0),  1.0, CV),
        ('LINEBELOW',     (0,-1),(-1,-1),1.0, CV),
    ]
    for i in range(12):
        cmds.append(('BACKGROUND', (i,1),(i,1), interp_color(valores[i])))
    t.setStyle(TableStyle(cmds))
    return t

# ── Semáforo técnico ──────────────────────────────────────────────────────────
def semaforo_tecnico(nivel, valor_str, umbral_str, descripcion, ancho=14*cm):
    E = _E()
    SEM = {
        'verde':    (CV,    CVC,   '●  APTO'),
        'amarillo': (CAM,   CAMC,  '●  CONDICIONADO'),
        'rojo':     (CRO,   CROC,  '●  NO APTO'),
    }
    col_b, col_f, estado = SEM.get(nivel.lower(), (CGRL, CGRC, nivel.upper()))
    datos = [[
        Paragraph(estado, ParagraphStyle('se', fontName=FNB, fontSize=10,
            textColor=col_b, alignment=TA_CENTER)),
        Paragraph(f'<b>{valor_str}</b>', ParagraphStyle('sv', fontName=FNB, fontSize=13,
            textColor=CGR, alignment=TA_CENTER)),
        Paragraph(f'Umbral: {umbral_str}', ParagraphStyle('su', fontName=FNI, fontSize=8.5,
            textColor=CGRL, alignment=TA_CENTER)),
        Paragraph(descripcion, ParagraphStyle('sd', fontName=FN, fontSize=9,
            textColor=CGRM)),
    ]]
    t = Table(datos, colWidths=[3*cm, 2.5*cm, 2.5*cm, 7*cm])
    t.setStyle(TableStyle([
        ('BACKGROUND',   (0,0),(0,0), col_f),
        ('BACKGROUND',   (1,0),(2,0), CGRF),
        ('BACKGROUND',   (3,0),(3,0), BL),
        ('BOX',          (0,0),(-1,-1), 1, col_b),
        ('LINEBEFORE',   (1,0),(1,0),  0.5, CGRL),
        ('LINEBEFORE',   (2,0),(2,0),  0.5, CGRL),
        ('LINEBEFORE',   (3,0),(3,0),  0.5, CGRL),
        ('VALIGN',       (0,0),(-1,-1), 'MIDDLE'),
        ('TOPPADDING',   (0,0),(-1,-1), 8),
        ('BOTTOMPADDING',(0,0),(-1,-1), 8),
        ('LEFTPADDING',  (0,0),(-1,-1), 8),
    ]))
    return t

# ── Tabla de estadísticas de precisión ───────────────────────────────────────
def tabla_estadisticas_pro(media, std, mn, mx, p25, p75, cnt,
                            fuente, resolucion, periodo):
    E   = _E()
    cv  = round(std / media * 100, 1) if media and media != 0 else 0
    iqr = round(p75 - p25, 4) if p75 and p25 else 0
    datos = [
        ['Media (μ)',          f'{media:.4f}',  'Fuente GEE',    fuente],
        ['Desv. estándar (σ)', f'{std:.4f}',    'Resolución',    f'{resolucion}'],
        ['Coef. var. (CV%)',   f'{cv:.1f} %',   'Período',       periodo],
        ['Mínimo',             f'{mn:.4f}',      'N° píxeles',   f'{cnt:,}'],
        ['Máximo',             f'{mx:.4f}',      'IQR (P75-P25)',f'{iqr:.4f}'],
        ['Percentil P25',      f'{p25:.4f}',     '', ''],
        ['Percentil P75',      f'{p75:.4f}',     '', ''],
    ]
    return tabla_booktabs(datos, headers=['Estadístico','Valor','Metadato','Detalle'],
                          col_w=[3.8*cm, 2.8*cm, 3.2*cm, 5.2*cm])

# ── Gráfico balance hídrico PP vs ET ─────────────────────────────────────────
def grafico_balance_hidrico(pp_meses, et_media, ancho=14*cm, alto=6*cm):
    """pp_meses: lista 12 floats (PP mensual). et_media: float (ET media mensual equiv.)"""
    if not pp_meses or len(pp_meses) < 12: return Spacer(1, 0.5*cm)
    MESES = ['E','F','M','A','M','J','J','A','S','O','N','D']
    d  = Drawing(ancho, alto + 2.2*cm)
    BX = 62; BY = 30; BH = alto - 25
    BW = ancho - BX - 12
    n  = 12
    sw = BW / n

    mx = max(pp_meses) * 1.1
    if mx == 0: mx = 1

    def ys(v): return BY + BH * min(float(v), mx) / mx

    # Líneas guía
    for tk in [0.25, 0.5, 0.75, 1.0]:
        y  = BY + BH * tk; tv = mx * tk
        d.add(Line(BX, y, BX + BW, y,
                   strokeColor=colors.HexColor('#EEEEEE'), strokeWidth=0.5))
        d.add(String(BX-5, y-3.5, f'{int(tv)}',
                     fontSize=6.5, fontName=FN, fillColor=CGRL, textAnchor='end'))

    # Línea ET mensual equivalente
    et_anual_eq = et_media * 365 / 8 / 12  # aproximar a mm/mes
    y_et = ys(et_anual_eq)
    d.add(Line(BX, y_et, BX + BW, y_et,
               strokeColor=colors.HexColor('#E65100'), strokeWidth=1.5))
    d.add(String(BX + BW + 3, y_et - 3, 'ET',
                 fontSize=7, fontName=FNB, fillColor=colors.HexColor('#E65100'),
                 textAnchor='start'))

    # Barras PP con color excedente/déficit
    for i, pp in enumerate(pp_meses):
        bx_i = BX + i * sw + sw * 0.1
        bw_i = sw * 0.8
        bh_i = max(BH * pp / mx, 1)
        col  = '#1565C0' if pp >= et_anual_eq else '#EF9A9A'
        d.add(Rect(bx_i, BY, bw_i, bh_i, fillColor=colors.HexColor(col), strokeColor=None))
        d.add(String(bx_i + bw_i/2, BY - 10, MESES[i],
                     fontSize=6.5, fontName=FN, fillColor=CGRM, textAnchor='middle'))

    # Ejes
    d.add(Line(BX, BY, BX, BY + BH, strokeColor=CGRL, strokeWidth=0.6))
    d.add(Line(BX, BY, BX + BW, BY, strokeColor=CGRL, strokeWidth=0.6))

    d.add(String(ancho/2, alto + 14,
                 'Balance hídrico mensual — Precipitación vs Evapotranspiración',
                 fontSize=9.5, fontName=FNB, fillColor=CGR, textAnchor='middle'))
    d.add(String(ancho/2, alto + 5,
                 'Azul: excedente hídrico (PP > ET)  ·  Rojo: déficit (PP < ET)  ·  Línea naranja: ET estimada',
                 fontSize=7, fontName=FNI, fillColor=CGRL, textAnchor='middle'))
    return d

# ── Torta de cobertura ────────────────────────────────────────────────────────
def torta_cobertura(clases_pct, area_ha, ancho=14*cm):
    """clases_pct: [(nombre, pct, color_hex), ...] ordenado desc"""
    if not clases_pct: return Spacer(1, 0.5*cm)
    # Dibujar torta manual con Drawing
    radio = 2.8*cm; cx = 3.5*cm; cy = radio + 0.3*cm
    alto  = radio * 2 + 0.8*cm
    d     = Drawing(ancho, alto)

    angulo = 90.0  # empezar desde arriba
    for nombre, pct, col_hex in clases_pct:
        sweep  = 360.0 * pct / 100.0
        ang_r  = math.radians(angulo)
        ang_r2 = math.radians(angulo - sweep)
        # Dibuja sector como polígono con muchos puntos
        pts = [cx, cy]
        pasos = max(int(sweep / 3), 4)
        for k in range(pasos + 1):
            a  = math.radians(angulo - sweep * k / pasos)
            pts += [cx + radio * math.cos(a), cy + radio * math.sin(a)]
        d.add(Polygon(pts, fillColor=colors.HexColor(col_hex),
                      strokeColor=BL, strokeWidth=0.8))
        angulo -= sweep

    # Leyenda derecha
    ly = alto - 0.5*cm
    d.add(String(6.2*cm, ly + 0.15*cm, 'Clase de cobertura',
                 fontSize=8, fontName=FNB, fillColor=CGR))
    ly -= 0.5*cm
    for nombre, pct, col_hex in clases_pct:
        ha_cls = area_ha * pct / 100
        d.add(Rect(6.2*cm, ly, 0.55*cm, 0.3*cm,
                   fillColor=colors.HexColor(col_hex), strokeColor=None))
        txt = f'{nombre[:18]}  {pct:.1f}%  ({ha_cls:.1f} ha)'
        d.add(String(6.9*cm, ly + 0.05*cm, txt,
                     fontSize=7.5, fontName=FN, fillColor=CGR))
        ly -= 0.42*cm
        if ly < 0.2*cm:
            break
    return d

# ══════════════════════════════════════════════════════════════════════════════
# PORTADA
# ══════════════════════════════════════════════════════════════════════════════
def _fn_portada(canvas, doc, nombre_proy, area_ha, admin):
    W, H = A4
    canvas.saveState()

    # Fondos
    canvas.setFillColor(colors.HexColor('#1B4332'))
    canvas.rect(0, 0, W, H, fill=1, stroke=0)
    canvas.setFillColor(colors.HexColor('#0D2B1A'))
    canvas.rect(0, H*0.52, W, H*0.48, fill=1, stroke=0)
    canvas.setFillColor(colors.HexColor('#071810'))
    canvas.rect(0, 0, W, H*0.18, fill=1, stroke=0)

    # Franja superior verde brillante
    canvas.setFillColor(colors.HexColor('#4CAF50'))
    canvas.rect(0, H-0.55*cm, W, 0.55*cm, fill=1, stroke=0)
    canvas.setFillColor(colors.HexColor('#81C784'))
    canvas.rect(0, H-0.70*cm, W, 0.15*cm, fill=1, stroke=0)

    # Pino decorativo
    cx = W*0.82; cy = H*0.64; sz = 90
    canvas.setFillColor(colors.HexColor('#4E342E'))
    canvas.rect(cx-sz*0.07, cy, sz*0.14, sz*0.22, fill=1, stroke=0)
    for cw, cpp, ch, col in [
        (0.45, cy+sz*0.18, sz*0.30, '#388E3C'),
        (0.32, cy+sz*0.36, sz*0.28, '#2E7D32'),
        (0.20, cy+sz*0.54, sz*0.36, '#1B5E20'),
    ]:
        canvas.setFillColor(colors.HexColor(col))
        p = canvas.beginPath()
        p.moveTo(cx-sz*cw, cpp); p.lineTo(cx+sz*cw, cpp); p.lineTo(cx, cpp+ch)
        p.close(); canvas.drawPath(p, fill=1, stroke=0)
    canvas.setFillColor(colors.HexColor('#A5D6A7'))
    canvas.circle(cx, cy+sz*0.90, 3, fill=1, stroke=0)

    # Título principal
    canvas.setFillColor(colors.HexColor('#000000'))
    canvas.setFillAlpha(0.2)
    canvas.setFont('Helvetica-Bold', 48)
    canvas.drawString(2.02*cm, H*0.755-1, 'GeoDiagnostic')
    canvas.setFillAlpha(1.0)
    canvas.setFillColor(BL)
    canvas.setFont('Helvetica-Bold', 48)
    canvas.drawString(2*cm, H*0.755, 'GeoDiagnostic')
    canvas.setFont('Helvetica', 15)
    canvas.setFillColor(colors.HexColor('#A5D6A7'))
    canvas.drawString(2*cm, H*0.710, 'Diagnóstico Geoespacial Automatizado')
    canvas.setFont('Helvetica', 11)
    canvas.setFillColor(colors.HexColor('#81C784'))
    canvas.drawString(2*cm, H*0.685, 'Google Earth Engine  ·  QGIS 3.x  ·  ' + VERSION)

    # Línea separadora
    canvas.setStrokeColor(colors.HexColor('#4CAF50')); canvas.setLineWidth(1.2)
    canvas.line(2*cm, H*0.665, W-2*cm, H*0.665)
    canvas.setStrokeColor(colors.HexColor('#2E7D32')); canvas.setLineWidth(0.4)
    canvas.line(2*cm, H*0.660, W-2*cm, H*0.660)

    # Caja de datos
    canvas.setFillColor(colors.HexColor('#061209'))
    canvas.roundRect(2*cm, H*0.225, W-4*cm, H*0.415, 10, fill=1, stroke=0)
    canvas.setStrokeColor(colors.HexColor('#2E7D32')); canvas.setLineWidth(0.7)
    canvas.roundRect(2*cm, H*0.225, W-4*cm, H*0.415, 10, fill=0, stroke=1)
    canvas.setFillColor(colors.HexColor('#2E7D32'))
    canvas.roundRect(2*cm, H*0.225, 0.35*cm, H*0.415, 5, fill=1, stroke=0)

    canvas.setFillColor(colors.HexColor('#4CAF50'))
    canvas.setFont('Helvetica-Bold', 7.5)
    canvas.drawString(2.7*cm, H*0.620, 'DATOS DEL PROYECTO')
    canvas.setStrokeColor(colors.HexColor('#2E7D32')); canvas.setLineWidth(0.3)
    canvas.line(2.7*cm, H*0.617, W-2.5*cm, H*0.617)

    filas = [
        ('Proyecto',          nombre_proy or 'Sin nombre'),
        ('Área analizada',    f'{area_ha:,.2f} ha   /   {area_ha/100:.4f} km²'),
        ('Departamento',      admin.get('Departamento','N/D')),
        ('Distrito',          admin.get('Distrito','N/D')),
        ('País',              admin.get('Pais','Perú')),
        ('Fecha de análisis', datetime.now().strftime('%d de %B de %Y   %H:%M h')),
    ]
    y_f = H*0.595
    for k, v in filas:
        canvas.setFont('Helvetica-Bold', 9); canvas.setFillColor(colors.HexColor('#81C784'))
        canvas.drawString(2.7*cm, y_f, k)
        canvas.setFont('Helvetica', 10); canvas.setFillColor(BL)
        canvas.drawString(7.5*cm, y_f, str(v)[:52])
        canvas.setStrokeColor(colors.HexColor('#0F2D17')); canvas.setLineWidth(0.3)
        canvas.line(2.7*cm, y_f-0.12*cm, W-2.5*cm, y_f-0.12*cm)
        y_f -= 0.63*cm

    # Bloque autor
    canvas.setStrokeColor(colors.HexColor('#1B5E20')); canvas.setLineWidth(0.5)
    canvas.line(2*cm, H*0.195, W-2*cm, H*0.195)
    canvas.setFillColor(colors.HexColor('#2E7D32'))
    canvas.circle(3.2*cm, H*0.115, 0.75*cm, fill=1, stroke=0)
    canvas.setStrokeColor(colors.HexColor('#4CAF50')); canvas.setLineWidth(1.2)
    canvas.circle(3.2*cm, H*0.115, 0.75*cm, fill=0, stroke=1)
    canvas.setFillColor(BL); canvas.setFont('Helvetica-Bold', 14)
    canvas.drawCentredString(3.2*cm, H*0.108, 'LJ')
    canvas.setFont('Helvetica-Bold', 15); canvas.setFillColor(BL)
    canvas.drawString(4.4*cm, H*0.135, AUTOR)
    canvas.setFont('Helvetica', 9.5); canvas.setFillColor(colors.HexColor('#A5D6A7'))
    canvas.drawString(4.4*cm, H*0.113, 'Ingeniero Forestal  ·  Especialista GIS')
    canvas.setFont('Helvetica', 9); canvas.setFillColor(colors.HexColor('#81C784'))
    canvas.drawString(4.4*cm, H*0.091, CORREO)
    canvas.setFillColor(colors.HexColor('#66BB6A'))
    canvas.drawRightString(W-2*cm, H*0.091, f'Yape / Plin:  {YAPE}')
    canvas.setFillColor(colors.HexColor('#1B5E20'))
    canvas.rect(0, 0, W, 0.25*cm, fill=1, stroke=0)
    canvas.restoreState()


def _fn_pagina(canvas, doc, nombre_proy):
    if doc.page <= 1: return
    W, H = A4
    canvas.saveState()
    canvas.setFillColor(CV); canvas.rect(0, H-1.4*cm, W, 1.4*cm, fill=1, stroke=0)
    canvas.setFillColor(BL); canvas.setFont('Helvetica-Bold', 8.5)
    canvas.drawString(2*cm, H-0.9*cm, VERSION)
    canvas.setFont('Helvetica', 8); canvas.setFillColor(colors.HexColor('#C8E6C9'))
    canvas.drawRightString(W-2*cm, H-0.9*cm,
                           f'Proyecto: {(nombre_proy or "")[:42]}')
    canvas.setStrokeColor(colors.HexColor('#CFD8DC')); canvas.setLineWidth(0.5)
    canvas.line(2*cm, 1.6*cm, W-2*cm, 1.6*cm)
    canvas.setFont('Helvetica', 7.5); canvas.setFillColor(CGRL)
    canvas.drawString(2*cm, 0.9*cm, f'{AUTOR}  |  Especialista GIS & Teledetección')
    canvas.drawRightString(W-2*cm, 0.9*cm, f'Página {doc.page - 1}')
    canvas.restoreState()


# ══════════════════════════════════════════════════════════════════════════════
# FUNCIÓN PRINCIPAL
# ══════════════════════════════════════════════════════════════════════════════
def generar_reporte(ruta_salida, nombre_proy, resultados, datos_ficha,
                    area_ha=0, modo_drive=False, imagen_aoi=None,
                    vertices=None, zona_utm=''):
    _fig_num[0] = 0
    _tab_num[0] = 0
    E     = _E()
    admin = resultados.get('_admin', {})

    doc = BaseDocTemplate(ruta_salida, pagesize=A4,
        rightMargin=2*cm, leftMargin=2*cm,
        topMargin=2.2*cm, bottomMargin=2.5*cm)
    fr_p = Frame(0, 0, A4[0], A4[1], id='portada',
        leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0)
    fr_c = Frame(2*cm, 2.5*cm, A4[0]-4*cm, A4[1]-4.7*cm, id='contenido')
    doc.addPageTemplates([
        PageTemplate(id='Portada', frames=[fr_p],
            onPage=lambda c,d: _fn_portada(c,d,nombre_proy,area_ha,admin)),
        PageTemplate(id='Contenido', frames=[fr_c],
            onPage=lambda c,d: _fn_pagina(c,d,nombre_proy)),
    ])
    H = [Spacer(1, A4[1]), NextPageTemplate('Contenido'), PageBreak()]

    # helpers
    def sec(num, titulo, fuente=''):
        H.append(Spacer(1, 0.2*cm))
        H.append(cabecera_seccion(num, titulo, fuente))
        H.append(Spacer(1, 0.2*cm))
    def h2(t): H.append(Paragraph(t, E['h2']))
    def h3(t): H.append(Paragraph(t, E['h3']))
    def p(t):  H.append(Paragraph(t, E['body']))
    def nota(t): H.append(Paragraph(f'<i>Nota técnica: {t}</i>', E['nota']))
    def sp(n=0.3): H.append(Spacer(1, n*cm))
    def pag(): H.append(PageBreak())

    # ── TOC ──────────────────────────────────────────────────────────────────
    sec('', 'Tabla de Contenidos')
    secs = [
        ('1.', 'Ficha Técnica del Área de Interés'),
        ('2.', 'Resumen Ejecutivo de Indicadores'),
        ('3.', 'Topografía  —  USGS SRTM v3 (30 m)'),
        ('4.', 'Vegetación e Índices Espectrales  —  Sentinel-2 SR (10 m)'),
        ('5.', 'Cobertura y Uso del Suelo  —  Dynamic World (10 m)'),
        ('6.', 'Precipitación  —  CHIRPS v2.0 (~5 km)'),
        ('7.', 'Temperatura  —  ERA5-Land (~11 km)'),
        ('8.', 'Propiedades del Suelo  —  SoilGrids / OpenLandMap (250 m)'),
        ('9.', 'Riesgo de Erosión RUSLE  —  Derivado (30 m)'),
        ('10.','Evapotranspiración Real  —  MOD16 MODIS (500 m)'),
        ('11.','Diagnóstico General de Aptitud para Reforestación'),
        ('12.','Metodología del Análisis'),
        ('13.','Especies Forestales Recomendadas'),
        ('14.','Conclusiones y Recomendaciones Técnicas'),
        ('15.','Referencias Bibliográficas (APA)'),
    ]
    filas_toc = [[Paragraph(f'<b>{n}</b>', ParagraphStyle('tn', fontName=FNB,
                    fontSize=9.5, textColor=CAZ)),
                  Paragraph(t, ParagraphStyle('tt', fontName=FN,
                    fontSize=9.5, textColor=CGR))]
                 for n, t in secs]
    t_toc = Table(filas_toc, colWidths=[1.2*cm, 13.8*cm])
    t_toc.setStyle(TableStyle([
        ('ROWBACKGROUNDS',(0,0),(-1,-1),[BL, CGRF]),
        ('LINEABOVE',     (0,0),(-1,0),  1.0, CV),
        ('LINEBELOW',     (0,-1),(-1,-1),1.0, CV),
        ('GRID',          (0,0),(-1,-1), 0.3, colors.HexColor('#E0E0E0')),
        ('VALIGN',        (0,0),(-1,-1), 'MIDDLE'),
        ('TOPPADDING',    (0,0),(-1,-1), 5),
        ('BOTTOMPADDING', (0,0),(-1,-1), 5),
        ('LEFTPADDING',   (0,0),(-1,-1), 8),
    ]))
    H.append(t_toc)
    pag()

    # ── 1. FICHA TÉCNICA DEL AOI ──────────────────────────────────────────────
    sec(1, 'Ficha Técnica del Área de Interés')
    if datos_ficha:
        ficha_limpia = {k:v for k,v in datos_ficha.items()
                        if not str(k).startswith('_')}
        H.append(tabla_kv_pro(ficha_limpia))
        H.append(tab_caption('Parámetros geométricos y ubicación del área de interés.'))
    sp()
    if admin:
        h2('Ubicación Administrativa')
        H.append(tabla_kv_pro(admin))
        sp()
    if modo_drive:
        t_av = Table([[Paragraph(
            'AVISO: El área supera los 8,000 ha. Los rasters fueron exportados '
            'a Google Drive (carpeta GeoDiagnostic). Descárguelos desde drive.google.com.',
            ParagraphStyle('av', fontName=FN, fontSize=9.5, textColor=CGR,
                leading=14))]],colWidths=[15*cm])
        t_av.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,-1),CNRC),
            ('BOX',(0,0),(-1,-1),1.5,CNR),
            ('LEFTPADDING',(0,0),(-1,-1),10),('TOPPADDING',(0,0),(-1,-1),8),
            ('BOTTOMPADDING',(0,0),(-1,-1),8)]))
        H.append(t_av); sp()
    if imagen_aoi and os.path.exists(imagen_aoi):
        try:
            from reportlab.platypus import Image as RLImage
            H.append(RLImage(imagen_aoi, width=14*cm, height=7*cm))
            H.append(fig_caption('Vista del área de interés sobre el mapa base de QGIS.'))
        except Exception:
            pass

    # ── Tabla de coordenadas de vértices ─────────────────────────────────────
    if vertices:
        sp(0.4)
        h2('Coordenadas de Vértices del AOI')
        n_total = len(vertices)
        LIMITE_TABLA = 50   # más de 50 → tabla resumida + nota
        LIMITE_CSV   = 200  # más de 200 → solo nota, no tabla completa

        if n_total <= LIMITE_TABLA:
            verts_tabla = vertices
            nota_verts  = None
        elif n_total <= LIMITE_CSV:
            # Mostrar primeros 25 y últimos 10
            verts_tabla = vertices[:25] + vertices[n_total-10:]
            nota_verts  = (f'El polígono tiene {n_total} vértices. Se muestran los primeros '
                           f'25 y los últimos 10. Usa el botón "Exportar vértices (.csv)" '
                           f'en GeoDiagnostic para obtener la tabla completa.')
        else:
            verts_tabla = vertices[:25]
            nota_verts  = (f'El polígono tiene {n_total} vértices — solo se muestran los '
                           f'primeros 25. Exporta el CSV completo desde GeoDiagnostic.')

        hdrs_v = ['N°', 'Latitud (°)', 'Longitud (°)',
                  f'Este UTM {zona_utm} (m)', f'Norte UTM {zona_utm} (m)']
        filas_v = []
        for v in verts_tabla:
            filas_v.append([
                str(v['n']),
                f"{v['lat']:.6f}",
                f"{v['lon']:.6f}",
                f"{v['este']:.1f}",
                f"{v['norte']:.1f}",
            ])
        t_verts = tabla_booktabs(
            filas_v, headers=hdrs_v,
            col_w=[1.2*cm, 3.2*cm, 3.2*cm, 3.8*cm, 3.6*cm])
        H.append(t_verts)
        H.append(tab_caption(
            f'Coordenadas de los {n_total} vértices del AOI en sistema geográfico '
            f'WGS84 (EPSG:4326) y proyección UTM Zona {zona_utm} (WGS84). '
            f'El vértice de cierre no se repite.'))
        if nota_verts:
            nota(nota_verts)
    pag()

    # ── 2. RESUMEN EJECUTIVO ──────────────────────────────────────────────────
    sec(2, 'Resumen Ejecutivo de Indicadores')
    p('La siguiente tabla sintetiza los indicadores más relevantes del diagnóstico '
      'geoespacial. Los semáforos de estado se basan en umbrales técnicos de aptitud '
      'para reforestación según criterios FAO/USDA.')
    sp(0.3)

    SEM_C = {
        'verde':    (CV,   'APTO'),
        'amarillo': (CAM,  'CONDICIONADO'),
        'rojo':     (CRO,  'NO APTO'),
    }
    inds = []
    if 'topografia' in resultados:
        r  = resultados['topografia']
        pm = float(r.get('Pendiente media (°)', r.get('Pendiente media (grados)',0)) or 0)
        ev = float(r.get('Elevación media (msnm)', r.get('Elevacion media (msnm)',0)) or 0)
        inds.append(('Topografía', 'Elevación media', f'{ev:.0f} msnm', 'verde'))
        inds.append(('Topografía', 'Pendiente media',
                     f'{pm:.1f}°',
                     'verde' if pm<15 else 'amarillo' if pm<30 else 'rojo'))
    if 'vegetacion' in resultados:
        nd = float(resultados['vegetacion'].get('NDVI medio',0) or 0)
        inds.append(('Vegetación','NDVI medio', f'{nd:.4f}',
                     'verde' if nd>0.4 else 'amarillo' if nd>0.2 else 'rojo'))
    if 'clima' in resultados:
        pp = float(resultados['clima'].get('Precipitación total (mm)',
               resultados['clima'].get('Precipitacion total (mm)',0)) or 0)
        inds.append(('Precipitación','PP total anual', f'{pp:.0f} mm',
                     'verde' if pp>600 else 'amarillo' if pp>300 else 'rojo'))
    if 'temperatura' in resultados:
        tm = float(resultados['temperatura'].get('Temperatura media anual (°C)',
               resultados['temperatura'].get('Temperatura media anual (C)',0)) or 0)
        inds.append(('Temperatura','Temp. media anual', f'{tm:.1f} °C', 'verde'))
    if 'suelos' in resultados:
        ph = float(resultados['suelos'].get('pH del suelo (0-5 cm)',
               resultados['suelos'].get('pH del suelo (0-5cm)',0)) or 0)
        inds.append(('Suelos','pH del suelo', f'{ph:.2f}',
                     'verde' if 5.5<=ph<=7.5 else 'amarillo' if 5.0<=ph<=8.0 else 'rojo'))
    if 'erosion' in resultados:
        rg = resultados['erosion'].get('Riesgo erosivo','Bajo')
        inds.append(('Erosión','Riesgo RUSLE', rg,
                     'verde' if rg=='Bajo' else 'amarillo' if rg=='Medio' else 'rojo'))
    if 'evapotranspiracion' in resultados:
        et = float(resultados['evapotranspiracion'].get('ET media (mm/8 días)',
               resultados['evapotranspiracion'].get('ET media (mm/8dias)',0)) or 0)
        inds.append(('ET','ET media', f'{et:.1f} mm/8d', 'verde'))

    if inds:
        # Tarjetas KPI en fila
        kpi_row = []
        for _, lbl, val, sem in inds[:4]:
            col_s, est_s = SEM_C.get(sem, (CGRL, sem.upper()))
            kpi_row.append(kpi_card(val, lbl, est_s, col_s, ancho=3.5*cm, alto=2.2*cm))
        if kpi_row:
            H.append(Table([kpi_row],
                colWidths=[3.6*cm]*len(kpi_row),
                style=TableStyle([('ALIGN',(0,0),(-1,-1),'CENTER'),
                                  ('VALIGN',(0,0),(-1,-1),'MIDDLE'),
                                  ('LEFTPADDING',(0,0),(-1,-1),3),
                                  ('RIGHTPADDING',(0,0),(-1,-1),3)])))
            sp(0.2)
        kpi_row2 = []
        for _, lbl, val, sem in inds[4:8]:
            col_s, est_s = SEM_C.get(sem, (CGRL, sem.upper()))
            kpi_row2.append(kpi_card(val, lbl, est_s, col_s, ancho=3.5*cm, alto=2.2*cm))
        if kpi_row2:
            H.append(Table([kpi_row2],
                colWidths=[3.6*cm]*len(kpi_row2),
                style=TableStyle([('ALIGN',(0,0),(-1,-1),'CENTER'),
                                  ('VALIGN',(0,0),(-1,-1),'MIDDLE'),
                                  ('LEFTPADDING',(0,0),(-1,-1),3),
                                  ('RIGHTPADDING',(0,0),(-1,-1),3)])))
        sp(0.3)
        # Tabla resumen
        fh = [Paragraph(f'<b>{x}</b>', E['tabla_h'])
              for x in ['Módulo','Indicador','Valor','Estado']]
        fr = []
        for mod, lbl, val, sem in inds:
            col_s, est_s = SEM_C.get(sem, (CGRL, sem.upper()))
            fr.append([
                Paragraph(mod, E['tabla_v']),
                Paragraph(lbl, E['tabla_v']),
                Paragraph(f'<b>{val}</b>', E['tabla_vb']),
                Paragraph(est_s, ParagraphStyle('es', fontName=FNB, fontSize=9,
                    textColor=col_s, alignment=TA_CENTER)),
            ])
        t_res = Table([fh]+fr, colWidths=[3.5*cm,4.5*cm,3.5*cm,3.5*cm])
        cmds_r = [
            ('BACKGROUND',   (0,0),(-1,0), colors.HexColor('#0D3B1F')),
            ('LINEABOVE',    (0,0),(-1,0),  1.2, CGR),
            ('LINEBELOW',    (0,0),(-1,0),  0.5, CGRL),
            ('LINEBELOW',    (0,-1),(-1,-1),1.0, CGR),
            ('GRID',         (0,1),(-1,-2), 0.3, colors.HexColor('#E0E0E0')),
            ('ROWBACKGROUNDS',(0,1),(-1,-1),[BL, CGRF]),
            ('VALIGN',       (0,0),(-1,-1), 'MIDDLE'),
            ('TOPPADDING',   (0,0),(-1,-1), 5),
            ('BOTTOMPADDING',(0,0),(-1,-1), 5),
            ('LEFTPADDING',  (0,0),(-1,-1), 7),
        ]
        for i,(mod,lbl,val,sem) in enumerate(inds,1):
            col_s,_ = SEM_C.get(sem,(CGRL,sem))
            cmds_r.append(('BACKGROUND',(3,i),(3,i),
                colors.HexColor('#E8F5E9') if sem=='verde' else
                colors.HexColor('#FFF3E0') if sem=='amarillo' else
                colors.HexColor('#FFEBEE')))
        t_res.setStyle(TableStyle(cmds_r))
        H.append(t_res)
        H.append(tab_caption('Resumen ejecutivo de indicadores y aptitud para reforestación.'))
    pag()

    # ── 3. TOPOGRAFÍA ─────────────────────────────────────────────────────────
    if 'topografia' in resultados:
        res = resultados['topografia']
        per = res.get('_periodo','Estático — SRTM 2000')
        sec(3, 'Topografía', 'USGS SRTM v3 — 30 m')
        p('El modelo digital de elevación (DEM) SRTM v3 proporciona información '
          'topográfica con resolución de 30 m. El Índice de Humedad Topográfica '
          '(TWI) indica las zonas con mayor acumulación de humedad en el suelo, '
          'fundamental para identificar áreas potenciales de reforestación.')
        sp(0.2)

        # Datos limpios para tabla
        topo_d = {k:v for k,v in res.items()
                  if not k.startswith('_') and k!='N° píxeles analizados'}
        H.append(tabla_kv_pro(topo_d))
        H.append(tab_caption('Variables topográficas calculadas sobre el área de interés.'))
        sp(0.3)

        em = float(res.get('Elevación media (msnm)', res.get('Elevacion media (msnm)',0)) or 0)
        en = float(res.get('Elevación mínima (msnm)', res.get('Elevacion minima (msnm)',0)) or 0)
        ex = float(res.get('Elevación máxima (msnm)', res.get('Elevacion maxima (msnm)',0)) or 0)
        pm = float(res.get('Pendiente media (°)', res.get('Pendiente media (grados)',0)) or 0)
        px = float(res.get('Pendiente máxima (°)', res.get('Pendiente maxima (grados)',0)) or 0)

        H.append(grafico_barras(
            [('Mín.',en,'#90CAF9'),('Media',em,'#1565C0'),('Máx.',ex,'#0D47A1')],
            'Perfil altitudinal del área de interés (msnm)',
            subtitulo='Elevación mínima, media y máxima del DEM SRTM v3',
            eje_y_label='msnm'))
        H.append(fig_caption('Perfil altitudinal: elevación mínima, media y máxima sobre el AOI.'))
        sp(0.3)

        niv = 'verde' if pm<15 else 'amarillo' if pm<30 else 'rojo'
        umb = '< 15° apto  |  15°–30° condicionado  |  > 30° no apto'
        H.append(semaforo_tecnico(niv,
            f'{pm:.1f}°', umb,
            f'Pendiente media: {pm:.1f}° — '
            f'{"Apta para reforestación sin obras especiales." if pm<15 else "Requiere terrazas de contorno y manejo de pendientes." if pm<30 else "Riesgo alto de erosión. Requiere obras de conservación antes de plantar."}'))
        sp(0.3)
        h3('Estadísticas de precisión — Elevación')
        std_e = float(res.get('Desv. estándar elev. (m)', res.get('Desv. estandar elev.',0)) or 0)
        p25_e = float(res.get('P25 elevación (msnm)',0) or 0)
        p75_e = float(res.get('P75 elevación (msnm)',0) or 0)
        cnt_e = int(res.get('N° píxeles analizados',0) or 0)
        H.append(tabla_estadisticas_pro(em, std_e, en, ex, p25_e, p75_e,
            cnt_e, 'USGS/SRTMGL1_003', '30 m', per))
        nota('SRTM v3: precisión vertical absoluta < 16 m (90% confianza). '
             'Farr et al. (2007). doi:10.1029/2005RG000183')
        pag()

    # ── 4. VEGETACIÓN ─────────────────────────────────────────────────────────
    if 'vegetacion' in resultados:
        res = resultados['vegetacion']
        per = res.get('_periodo','N/D')
        sec(4, 'Vegetación e Índices Espectrales', 'Sentinel-2 SR — 10 m')
        p('Los índices espectrales derivados de Sentinel-2 SR permiten caracterizar '
          'el estado de la vegetación, humedad del suelo y riesgo de incendio. '
          'Se calculó la mediana del período para minimizar efectos de nubes '
          f'(filtro: cobertura nubosa < 20%). Período analizado: {per}.')
        sp(0.2)

        INDICES = ['NDVI','EVI','SAVI','NDWI','NDMI','NBR','BSI']
        DESC    = {
            'NDVI': 'Índice de vegetación de diferencia normalizada',
            'EVI':  'Índice de vegetación mejorado',
            'SAVI': 'Índice de vegetación ajustado al suelo',
            'NDWI': 'Índice de agua de diferencia normalizada',
            'NDMI': 'Índice de humedad de diferencia normalizada',
            'NBR':  'Índice de área quemada normalizado',
            'BSI':  'Índice de suelo desnudo',
        }

        # Tabla 6 columnas: índice | descripción | media | min | max | p25-p75
        filas_v = []
        for idx in INDICES:
            filas_v.append([
                idx,
                DESC.get(idx,''),
                f'{float(res.get(f"{idx} medio",0) or 0):.4f}',
                f'{float(res.get(f"{idx} min",0) or 0):.4f}',
                f'{float(res.get(f"{idx} max",0) or 0):.4f}',
                f'{float(res.get(f"{idx} p25",0) or 0):.4f} — {float(res.get(f"{idx} p75",0) or 0):.4f}',
            ])
        H.append(tabla_booktabs(filas_v,
            headers=['Índice','Descripción','Media','Mínimo','Máximo','P25 — P75'],
            col_w=[1.5*cm, 5*cm, 1.8*cm, 1.8*cm, 1.8*cm, 3.1*cm]))
        H.append(tab_caption('Estadísticas espaciales de los índices espectrales calculados sobre el AOI.'))
        sp(0.3)

        # Gráfico barras medias
        PAL_I = ['#1B5E20','#2E7D32','#388E3C','#0D47A1','#1565C0','#E65100','#B71C1C']
        H.append(grafico_barras(
            [(ix, float(res.get(f'{ix} medio',0) or 0), PAL_I[i])
             for i,ix in enumerate(INDICES)],
            'Valores medios de los índices espectrales',
            subtitulo='Mediana del período analizado sobre el área de interés',
            ancho=14*cm, alto=5.5*cm))
        H.append(fig_caption('Valores medios de los siete índices espectrales calculados.'))
        sp(0.3)

        # Boxplot distribución espacial
        H.append(boxplot_indices(res, INDICES, ancho=14*cm, alto=5*cm))
        H.append(fig_caption(
            'Distribución espacial de los índices espectrales. '
            'Caja: rango intercuartil (P25–P75). Línea: mediana. Punto: media. '
            'Bigotes: rango completo (mín.–máx.).'))
        sp(0.3)

        # ── Análisis multitemporal — evolución mensual de los 7 índices ──────
        _meses_idx = {idx: [res.get(f'{idx}_Mes_{m:02d}', None)
                             for m in range(1,13)] for idx in INDICES}
        _tiene_datos_mensuales = any(
            v is not None for vs in _meses_idx.values() for v in vs)

        if _tiene_datos_mensuales:
            pag()
            h2('Análisis multitemporal — Evolución mensual de índices espectrales')
            p('La siguiente gráfica muestra la evolución mensual de los siete índices '
              'espectrales calculados sobre el área de interés. Cada línea representa '
              'el valor medio del índice para todas las imágenes Sentinel-2 disponibles '
              f'en ese mes (filtro: nubosidad < 20%). Período: {per}.')
            sp(0.25)
            H.append(grafico_multiserie_indices(
                res,
                'Evolución mensual de los 7 índices espectrales',
                subtitulo=f'Sentinel-2 SR — Mediana mensual — Período: {per}',
                ancho=14*cm, alto=6.5*cm))
            H.append(fig_caption(
                'Evolución temporal mensual de los índices espectrales sobre el AOI. '
                'Cada punto representa la mediana del mes. Los valores None indican '
                'meses sin imágenes disponibles por cobertura nubosa.'))
            sp(0.3)

            # Heatmap mensual de NDVI
            _ndvi_mes = [res.get(f'NDVI_Mes_{m:02d}', None) for m in range(1,13)]
            _ndvi_vals = [float(v) if v is not None else 0.0 for v in _ndvi_mes]
            if any(v > 0 for v in _ndvi_vals):
                H.append(tabla_heatmap_meses(
                    _ndvi_vals, '',
                    'NDVI mensual',
                    color_max='#1B5E20', color_min='#F1F8E9'))
                H.append(tab_caption(
                    'NDVI mensual sobre el AOI. '
                    'Verde intenso: mayor cobertura vegetal. '
                    'Verde claro: menor cobertura o meses sin datos.'))
                sp(0.2)

            # Mini-tabla resumen con medias mensuales de todos los índices
            MESES_NOM = ['Ene','Feb','Mar','Abr','May','Jun',
                         'Jul','Ago','Sep','Oct','Nov','Dic']
            _filas_mt = []
            for idx in INDICES:
                fila = [idx]
                for m in range(1, 13):
                    v = res.get(f'{idx}_Mes_{m:02d}', None)
                    fila.append(f'{float(v):.3f}' if v is not None else '—')
                _filas_mt.append(fila)
            H.append(tabla_booktabs(
                _filas_mt,
                headers=['Índice'] + MESES_NOM,
                col_w=[1.4*cm] + [1.05*cm]*12))
            H.append(tab_caption(
                'Valores medios mensuales de los 7 índices espectrales. '
                '"—" indica mes sin imágenes disponibles.'))
            sp(0.3)

        # Semáforo NDVI
        nd = float(res.get('NDVI medio',0) or 0)
        niv_nd = 'verde' if nd>0.4 else 'amarillo' if nd>0.2 else 'rojo'
        H.append(semaforo_tecnico(niv_nd,
            f'NDVI = {nd:.4f}',
            '> 0.4 apto  |  0.2–0.4 cond.  |  < 0.2 degradado',
            f'{"Cobertura vegetal densa y saludable — condiciones favorables para reforestación." if nd>0.4 else "Cobertura moderada o con estrés hídrico — se recomienda evaluación en campo." if nd>0.2 else "Cobertura escasa o suelo desnudo — zona prioritaria para intervención."}'))
        sp(0.3)

        # Tabla de estadísticas de precisión para NDVI
        h3('Estadísticas de precisión — NDVI')
        H.append(tabla_estadisticas_pro(
            nd,
            float(res.get('NDVI stdDev',0) or 0),
            float(res.get('NDVI min',0) or 0),
            float(res.get('NDVI max',0) or 0),
            float(res.get('NDVI p25',0) or 0),
            float(res.get('NDVI p75',0) or 0),
            int(res.get('NDVI count',0) or 0),
            'COPERNICUS/S2_SR_HARMONIZED', '10 m', per))
        nota('Sentinel-2 MSI: resolución 10 m (bandas NIR y rojo). Mediana del período. '
             'Drusch et al. (2012). doi:10.1016/j.rse.2011.11.026')
        pag()

    # ── 5. COBERTURA ──────────────────────────────────────────────────────────
    if 'cobertura' in resultados:
        res = resultados['cobertura']
        per = res.get('_periodo','N/D')
        sec(5, 'Cobertura y Uso del Suelo', 'Dynamic World — 10 m')
        p('Dynamic World es un producto de clasificación de cobertura del suelo '
          'en tiempo casi real (latencia ~5 días) con resolución de 10 m, basado '
          'en aprendizaje profundo sobre imágenes Sentinel-2. '
          f'Período analizado: {per}.')
        sp(0.2)

        DESCR_DW = {
            'Agua':         'Cuerpos hídricos permanentes (ríos, lagunas, reservorios)',
            'Árboles':      'Bosque nativo, secundario y plantaciones forestales',
            'Césped/Pasto': 'Pastizales naturales, praderas y herbazales',
            'Veg. inundada':'Bofedales, humedales y vegetación palustre',
            'Cultivos':     'Tierras agrícolas activas y en descanso (barbecho)',
            'Arbustos':     'Matorrales, chaparrales y arbustales densos',
            'Construido':   'Zonas urbanas, vías, infraestructura construida',
            'Suelo desnudo':'Áreas sin cobertura vegetal significativa',
            'Nieve/Hielo':  'Zonas glaciares, nevados y permafrost',
        }
        cp = {k: float(v or 0) for k,v in res.items()
              if '(%)' in k and not k.startswith('_') and float(v or 0) > 0}
        co = sorted(cp.items(), key=lambda x: -x[1])

        if co:
            # Tabla con chip + ha + %
            hdrs = ['Color','Clase','Descripción','%','Hectáreas']
            filas_c = []
            for k, v in co:
                nm  = k.replace(' (%)','')
                col = COLORES_DW.get(nm, '#9E9E9E')
                ha_cls = area_ha * v / 100
                filas_c.append([
                    Drawing(10,10, initialFontName=FN,
                            initialFontSize=8).__class__.__name__,  # placeholder
                    nm,
                    DESCR_DW.get(nm,''),
                    f'{v:.2f}%',
                    f'{ha_cls:.1f} ha',
                ])
            # Generar tabla real con chips
            hdr_row = [Paragraph(h, E['tabla_h']) for h in hdrs]
            data_rows = []
            for k, v in co:
                nm     = k.replace(' (%)','')
                col    = COLORES_DW.get(nm, '#9E9E9E')
                ha_cls = area_ha * v / 100
                chip   = Drawing(10, 10)
                chip.add(Rect(0,0,10,10, fillColor=colors.HexColor(col),
                              strokeColor=colors.HexColor('#90A4AE'), strokeWidth=0.5))
                data_rows.append([
                    chip,
                    Paragraph(f'<b>{nm}</b>', E['tabla_v']),
                    Paragraph(DESCR_DW.get(nm,''), ParagraphStyle('dc',
                        fontName=FN, fontSize=8.5, textColor=CGR, leading=12)),
                    Paragraph(f'<b>{v:.2f}%</b>', ParagraphStyle('vc',
                        fontName=FNB, fontSize=9, textColor=CAZM,
                        alignment=TA_CENTER)),
                    Paragraph(f'{ha_cls:.1f}', ParagraphStyle('hc',
                        fontName=FNB, fontSize=9, textColor=CV,
                        alignment=TA_CENTER)),
                ])
            t_cob = Table([hdr_row]+data_rows,
                          colWidths=[0.9*cm,3.2*cm,7.4*cm,2*cm,1.5*cm])
            t_cob.setStyle(TableStyle([
                ('BACKGROUND',   (0,0),(-1,0), colors.HexColor('#0D3B1F')),
                ('LINEABOVE',    (0,0),(-1,0),  1.2, CGR),
                ('LINEBELOW',    (0,0),(-1,0),  0.5, CGRL),
                ('LINEBELOW',    (0,-1),(-1,-1),1.0, CGR),
                ('GRID',         (0,1),(-1,-2), 0.3, colors.HexColor('#E0E0E0')),
                ('ROWBACKGROUNDS',(0,1),(-1,-1),[BL, CGRF]),
                ('VALIGN',       (0,0),(-1,-1), 'MIDDLE'),
                ('ALIGN',        (0,0),(0,-1),  'CENTER'),
                ('ALIGN',        (3,0),(4,-1),  'CENTER'),
                ('TOPPADDING',   (0,0),(-1,-1), 5),
                ('BOTTOMPADDING',(0,0),(-1,-1), 5),
                ('LEFTPADDING',  (0,0),(-1,-1), 6),
            ]))
            H.append(t_cob)
            H.append(tab_caption(
                'Distribución porcentual y en hectáreas de las clases de cobertura '
                'del suelo según Dynamic World.'))
            sp(0.4)

            # Barras horizontales con color DW
            H.append(barras_horizontales(
                [(k.replace(' (%)',''), v, COLORES_DW.get(k.replace(' (%)',''),'#9E9E9E'))
                 for k,v in co],
                'Distribución porcentual por clase de cobertura (%)'))
            H.append(fig_caption(
                'Distribución porcentual de las clases de cobertura del suelo. '
                'Colores oficiales Dynamic World (Brown et al., 2022).'))
            sp(0.3)

            # Torta con leyenda
            clases_torta = [(k.replace(' (%)',''), v,
                             COLORES_DW.get(k.replace(' (%)',''),'#9E9E9E'))
                            for k,v in co]
            H.append(torta_cobertura(clases_torta, area_ha, ancho=14*cm))
            H.append(fig_caption(
                'Distribución proporcional de las clases de cobertura del suelo.'))
            nota('Dynamic World: clasificación en tiempo real sobre Sentinel-2 (10 m). '
                 'Brown et al. (2022). doi:10.1038/s41597-022-01307-4')
        pag()

    # ── 6. PRECIPITACIÓN ──────────────────────────────────────────────────────
    if 'clima' in resultados:
        res = resultados['clima']
        per = res.get('_periodo','N/D')
        sec(6, 'Precipitación', 'CHIRPS v2.0 — ~5 km')
        p('CHIRPS (Climate Hazards Group InfraRed Precipitation with Station data) '
          'combina datos de estaciones meteorológicas con imágenes satelitales '
          f'infrarrojas para estimar precipitación diaria a ~5 km. Período: {per}.')
        sp(0.2)

        pp_tot = float(res.get('Precipitación total (mm)',
                 res.get('Precipitacion total (mm)',0)) or 0)
        pp_min = float(res.get('Precipitación mínima (mm)',
                 res.get('Precipitacion minima (mm)',0)) or 0)
        pp_max = float(res.get('Precipitación máxima (mm)',
                 res.get('Precipitacion maxima (mm)',0)) or 0)
        pp_std = float(res.get('Desv. estándar PP (mm)',0) or 0)
        pp_cnt = int(res.get('N° píxeles analizados',0) or 0)

        resumen_pp = {
            'Precipitación total anual (mm)': f'{pp_tot:.1f}',
            'Precipitación mínima espacial (mm)': f'{pp_min:.1f}',
            'Precipitación máxima espacial (mm)': f'{pp_max:.1f}',
            'Desv. estándar espacial (mm)': f'{pp_std:.2f}',
            'N° píxeles analizados': f'{pp_cnt:,}',
        }
        H.append(tabla_kv_pro(resumen_pp))
        H.append(tab_caption('Estadísticas espaciales de precipitación sobre el área de interés.'))
        sp(0.3)

        mv = [float(res.get(f'PP_Mes_{m:02d} (mm)',0) or 0) for m in range(1,13)]
        if any(v > 0 for v in mv):
            # Tabla heatmap
            H.append(tabla_heatmap_meses(mv, 'mm',
                'Precipitación mensual acumulada (mm)'))
            H.append(tab_caption(
                'Precipitación mensual acumulada. '
                'La intensidad del azul indica mayor precipitación.'))
            sp(0.3)

            H.append(grafico_lineas(mv,
                'Precipitación mensual acumulada (mm)',
                subtitulo=f'Período: {per}',
                color='#1565C0', color_area='#BBDEFB',
                eje_y_label='mm'))
            H.append(fig_caption('Serie mensual de precipitación acumulada sobre el AOI.'))
            sp(0.3)

            mx_mes = max(enumerate(mv), key=lambda x:x[1])
            mn_mes = min(enumerate(mv), key=lambda x:x[1])
            MESES_NOM = ['Enero','Febrero','Marzo','Abril','Mayo','Junio',
                         'Julio','Agosto','Septiembre','Octubre','Noviembre','Diciembre']
            p(f'El mes más lluvioso es <b>{MESES_NOM[mx_mes[0]]}</b> con '
              f'<b>{mx_mes[1]:.1f} mm</b>, mientras que el más seco es '
              f'<b>{MESES_NOM[mn_mes[0]]}</b> con <b>{mn_mes[1]:.1f} mm</b>. '
              f'La precipitación total anual de <b>{pp_tot:.0f} mm</b> '
              f'{"indica un régimen húmedo favorable para la vegetación." if pp_tot>800 else "corresponde a un régimen subhúmedo — se recomienda evaluar el balance hídrico." if pp_tot>400 else "indica un régimen semiárido — se requieren especies tolerantes a sequía."}')
        sp(0.3)
        h3('Estadísticas de precisión — Precipitación')
        H.append(tabla_estadisticas_pro(pp_tot, pp_std, pp_min, pp_max,
            0, 0, pp_cnt, 'UCSB-CHG/CHIRPS/DAILY', '5566 m (~5 km)', per))
        nota('CHIRPS v2.0: combina estaciones con imágenes infrarrojas. '
             'Latencia ~3 semanas. Funk et al. (2015). doi:10.1038/sdata.2015.66')
        pag()

    # ── 7. TEMPERATURA ────────────────────────────────────────────────────────
    if 'temperatura' in resultados:
        res = resultados['temperatura']
        per = res.get('_periodo','N/D')
        sec(7, 'Temperatura', 'ERA5-Land — ~11 km')
        p('ERA5-Land es el reanálisis climático de mayor resolución del ECMWF, '
          'que combina modelos meteorológicos con observaciones globales. '
          'Proporciona temperatura del aire a 2 m de altura con resolución '
          f'de 0.1° (~11 km). Período: {per}.')
        sp(0.2)

        t_med = float(res.get('Temperatura media anual (°C)',
                 res.get('Temperatura media anual (C)',0)) or 0)
        t_min = float(res.get('Temperatura mínima (°C)',
                 res.get('Temperatura minima (C)',0)) or 0)
        t_max = float(res.get('Temperatura máxima (°C)',
                 res.get('Temperatura maxima (C)',0)) or 0)
        t_amp = float(res.get('Amplitud térmica (°C)',0) or round(t_max-t_min,1))
        t_std = float(res.get('Desv. estándar T (°C)',0) or 0)
        t_cnt = int(res.get('N° píxeles analizados',0) or 0)

        resumen_t = {
            'Temperatura media anual (°C)': f'{t_med:.1f}',
            'Temperatura mínima (°C)':       f'{t_min:.1f}',
            'Temperatura máxima (°C)':       f'{t_max:.1f}',
            'Amplitud térmica anual (°C)':   f'{t_amp:.1f}',
            'Desv. estándar (°C)':           f'{t_std:.2f}',
            'N° píxeles analizados':         f'{t_cnt:,}',
        }
        H.append(tabla_kv_pro(resumen_t))
        H.append(tab_caption('Estadísticas espaciales de temperatura sobre el área de interés.'))
        sp(0.3)

        mt = [float(res.get(f'Temp_Mes_{m:02d} (°C)',
               res.get(f'Temp_Mes_{m:02d} (C)',0)) or 0) for m in range(1,13)]
        if any(v != 0 for v in mt):
            H.append(tabla_heatmap_meses(mt, '°C',
                'Temperatura media mensual (°C)',
                color_max='#C62828', color_min='#BBDEFB'))
            H.append(tab_caption(
                'Temperatura media mensual. Azul: meses más fríos. Rojo: meses más cálidos.'))
            sp(0.3)
            H.append(grafico_lineas(mt,
                'Temperatura media mensual (°C)',
                subtitulo=f'Período: {per}',
                color='#C62828', color_area='#FFCDD2',
                eje_y_label='°C'))
            H.append(fig_caption('Serie mensual de temperatura media sobre el AOI.'))

        sp(0.3)
        # Balance hídrico PP vs ET
        if 'clima' in resultados and 'evapotranspiracion' in resultados:
            pp_m = [float(resultados['clima'].get(f'PP_Mes_{m:02d} (mm)',0) or 0)
                    for m in range(1,13)]
            et_med_v = float(resultados['evapotranspiracion'].get(
                'ET media (mm/8 días)',
                resultados['evapotranspiracion'].get('ET media (mm/8dias)',0)) or 0)
            if any(v>0 for v in pp_m):
                H.append(grafico_balance_hidrico(pp_m, et_med_v, ancho=14*cm, alto=5.5*cm))
                H.append(fig_caption(
                    'Balance hídrico mensual. Barras azules: meses con excedente hídrico. '
                    'Barras rojas: meses con déficit. Línea naranja: evapotranspiración '
                    'potencial estimada.'))
        sp(0.3)
        h3('Estadísticas de precisión — Temperatura')
        H.append(tabla_estadisticas_pro(t_med, t_std, t_min, t_max,
            0, 0, t_cnt, 'ECMWF/ERA5_LAND/MONTHLY_AGGR', '11132 m (~11 km)', per))
        nota('ERA5-Land: reanálisis ECMWF. Latencia ~3 meses. '
             'Muñoz-Sabater et al. (2021). doi:10.5194/essd-13-4349-2021')
        pag()

    # ── 8. SUELOS ─────────────────────────────────────────────────────────────
    if 'suelos' in resultados:
        res = resultados['suelos']
        per = res.get('_periodo','Estático — SoilGrids 2.0')
        sec(8, 'Propiedades del Suelo', 'SoilGrids / OpenLandMap — 250 m')
        p('SoilGrids 2.0 es un modelo predictivo global de propiedades del suelo '
          'generado con aprendizaje automático sobre ~240,000 perfiles de suelo '
          'y más de 400 covariables ambientales. Resolución de 250 m. '
          'Profundidad de muestreo: 0–5 cm.')
        sp(0.2)

        suelos_d = {k:v for k,v in res.items()
                    if not k.startswith('_') and 'stdDev' not in k
                    and k != 'N° píxeles analizados'}
        H.append(tabla_kv_pro(suelos_d))
        H.append(tab_caption('Propiedades físicas y químicas del suelo (0–5 cm de profundidad).'))
        sp(0.3)

        cl = float(res.get('Arcilla (%)',0) or 0)
        si = float(res.get('Limo (%)',0) or 0)
        sa = float(res.get('Arena (%)',0) or 0)
        if cl+si+sa > 0:
            H.append(barras_horizontales([
                ('Arcilla', cl, '#C62828'),
                ('Limo',    si, '#F57F17'),
                ('Arena',   sa, '#FDD835'),
            ], 'Composición granulométrica del suelo (%)'))
            H.append(fig_caption(
                'Distribución porcentual de las fracciones texturales del suelo. '
                f'Clase USDA: {res.get("Clase textural USDA","N/D")}.'))
        sp(0.3)

        ph = float(res.get('pH del suelo (0-5 cm)',
               res.get('pH del suelo (0-5cm)',0)) or 0)
        niv_ph = 'verde' if 5.5<=ph<=7.5 else 'amarillo' if 5.0<=ph<=8.0 else 'rojo'
        H.append(semaforo_tecnico(niv_ph,
            f'pH = {ph:.2f}',
            '5.5–7.5 óptimo  |  5.0–5.5 o 7.5–8.0 cond.  |  <5.0 o >8.0 no apto',
            f'{"pH óptimo para la mayoría de especies forestales (Aliso, Pino, Eucalipto)." if 5.5<=ph<=7.5 else "pH ligeramente ácido o alcalino — algunas especies requieren enmiendas antes de plantar." if 5.0<=ph<=8.0 else "pH extremo — requiere corrección con cal (suelos ácidos) o azufre (suelos alcalinos) antes de cualquier intervención."}'))
        sp(0.3)
        h3('Estadísticas de precisión — pH')
        H.append(tabla_estadisticas_pro(ph, float(res.get('pH stdDev',0) or 0),
            0, 14, 0, 0, int(res.get('N° píxeles analizados',0) or 0),
            'OpenLandMap/SOL (ISRIC)', '250 m', per))
        nota('SoilGrids 2.0: ~240,000 perfiles, 400+ covariables, ML con '
             'incertidumbre cuantificada. Poggio et al. (2021). doi:10.5194/soil-7-217-2021')
        pag()

    # ── 9. EROSIÓN RUSLE ──────────────────────────────────────────────────────
    if 'erosion' in resultados:
        res = resultados['erosion']
        per = res.get('_periodo','N/D')
        sec(9, 'Riesgo de Erosión RUSLE', 'SRTM + CHIRPS + DW — 30 m')
        p('El modelo RUSLE (Revised Universal Soil Loss Equation) estima la pérdida '
          'potencial de suelo por erosión hídrica integrando factores de erosividad '
          'de lluvia (R), topografía (LS) y cobertura vegetal (C). '
          'Se aplica una versión simplificada sobre datos satelitales.')
        sp(0.2)

        rusle_m  = float(res.get('Índice RUSLE medio', res.get('Indice RUSLE medio',0)) or 0)
        rusle_mx = float(res.get('Índice RUSLE máximo', res.get('Indice RUSLE maximo',0)) or 0)
        rusle_s  = float(res.get('Índice RUSLE stdDev',0) or 0)
        rusle_c  = int(res.get('N° píxeles analizados',0) or 0)
        rg       = res.get('Riesgo erosivo','Bajo')

        H.append(tabla_kv_pro({
            'Índice RUSLE medio':    f'{rusle_m:.4f}',
            'Índice RUSLE máximo':   f'{rusle_mx:.4f}',
            'Desv. estándar RUSLE':  f'{rusle_s:.4f}',
            'N° píxeles analizados': f'{rusle_c:,}',
            'Nivel de riesgo erosivo': rg,
        }))
        H.append(tab_caption('Indicadores del modelo RUSLE simplificado sobre el AOI.'))
        sp(0.3)

        niv_e = {'Bajo':'verde','Medio':'amarillo','Alto':'rojo'}.get(rg,'amarillo')
        H.append(semaforo_tecnico(niv_e,
            f'RUSLE = {rusle_m:.4f}',
            '< 0.02 bajo  |  0.02–0.10 medio  |  > 0.10 alto',
            f'Riesgo {rg}. '
            f'{"Sin obras especiales requeridas — condiciones favorables para reforestación." if rg=="Bajo" else "Se recomienda implementar terrazas de contorno y cobertura vegetal permanente." if rg=="Medio" else "Requiere obras urgentes de conservación de suelos antes de cualquier intervención forestal."}'))
        sp(0.3)

        H.append(grafico_barras(
            [('RUSLE medio', rusle_m, '#E65100'), ('RUSLE máximo', rusle_mx, '#B71C1C')],
            'Índice RUSLE: valor medio y máximo del área de interés',
            subtitulo='Valores más altos indican mayor riesgo erosivo',
            ancho=10*cm))
        H.append(fig_caption('Índice RUSLE medio y máximo calculados sobre el AOI.'))
        sp(0.3)

        p('<b>Metodología RUSLE simplificada:</b> '
          'Índice = R × LS × C, donde: '
          'R = factor erosividad (CHIRPS media diaria × 0.04), '
          'LS = factor longitud-pendiente (sin(θ)/0.0896)⁰·⁶ × (tan(θ)/0.0896)¹·³, '
          'C = factor cobertura según clase Dynamic World '
          '(bosque: 0.003, pastizal: 0.010, cultivos: 0.200, construido: 0.600).')
        nota('Wischmeier & Smith (1978). USDA Agriculture Handbook 537. '
             'Modelo RUSLE simplificado — no sustituye estudios de erosión en campo.')
        pag()

    # ── 10. EVAPOTRANSPIRACIÓN ────────────────────────────────────────────────
    if 'evapotranspiracion' in resultados:
        res = resultados['evapotranspiracion']
        per = res.get('_periodo','N/D')
        sec(10, 'Evapotranspiración Real', 'MOD16 MODIS — 500 m')
        p('El producto MOD16 estima la evapotranspiración real mediante el algoritmo '
          'de Penman-Monteith sobre imágenes MODIS. Proporciona valores cada 8 días '
          f'con resolución de 500 m. Período: {per}.')
        sp(0.2)

        et_m  = float(res.get('ET media (mm/8 días)', res.get('ET media (mm/8dias)',0)) or 0)
        et_mn = float(res.get('ET mínima (mm/8 días)', res.get('ET minima (mm/8dias)',0)) or 0)
        et_mx = float(res.get('ET máxima (mm/8 días)', res.get('ET maxima (mm/8dias)',0)) or 0)
        et_s  = float(res.get('ET stdDev (mm/8 días)',0) or 0)
        et_c  = int(res.get('N° píxeles analizados',0) or 0)

        H.append(tabla_kv_pro({
            'ET media (mm/8 días)':   f'{et_m:.2f}',
            'ET mínima (mm/8 días)':  f'{et_mn:.2f}',
            'ET máxima (mm/8 días)':  f'{et_mx:.2f}',
            'Desv. estándar (mm/8d)': f'{et_s:.2f}',
            'N° píxeles analizados':  f'{et_c:,}',
            'ET anual estimada (mm)': f'{et_m * 365 / 8:.1f}',
        }))
        H.append(tab_caption('Estadísticas de evapotranspiración real sobre el AOI.'))
        sp(0.3)

        H.append(grafico_barras([
            ('ET mínima', et_mn, '#B3E5FC'),
            ('ET media',  et_m,  '#0288D1'),
            ('ET máxima', et_mx, '#01579B'),
        ], 'Evapotranspiración real (mm/8 días)',
           subtitulo=f'Período: {per}',
           ancho=10*cm))
        H.append(fig_caption(
            'Estadísticas espaciales de la evapotranspiración real sobre el AOI.'))

        sp(0.3)
        # Índice hídrico
        if 'clima' in resultados:
            pp_tot_v = float(resultados['clima'].get('Precipitación total (mm)',
                        resultados['clima'].get('Precipitacion total (mm)',0)) or 0)
            et_anual = et_m * 365 / 8
            if et_anual > 0:
                ia = round(pp_tot_v / et_anual, 2)
                niv_ia = 'verde' if ia>1.0 else 'amarillo' if ia>0.5 else 'rojo'
                H.append(semaforo_tecnico(niv_ia,
                    f'IA = {ia:.2f}',
                    '> 1.0 húmedo  |  0.5–1.0 subhúmedo  |  < 0.5 árido',
                    f'Índice de aridez (PP/ET) = {ia:.2f}. '
                    f'{"Área húmeda — excedente hídrico favorable para la vegetación." if ia>1.0 else "Área subhúmeda — se recomienda seleccionar especies con mayor tolerancia al estrés hídrico." if ia>0.5 else "Área semiárida — requiere especies altamente tolerantes a la sequía."}'))

        sp(0.3)
        h3('Estadísticas de precisión — ET')
        H.append(tabla_estadisticas_pro(et_m, et_s, et_mn, et_mx,
            0, 0, et_c, 'MODIS/061/MOD16A2GF', '500 m', per))
        nota('MOD16: Penman-Monteith. 8 días, 500 m. '
             'Running et al. (2017). doi:10.5067/MODIS/MOD16A2.006')
        pag()

    # ── 11. DIAGNÓSTICO GENERAL ───────────────────────────────────────────────
    sec(11, 'Diagnóstico General de Aptitud para Reforestación')
    p('La siguiente tabla integra los resultados de todos los módulos analizados '
      'en un diagnóstico consolidado de aptitud para reforestación, basado en '
      'umbrales técnicos FAO/USDA.')
    sp(0.3)

    rsm = []
    if 'topografia' in resultados:
        pm = float(resultados['topografia'].get('Pendiente media (°)',
               resultados['topografia'].get('Pendiente media (grados)',0)) or 0)
        rsm.append(('Topografía','Pendiente media',f'{pm:.1f}°',
                    'APTO' if pm<15 else 'CONDICIONADO' if pm<30 else 'NO APTO',
                    pm<15, pm<30))
    if 'vegetacion' in resultados:
        nd = float(resultados['vegetacion'].get('NDVI medio',0) or 0)
        rsm.append(('Vegetación','NDVI medio',f'{nd:.4f}',
                    'BUENA' if nd>0.4 else 'MODERADA' if nd>0.2 else 'BAJA',
                    nd>0.4, nd>0.2))
    if 'suelos' in resultados:
        ph = float(resultados['suelos'].get('pH del suelo (0-5 cm)',
               resultados['suelos'].get('pH del suelo (0-5cm)',0)) or 0)
        rsm.append(('Suelos','pH del suelo',f'{ph:.2f}',
                    'ÓPTIMO' if 5.5<=ph<=7.5 else 'CONDICIONADO',
                    5.5<=ph<=7.5, True))
    if 'erosion' in resultados:
        rg  = resultados['erosion'].get('Riesgo erosivo','Bajo')
        rix = float(resultados['erosion'].get('Índice RUSLE medio',
               resultados['erosion'].get('Indice RUSLE medio',0)) or 0)
        rsm.append(('Erosión RUSLE','Riesgo erosivo',rg,
                    'BAJO' if rg=='Bajo' else 'MEDIO' if rg=='Medio' else 'ALTO',
                    rg=='Bajo', rg!='Alto'))
    if 'clima' in resultados:
        pp = float(resultados['clima'].get('Precipitación total (mm)',
               resultados['clima'].get('Precipitacion total (mm)',0)) or 0)
        rsm.append(('Precipitación','PP total anual',f'{pp:.0f} mm',
                    'ADECUADA' if pp>600 else 'MODERADA' if pp>300 else 'BAJA',
                    pp>600, pp>300))
    if 'temperatura' in resultados:
        tm = float(resultados['temperatura'].get('Temperatura media anual (°C)',
               resultados['temperatura'].get('Temperatura media anual (C)',0)) or 0)
        rsm.append(('Temperatura','T media anual',f'{tm:.1f} °C','ADECUADA',True,True))

    if rsm:
        fh = [Paragraph(x, E['tabla_h'])
              for x in ['Módulo','Indicador','Valor','Estado','Aptitud']]
        fr = []
        for mod,ind,val,est,ok,cd in rsm:
            sc_ = colors.HexColor('#C8E6C9') if ok else colors.HexColor('#FFE0B2') if cd else colors.HexColor('#FFCDD2')
            tx_ = 'APTO' if ok else 'CONDICIONADO' if cd else 'NO APTO'
            fr.append([
                Paragraph(mod, E['tabla_v']),
                Paragraph(ind, E['tabla_v']),
                Paragraph(f'<b>{val}</b>', E['tabla_vb']),
                Paragraph(est, E['tabla_v']),
                Paragraph(tx_, ParagraphStyle('apt', fontName=FNB, fontSize=9,
                    textColor=(CV if ok else CAM if cd else CRO),
                    alignment=TA_CENTER)),
            ])
        t_diag = Table([fh]+fr, colWidths=[3*cm,3.5*cm,2.5*cm,3*cm,3*cm])
        cmds_d = [
            ('BACKGROUND',    (0,0),(-1,0), colors.HexColor('#0D3B1F')),
            ('LINEABOVE',     (0,0),(-1,0),  1.2, CGR),
            ('LINEBELOW',     (0,0),(-1,0),  0.5, CGRL),
            ('LINEBELOW',     (0,-1),(-1,-1),1.0, CGR),
            ('GRID',          (0,1),(-1,-2), 0.3, colors.HexColor('#E0E0E0')),
            ('ROWBACKGROUNDS',(0,1),(-1,-1), [BL, CGRF]),
            ('VALIGN',        (0,0),(-1,-1), 'MIDDLE'),
            ('TOPPADDING',    (0,0),(-1,-1), 6),
            ('BOTTOMPADDING', (0,0),(-1,-1), 6),
            ('LEFTPADDING',   (0,0),(-1,-1), 8),
            ('ALIGN',         (4,0),(4,-1),  'CENTER'),
        ]
        for i,(mod,ind,val,est,ok,cd) in enumerate(rsm,1):
            cmds_d.append(('BACKGROUND',(4,i),(4,i),
                colors.HexColor('#E8F5E9') if ok else
                colors.HexColor('#FFF3E0') if cd else
                colors.HexColor('#FFEBEE')))
        t_diag.setStyle(TableStyle(cmds_d))
        H.append(t_diag)
        H.append(tab_caption(
            'Diagnóstico integrado de aptitud para reforestación por módulo.'))
    pag()

    # ── 12. METODOLOGÍA ───────────────────────────────────────────────────────
    sec(12, 'Metodología del Análisis')
    p('El diagnóstico fue generado mediante procesamiento en la plataforma '
      '<b>Google Earth Engine (GEE)</b> de Google, integrando ocho fuentes '
      'de datos satelitales de libre acceso. A continuación se describe la '
      'metodología aplicada en cada módulo.')
    sp(0.3)

    METS = [
        ('Topografía','USGS/SRTMGL1_003 (SRTM v3, 30 m)',
         'DEM directo. Pendiente: ee.Terrain.slope(). '
         'TWI: ln(A_acu / tan(β)), donde A_acu = área de captación acumulada '
         '(HydroSHEDS 15ACC) y β = pendiente en radianes.'),
        ('Vegetación','COPERNICUS/S2_SR_HARMONIZED (Sentinel-2 SR, 10 m)',
         'NDVI = (B8−B4)/(B8+B4). EVI = 2.5×(B8−B4)/(B8+6B4−7.5B2+1). '
         'SAVI = 1.5×(B8−B4)/(B8+B4+0.5). NDWI = (B3−B8)/(B3+B8). '
         'NDMI = (B8−B11)/(B8+B11). NBR = (B8−B12)/(B8+B12). '
         'BSI = (B11+B4−B8−B2)/(B11+B4+B8+B2). '
         'Colección filtrada por nubes < 20%, reducción por mediana.'),
        ('Cobertura','GOOGLE/DYNAMICWORLD/V1 (Dynamic World, 10 m)',
         '9 clases mediante deep learning sobre Sentinel-2. '
         'Modo de la colección del período como clase representativa por píxel.'),
        ('Precipitación','UCSB-CHG/CHIRPS/DAILY (CHIRPS v2.0, ~5 km)',
         'Suma de precipitación diaria en el período. Serie mensual: suma '
         'por mes. Estadísticas espaciales sobre el AOI.'),
        ('Temperatura','ECMWF/ERA5_LAND/MONTHLY_AGGR (ERA5-Land, ~11 km)',
         'Variable temperature_2m. Conversión K→°C: T(°C) = T(K) − 273.15. '
         'Media, mínimo y máximo de la colección mensual sobre el AOI.'),
        ('Suelos','OpenLandMap/SOL/* (SoilGrids 2.0, 250 m)',
         'pH ÷ 10. Limo = 100 − Arcilla − Arena. '
         'Densidad aparente ÷ 100. Clase textural USDA derivada.'),
        ('Erosión RUSLE','SRTM + CHIRPS + Dynamic World (30 m)',
         'RUSLE = R × LS × C. R = PP_media × 0.04. '
         'LS = (sin θ / 0.0896)⁰·⁶ × (tan θ / 0.0896)¹·³. '
         'C por clase DW: bosque=0.003, pasto=0.01, cultivos=0.2, construido=0.6.'),
        ('Evapotranspiración','MODIS/061/MOD16A2GF (MOD16, 500 m)',
         'ET real Penman-Monteith. Factor de escala 0.1. '
         'Media, mínimo y máximo sobre el AOI.'),
    ]
    filas_met = [[Paragraph(f'<b>{m[0]}</b>', E['tabla_v']),
                  Paragraph(m[1], E['tabla_v']),
                  Paragraph(m[2], ParagraphStyle('met', fontName=FN, fontSize=9,
                      textColor=CGRM, leading=13))]
                 for m in METS]
    H.append(tabla_booktabs(filas_met,
        headers=['Módulo','Dataset GEE','Metodología'],
        col_w=[2.8*cm, 4.2*cm, 8*cm]))
    H.append(tab_caption('Descripción metodológica por módulo.'))
    sp(0.3)

    # Tabla de limitaciones
    h3('Limitaciones y consideraciones técnicas')
    lims = [
        ('SRTM v3','Misión 2000 — no refleja cambios topográficos recientes',
         '±16 m vertical (90% confianza)','30 m'),
        ('Sentinel-2','Mediana del período — puede no reflejar condiciones actuales exactas',
         'Resolución nominal 10 m','10 m'),
        ('Dynamic World','Clasificación automática — errores del 5–15% en clases similares',
         'Precisión global ~83%','10 m'),
        ('CHIRPS','Interpolación combinada — menor precisión en zonas montañosas',
         'Error ~15% en áreas de topografía compleja','~5 km'),
        ('ERA5-Land','Reanálisis — no captura microclimas locales',
         'Latencia de 3 meses','~11 km'),
        ('SoilGrids 2.0','Modelo predictivo — incertidumbre alta en zonas con pocos perfiles',
         'Incertidumbre reportada ±1 unidad pH','250 m'),
    ]
    H.append(tabla_booktabs(lims,
        headers=['Dataset','Limitación principal','Precisión reportada','Resolución'],
        col_w=[2.2*cm, 6.3*cm, 4*cm, 2.5*cm]))
    H.append(tab_caption('Limitaciones técnicas de los datasets utilizados.'))
    pag()

    # ── 13. ESPECIES FORESTALES ───────────────────────────────────────────────
    sec(13, 'Especies Forestales Recomendadas')
    em2 = float(resultados.get('topografia',{}).get('Elevación media (msnm)',
           resultados.get('topografia',{}).get('Elevacion media (msnm)',0)) or 0)
    ph2 = float(resultados.get('suelos',{}).get('pH del suelo (0-5 cm)',
           resultados.get('suelos',{}).get('pH del suelo (0-5cm)',6.5)) or 6.5)
    tm2 = float(resultados.get('temperatura',{}).get('Temperatura media anual (°C)',
           resultados.get('temperatura',{}).get('Temperatura media anual (C)',15)) or 15)
    p(f'Basado en las condiciones del área de estudio (elevación: {em2:.0f} msnm, '
      f'pH: {ph2:.2f}, temperatura media: {tm2:.1f} °C), se presentan las especies '
      f'forestales con mayor probabilidad de éxito para reforestación:')
    sp(0.3)

    TODAS = [
        ('Alnus acuminata','Aliso','1800-3800','5.0-7.5','8-20','Nativa',
         'Fijadora de N₂. Riberas, pendientes. Crecimiento rápido.'),
        ('Polylepis racemosa','Quinual','3000-4500','4.5-7.0','5-14','Nativa',
         'Especie bandera de reforestación andina. Tolera heladas.'),
        ('Buddleja incana','Quishuar','3000-4200','5.0-7.5','8-16','Nativa',
         'Borde de quebradas, laderas expuestas al viento.'),
        ('Pinus radiata','Pino','1500-3500','5.5-7.0','10-22','Exótica',
         'Reforestación comercial. Alta productividad de biomasa.'),
        ('Eucalyptus globulus','Eucalipto','1500-3200','5.5-7.5','12-24','Exótica',
         'Reforestación rápida. Cuencas hídricas.'),
        ('Escallonia resinosa','Chachacomo','2500-4000','5.0-7.0','8-16','Nativa',
         'Zonas semiáridas andinas. Alta resistencia a sequía.'),
        ('Sambucus peruviana','Sauco','2000-3500','5.5-7.5','10-20','Nativa',
         'Sistemas agroforestales. Crecimiento rápido.'),
        ('Cedrela montana','Cedro andino','2000-3500','5.5-7.0','12-20','Nativa',
         'Madera valiosa. Zonas húmedas de montaña.'),
    ]
    aptas = []
    for e in TODAS:
        a_n,a_x = float(e[2].split('-')[0]), float(e[2].split('-')[1])
        p_n,p_x = float(e[3].split('-')[0]), float(e[3].split('-')[1])
        t_n,t_x = float(e[4].split('-')[0]), float(e[4].split('-')[1])
        if a_n<=em2<=a_x and p_n<=ph2<=p_x and t_n<=tm2<=t_x:
            aptas.append(e)
    if not aptas: aptas = TODAS[:5]

    filas_e = [[
        Paragraph(f'<i>{e[0]}</i>', E['tabla_v']),
        Paragraph(e[1], E['tabla_v']),
        Paragraph(e[2], ParagraphStyle('ec', fontName=FN, fontSize=9,
            textColor=CGR, alignment=TA_CENTER)),
        Paragraph(e[3], ParagraphStyle('ep', fontName=FN, fontSize=9,
            textColor=CGR, alignment=TA_CENTER)),
        Paragraph(e[4], ParagraphStyle('et', fontName=FN, fontSize=9,
            textColor=CGR, alignment=TA_CENTER)),
        Paragraph(e[5], ParagraphStyle('eo', fontName=FN, fontSize=9,
            textColor=CV if e[5]=='Nativa' else CAZ, alignment=TA_CENTER)),
        Paragraph(e[6], ParagraphStyle('eu', fontName=FN, fontSize=8.5,
            textColor=CGRM)),
    ] for e in aptas]
    t_esp = Table(
        [[Paragraph(h, E['tabla_h']) for h in
          ['Especie','Nombre común','Alt. (msnm)','pH','T (°C)','Origen','Uso / notas']]]
        + filas_e,
        colWidths=[3.5*cm, 1.8*cm, 1.8*cm, 1.4*cm, 1.4*cm, 1.4*cm, 3.7*cm])
    t_esp.setStyle(TableStyle([
        ('BACKGROUND',    (0,0),(-1,0), colors.HexColor('#0D3B1F')),
        ('LINEABOVE',     (0,0),(-1,0),  1.2, CGR),
        ('LINEBELOW',     (0,0),(-1,0),  0.5, CGRL),
        ('LINEBELOW',     (0,-1),(-1,-1),1.0, CGR),
        ('GRID',          (0,1),(-1,-2), 0.3, colors.HexColor('#E0E0E0')),
        ('ROWBACKGROUNDS',(0,1),(-1,-1), [BL, CGRF]),
        ('VALIGN',        (0,0),(-1,-1), 'MIDDLE'),
        ('ALIGN',         (2,0),(5,-1),  'CENTER'),
        ('TOPPADDING',    (0,0),(-1,-1), 5),
        ('BOTTOMPADDING', (0,0),(-1,-1), 5),
        ('LEFTPADDING',   (0,0),(-1,-1), 5),
    ]))
    H.append(t_esp)
    H.append(tab_caption(
        f'Especies forestales aptas para las condiciones del área '
        f'(elev. {em2:.0f} msnm, pH {ph2:.2f}, T {tm2:.1f} °C).'))
    nota(f'Lista filtrada automáticamente por condiciones del área. '
         'Se recomienda consultar con especialistas forestales locales '
         'y realizar pruebas de germinación antes de iniciar la plantación.')
    pag()

    # ── 14. CONCLUSIONES ──────────────────────────────────────────────────────
    sec(14, 'Conclusiones y Recomendaciones Técnicas')
    p(f'El diagnóstico geoespacial del área de estudio ({area_ha:,.1f} ha) '
      'fue realizado mediante el procesamiento en Google Earth Engine de '
      'ocho fuentes de datos satelitales. A continuación se presentan las '
      'conclusiones técnicas y recomendaciones por módulo:')
    sp(0.3)

    if 'topografia' in resultados:
        r   = resultados['topografia']
        pm  = float(r.get('Pendiente media (°)', r.get('Pendiente media (grados)',0)) or 0)
        ev  = float(r.get('Elevación media (msnm)', r.get('Elevacion media (msnm)',0)) or 0)
        twi = float(r.get('TWI medio',0) or 0)
        p(f'<b>Topografía:</b> El área presenta una elevación media de {ev:.0f} msnm '
          f'con una pendiente media de {pm:.1f}°. '
          f'{"Las condiciones topográficas son favorables para la reforestación sin necesidad de obras de ingeniería especiales." if pm<15 else "Las pendientes moderadas requieren el diseño de terrazas de contorno para garantizar la estabilidad de la plantación y reducir la escorrentía superficial." if pm<30 else "Las pendientes pronunciadas representan un riesgo alto de erosión hídrica. Se recomienda la implementación de zanjas de infiltración y barreras vivas antes de cualquier intervención forestal."} '
          f'El TWI medio de {twi:.2f} indica '
          f'{"alta capacidad de retención de humedad del suelo." if twi>7 else "capacidad de humedad del suelo moderada." if twi>5 else "baja acumulación de humedad — posible estrés hídrico estacional."}')

    if 'vegetacion' in resultados:
        nd  = float(resultados['vegetacion'].get('NDVI medio',0) or 0)
        nbr = float(resultados['vegetacion'].get('NBR medio',0) or 0)
        bsi = float(resultados['vegetacion'].get('BSI medio',0) or 0)
        p(f'<b>Vegetación:</b> El NDVI medio de {nd:.4f} indica '
          f'{"una cobertura vegetal densa y en buen estado fitosanitario." if nd>0.5 else "una cobertura vegetal moderada con posible estrés hídrico o degradación." if nd>0.3 else "una cobertura vegetal escasa o degradada — el área es prioritaria para intervención."} '
          f'El índice NBR de {nbr:.4f} '
          f'{"no sugiere afectación por incendios recientes." if nbr>0.1 else "sugiere posible afectación por incendios o alta exposición solar."} '
          f'El BSI de {bsi:.4f} indica '
          f'{"presencia significativa de suelo desnudo." if bsi>0 else "cobertura del suelo adecuada."}')

    if 'suelos' in resultados:
        ph  = float(resultados['suelos'].get('pH del suelo (0-5 cm)',
               resultados['suelos'].get('pH del suelo (0-5cm)',0)) or 0)
        ct  = resultados['suelos'].get('Clase textural USDA','N/D')
        co  = float(resultados['suelos'].get('Carbono orgánico (g/kg)',
               resultados['suelos'].get('Carbono organico (g/kg)',0)) or 0)
        p(f'<b>Suelos:</b> pH de {ph:.2f} con textura {ct} y carbono orgánico '
          f'de {co:.1f} g/kg. '
          f'{"El pH es óptimo para la mayoría de especies forestales andinas." if 5.5<=ph<=7.5 else "El pH requiere corrección con cal agrícola antes de la plantación." if ph<5.5 else "El pH alcalino puede limitar la disponibilidad de micronutrientes."} '
          f'{"El alto contenido de carbono orgánico indica suelo con buena actividad biológica." if co>30 else "Se recomienda incorporar materia orgánica para mejorar la fertilidad del suelo."}')

    if 'erosion' in resultados:
        rg  = resultados['erosion'].get('Riesgo erosivo','Bajo')
        rix = float(resultados['erosion'].get('Índice RUSLE medio',
               resultados['erosion'].get('Indice RUSLE medio',0)) or 0)
        p(f'<b>Erosión:</b> Riesgo RUSLE {rg} (índice medio: {rix:.4f}). '
          f'{"No se requieren obras especiales de conservación — el riesgo erosivo es manejable con buenas prácticas de reforestación." if rg=="Bajo" else "Se recomienda implementar terrazas de contorno, barreras vivas y mulch orgánico en las zonas de mayor pendiente." if rg=="Medio" else "Las condiciones de erosión son críticas. Es indispensable implementar obras de conservación de suelos antes de iniciar la plantación forestal."}')

    if 'clima' in resultados and 'evapotranspiracion' in resultados:
        pp  = float(resultados['clima'].get('Precipitación total (mm)',
               resultados['clima'].get('Precipitacion total (mm)',0)) or 0)
        et2 = float(resultados['evapotranspiracion'].get('ET media (mm/8 días)',
               resultados['evapotranspiracion'].get('ET media (mm/8dias)',0)) or 0)
        et_a = et2 * 365 / 8
        ia   = round(pp / et_a, 2) if et_a > 0 else 0
        p(f'<b>Clima e hidrología:</b> Precipitación anual de {pp:.0f} mm y '
          f'ET estimada de {et_a:.0f} mm/año. '
          f'Índice de aridez = {ia:.2f} '
          f'({"régimen húmedo favorable" if ia>1 else "régimen subhúmedo — evaluar disponibilidad hídrica" if ia>0.5 else "régimen semiárido — seleccionar especies resistentes a sequía"}). '
          f'Se recomienda priorizar la época de lluvias para la plantación.')

    sp(0.3)
    # Determinar aptitud general basada en resultados reales
    _apt_flags = []
    if 'topografia' in resultados:
        _pm = float(resultados['topografia'].get('Pendiente media (°)', 0) or 0)
        _apt_flags.append(_pm < 30)
    if 'suelos' in resultados:
        _ph = float(resultados['suelos'].get('pH del suelo (0-5 cm)', 6.5) or 6.5)
        _apt_flags.append(5.0 <= _ph <= 8.0)
    if 'erosion' in resultados:
        _rg = resultados['erosion'].get('Riesgo erosivo', 'Bajo')
        _apt_flags.append(_rg != 'Alto')
    if 'clima' in resultados:
        _pp = float(resultados['clima'].get('Precipitación total (mm)', 0) or 0)
        _apt_flags.append(_pp > 300)
    _n_aptos = sum(_apt_flags)
    _n_total_flags = len(_apt_flags) if _apt_flags else 1
    _ratio_apto = _n_aptos / _n_total_flags

    if _ratio_apto >= 0.75:
        _rec_general = ('favorables para reforestación con especies nativas andinas. '
                        'Se recomienda iniciar con <i>Alnus acuminata</i> (aliso) en '
                        'zonas ribereñas y <i>Polylepis racemosa</i> (quinual) en las '
                        'partes altas.')
    elif _ratio_apto >= 0.5:
        _rec_general = ('condicionadas para reforestación. Se recomienda subsanar las '
                        'limitaciones identificadas (pendiente, pH o erosión) antes de '
                        'iniciar la plantación. Priorizar especies tolerantes a estrés '
                        'como <i>Escallonia resinosa</i> (chachacomo) o '
                        '<i>Buddleja incana</i> (quishuar).')
    else:
        _rec_general = ('restrictivas para reforestación directa. Se requiere una '
                        'evaluación técnica de campo detallada y la implementación de '
                        'obras de conservación de suelos antes de cualquier intervención '
                        'forestal.')
    p(f'<b>Recomendación general:</b> El área presenta condiciones {_rec_general}')
    pag()

    # ── 15. REFERENCIAS ───────────────────────────────────────────────────────
    sec(15, 'Referencias Bibliográficas')
    refs = [
        'Brown, C. F., Brumby, S. P., Guzder-Williams, B., Birch, T., et al. (2022). '
        'Dynamic World, near real-time global 10 m land use land cover mapping. '
        '<i>Scientific Data</i>, 9, 251. https://doi.org/10.1038/s41597-022-01307-4',

        'Drusch, M., Del Bello, U., Carlier, S., Colin, O., et al. (2012). '
        'Sentinel-2: ESA\'s optical high-resolution mission for GMES operational '
        'services. <i>Remote Sensing of Environment</i>, 120, 25–36. '
        'https://doi.org/10.1016/j.rse.2011.11.026',

        'FAO. (2006). <i>Guidelines for soil description</i> (4th ed.). '
        'Food and Agriculture Organization of the United Nations.',

        'Farr, T. G., Rosen, P. A., Caro, E., Crippen, R., et al. (2007). '
        'The Shuttle Radar Topography Mission. <i>Reviews of Geophysics</i>, '
        '45(2), RG2004. https://doi.org/10.1029/2005RG000183',

        'Funk, C., Peterson, P., Landsfeld, M., Pedreros, D., et al. (2015). '
        'The climate hazards infrared precipitation with stations — a new '
        'environmental record for monitoring extremes. <i>Scientific Data</i>, '
        '2, 150066. https://doi.org/10.1038/sdata.2015.66',

        'Gorelick, N., Hancher, M., Dixon, M., Ilyushchenko, S., Thau, D., & '
        'Moore, R. (2017). Google Earth Engine: Planetary-scale geospatial '
        'analysis for everyone. <i>Remote Sensing of Environment</i>, 202, 18–27. '
        'https://doi.org/10.1016/j.rse.2017.06.031',

        'Muñoz-Sabater, J., Dutra, E., Agusti-Panareda, A., Albergel, C., et al. '
        '(2021). ERA5-Land: a state-of-the-art global reanalysis dataset for land '
        'applications. <i>Earth System Science Data</i>, 13(9), 4349–4383. '
        'https://doi.org/10.5194/essd-13-4349-2021',

        'Poggio, L., de Sousa, L. M., Batjes, N. H., Heuvelink, G. B. M., et al. '
        '(2021). SoilGrids 2.0: producing soil information for the globe with '
        'quantified spatial uncertainty. <i>SOIL</i>, 7(1), 217–240. '
        'https://doi.org/10.5194/soil-7-217-2021',

        'Running, S. W., Mu, Q., & Zhao, M. (2017). MOD16A2 MODIS/Terra Net '
        'Evapotranspiration 8-Day L4 Global 500m SIN Grid V006. '
        '<i>NASA EOSDIS Land Processes DAAC</i>. '
        'https://doi.org/10.5067/MODIS/MOD16A2.006',

        'Wischmeier, W. H., & Smith, D. D. (1978). <i>Predicting rainfall erosion '
        'losses: A guide to conservation planning</i>. USDA Agriculture Handbook 537.',
    ]
    for i, ref in enumerate(refs, 1):
        H.append(Paragraph(
            f'[{i}]  {ref}',
            ParagraphStyle(f'ref{i}', fontName=FN, fontSize=9.5,
                textColor=CGR, spaceBefore=4, spaceAfter=4, leading=14,
                leftIndent=24, firstLineIndent=-24, alignment=TA_JUSTIFY)))
    pag()

    # ── DONACIÓN ──────────────────────────────────────────────────────────────
    H.append(Spacer(1, 1.5*cm))
    don = Table([[Paragraph(
        f'<b>GeoDiagnostic es una herramienta gratuita y de código abierto.</b>'
        f'<br/><br/>'
        f'Si este diagnóstico fue útil en tu proyecto, tesis o trabajo '
        f'profesional, considera apoyar su desarrollo continuo:<br/><br/>'
        f'<b>Yape o Plin: {YAPE}</b>  —  {AUTOR}  —  {CORREO}<br/><br/>'
        f'<i>Tu aporte hace posible continuar desarrollando herramientas libres '
        f'para la comunidad SIG latinoamericana.</i>',
        ParagraphStyle('don', fontName=FN, fontSize=10,
            textColor=CGR, leading=16))]], colWidths=[15*cm])
    don.setStyle(TableStyle([
        ('BACKGROUND',   (0,0),(-1,-1), CVC),
        ('BOX',          (0,0),(-1,-1), 1.5, CVM),
        ('LINEBEFORE',   (0,0),(0,-1),  5, CV),
        ('TOPPADDING',   (0,0),(-1,-1), 18),
        ('BOTTOMPADDING',(0,0),(-1,-1), 18),
        ('LEFTPADDING',  (0,0),(-1,-1), 20),
        ('RIGHTPADDING', (0,0),(-1,-1), 20),
    ]))
    H.append(don)
    H.append(Spacer(1, 0.6*cm))

    # Pie de fuentes
    pie = Table([[Paragraph(
        f'<b>Fuentes de datos:</b> SRTM v3 (NASA/USGS) · Sentinel-2 SR (ESA/Copernicus) · '
        f'CHIRPS v2.0 (UCSB/CHG) · ERA5-Land (ECMWF) · SoilGrids/OpenLandMap (ISRIC) · '
        f'Dynamic World (Google/WRI) · MOD16 (NASA/MODIS) · FAO GAUL · HydroSHEDS (WWF)<br/>'
        f'<b>Plataforma:</b> Google Earth Engine · '
        f'<b>Plugin:</b> {VERSION} · <b>Tipografía:</b> STIX General (Scientific · '
        f'<b>Generado:</b> {datetime.now().strftime("%d/%m/%Y %H:%M")}',
        ParagraphStyle('pie', fontName=FN, fontSize=7.5,
            textColor=CGRL, leading=12))]], colWidths=[15*cm])
    pie.setStyle(TableStyle([
        ('BACKGROUND',   (0,0),(-1,-1), CGRC),
        ('TOPPADDING',   (0,0),(-1,-1), 8),
        ('BOTTOMPADDING',(0,0),(-1,-1), 8),
        ('LEFTPADDING',  (0,0),(-1,-1), 10),
    ]))
    H.append(pie)

    doc.build(H)
    return ruta_salida
