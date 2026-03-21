"""
GeoDiagnostic v1.0.7 — Generador de reporte PDF profesional
Autor: Lenin E. Julca — ljulcao_epg19@unc.edu.pe
"""
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import cm
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY, TA_RIGHT
from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer,
                                 PageBreak, Table, TableStyle, HRFlowable,
                                 BaseDocTemplate, Frame, PageTemplate, NextPageTemplate)
from reportlab.graphics.shapes import Drawing, Rect, String, Line, Wedge, Circle, Polygon
from reportlab.graphics.charts.barcharts import VerticalBarChart
from reportlab.graphics.charts.linecharts import HorizontalLineChart
from reportlab.graphics.charts.piecharts import Pie
from reportlab.graphics import renderPDF
from reportlab.platypus.flowables import Flowable
from datetime import datetime
import os

# ── Colores ──────────────────────────────────────────────────────────────────
CV   = colors.HexColor('#1B5E20')
CVM  = colors.HexColor('#2E7D32')
CVC  = colors.HexColor('#E8F5E9')
CAZ  = colors.HexColor('#0D47A1')
CAZC = colors.HexColor('#E3F2FD')
CNR  = colors.HexColor('#E65100')
CNRC = colors.HexColor('#FFF3E0')
CRO  = colors.HexColor('#C62828')
CROC = colors.HexColor('#FFEBEE')
CGR  = colors.HexColor('#37474F')
CGRC = colors.HexColor('#ECEFF1')
CAM  = colors.HexColor('#F57F17')
CAMC = colors.HexColor('#FFF8E1')
BL   = colors.white

AUTOR  = 'Lenin E. Julca'
CORREO = 'ljulcao_epg19@unc.edu.pe'
YAPE   = '+51 976 742 241'
VERSION = 'GeoDiagnostic v1.0.7'

# ── Estilos ───────────────────────────────────────────────────────────────────
def _estilos():
    E = {}
    E['h1'] = ParagraphStyle('h1', fontName='Helvetica-Bold', fontSize=14,
        textColor=CV, spaceBefore=14, spaceAfter=6, leading=18)
    E['h2'] = ParagraphStyle('h2', fontName='Helvetica-Bold', fontSize=11,
        textColor=CAZ, spaceBefore=10, spaceAfter=4, leading=14)
    E['h3'] = ParagraphStyle('h3', fontName='Helvetica-Bold', fontSize=9.5,
        textColor=CGR, spaceBefore=6, spaceAfter=3, leading=13)
    E['body'] = ParagraphStyle('body', fontName='Helvetica', fontSize=9,
        textColor=CGR, spaceBefore=2, spaceAfter=4, leading=14, alignment=TA_JUSTIFY)
    E['bullet'] = ParagraphStyle('bullet', fontName='Helvetica', fontSize=9,
        textColor=CGR, spaceBefore=2, spaceAfter=2, leading=13,
        leftIndent=12, firstLineIndent=-10)
    E['centro'] = ParagraphStyle('centro', fontName='Helvetica', fontSize=9,
        textColor=CGR, alignment=TA_CENTER, spaceAfter=4)
    E['pie_tabla'] = ParagraphStyle('pie_tabla', fontName='Helvetica', fontSize=7.5,
        textColor=CGR, alignment=TA_CENTER, spaceAfter=4)
    E['portada_titulo'] = ParagraphStyle('portada_titulo', fontName='Helvetica-Bold',
        fontSize=26, textColor=BL, alignment=TA_CENTER, spaceAfter=6, leading=32)
    E['portada_sub'] = ParagraphStyle('portada_sub', fontName='Helvetica',
        fontSize=12, textColor=colors.HexColor('#C8E6C9'),
        alignment=TA_CENTER, spaceAfter=4)
    return E


# ── Gráfico de barras ─────────────────────────────────────────────────────────
def grafico_barras(datos, titulo, ancho=14*cm, alto=6*cm, color_barra=None):
    """datos: list of (label, value)"""
    if not datos:
        return Spacer(1, 0.5*cm)
    d = Drawing(ancho, alto + 1.5*cm)
    bc = VerticalBarChart()
    bc.x, bc.y = 60, 30
    bc.width  = ancho - 80
    bc.height = alto - 20
    bc.data   = [[v for _, v in datos]]
    bc.categoryAxis.categoryNames = [lbl[:14] for lbl, _ in datos]
    bc.categoryAxis.labels.fontSize = 7
    bc.categoryAxis.labels.angle    = 25
    bc.categoryAxis.labels.dy       = -12
    bc.valueAxis.labels.fontSize    = 7
    bc.valueAxis.rangeRound         = 'both'
    bc.bars[0].fillColor = color_barra or CVM
    bc.bars[0].strokeColor = None
    d.add(bc)
    d.add(String(ancho/2, alto + 5, titulo,
                 fontSize=9, fontName='Helvetica-Bold',
                 fillColor=CGR, textAnchor='middle'))
    return d


# ── Gráfico de torta ──────────────────────────────────────────────────────────
def grafico_torta(datos, titulo, ancho=14*cm, alto=7*cm):
    """datos: list of (label, value, color_hex)"""
    if not datos:
        return Spacer(1, 0.5*cm)
    d = Drawing(ancho, alto)
    pie = Pie()
    pie.x, pie.y = 20, 20
    pie.width = pie.height = alto - 40
    pie.data   = [v for _, v, _ in datos]
    pie.labels = [f'{lbl[:10]} {v:.1f}%' for lbl, v, _ in datos]
    pie.sideLabels    = True
    pie.sideLabelsOffset = 0.05
    pie.slices.fontSize  = 7
    for i, (_, _, hex_c) in enumerate(datos):
        try:    pie.slices[i].fillColor = colors.HexColor(hex_c)
        except: pie.slices[i].fillColor = CVM
    d.add(pie)
    d.add(String(ancho/2, alto - 10, titulo,
                 fontSize=9, fontName='Helvetica-Bold',
                 fillColor=CGR, textAnchor='middle'))
    return d


# ── Gráfico de líneas (serie mensual) ────────────────────────────────────────
def grafico_lineas(datos, titulo, ylabel='', ancho=14*cm, alto=6*cm, color=None):
    """datos: list of 12 valores (ene-dic)"""
    if not datos or len(datos) < 2:
        return Spacer(1, 0.5*cm)
    d  = Drawing(ancho, alto + 1.5*cm)
    lc = HorizontalLineChart()
    lc.x, lc.y = 55, 25
    lc.width  = ancho - 75
    lc.height = alto - 20
    lc.data   = [datos]
    meses = ['Ene','Feb','Mar','Abr','May','Jun','Jul','Ago','Sep','Oct','Nov','Dic']
    lc.categoryAxis.categoryNames = meses[:len(datos)]
    lc.categoryAxis.labels.fontSize = 7
    lc.valueAxis.labels.fontSize    = 7
    lc.lines[0].strokeColor = color or CVM
    lc.lines[0].strokeWidth = 1.5
    d.add(lc)
    d.add(String(ancho/2, alto + 5, titulo,
                 fontSize=9, fontName='Helvetica-Bold',
                 fillColor=CGR, textAnchor='middle'))
    return d


# ── Semáforo visual ───────────────────────────────────────────────────────────
def semaforo_visual(nivel, ancho=14*cm):
    """nivel: 'verde'|'amarillo'|'rojo'"""
    d = Drawing(ancho, 30)
    colores_sem = {'verde': (CVM,  'APTO'),
                   'amarillo': (CAM,  'CONDICIONADO'),
                   'rojo': (CRO,  'NO APTO')}
    c, txt = colores_sem.get(nivel.lower(), (CGR, nivel.upper()))
    d.add(Rect(0, 5, ancho, 20, fillColor=c, strokeColor=None, rx=4))
    d.add(String(ancho/2, 11, txt, fontSize=9, fontName='Helvetica-Bold',
                 fillColor=BL, textAnchor='middle'))
    return d


# ── Tabla estándar ────────────────────────────────────────────────────────────
def tabla_kv(datos, col_w=None, header_color=None):
    col_w = col_w or [6*cm, 9*cm]
    hc    = header_color or CV
    rows  = [[Paragraph(f'<b>{k}</b>', ParagraphStyle('tk', fontName='Helvetica-Bold',
                fontSize=8.5, textColor=BL)),
              Paragraph(str(v), ParagraphStyle('tv', fontName='Helvetica',
                fontSize=8.5, textColor=CGR))]
             for k, v in datos.items() if not str(k).startswith('_')]
    if not rows:
        return Spacer(1, 0.2*cm)
    t = Table(rows, colWidths=col_w)
    t.setStyle(TableStyle([
        ('ROWBACKGROUNDS', (0,0), (-1,-1), [CVC, BL]),
        ('GRID',     (0,0), (-1,-1), 0.3, colors.HexColor('#CFD8DC')),
        ('VALIGN',   (0,0), (-1,-1), 'MIDDLE'),
        ('LEFTPADDING',  (0,0), (-1,-1), 7),
        ('TOPPADDING',   (0,0), (-1,-1), 4),
        ('BOTTOMPADDING',(0,0), (-1,-1), 4),
    ]))
    return t


# ── Encabezado de sección ─────────────────────────────────────────────────────
def encabezado_seccion(texto, color=CV):
    d = Drawing(15*cm, 26)
    d.add(Rect(0, 0, 15*cm, 26, fillColor=color, strokeColor=None, rx=4))
    d.add(String(10, 8, texto, fontSize=11, fontName='Helvetica-Bold',
                 fillColor=BL))
    return d


# ── Portada ───────────────────────────────────────────────────────────────────
def _fn_portada(canvas, doc, nombre_proy, area_ha, admin):
    W, H = A4
    canvas.saveState()
    canvas.setFillColor(CV)
    canvas.rect(0, 0, W, H, fill=1, stroke=0)
    canvas.setFillColor(colors.HexColor('#1B4332'))
    canvas.rect(0, H*0.55, W, H*0.45, fill=1, stroke=0)
    canvas.setFillColor(colors.HexColor('#081C0E'))
    canvas.rect(0, 0, W, H*0.22, fill=1, stroke=0)
    canvas.setStrokeColor(colors.HexColor('#4CAF50'))
    canvas.setLineWidth(1.5)
    canvas.line(2*cm, H*0.22, W-2*cm, H*0.22)
    # Pino
    cx = W/2; cy = H*0.64; sz = 100
    canvas.setFillColor(colors.HexColor('#5D4037'))
    canvas.setStrokeColor(colors.HexColor('#3E2723'))
    canvas.rect(cx-sz*0.07, cy, sz*0.14, sz*0.22, fill=1, stroke=0)
    for cop_w, cop_y, cop_h, col in [
        (0.48, cy+sz*0.18, sz*0.34, '#2E7D32'),
        (0.36, cy+sz*0.38, sz*0.32, '#1B5E20'),
        (0.22, cy+sz*0.56, sz*0.40, '#33691E'),
    ]:
        canvas.setFillColor(colors.HexColor(col))
        p = canvas.beginPath()
        p.moveTo(cx-sz*cop_w, cop_y); p.lineTo(cx+sz*cop_w, cop_y)
        p.lineTo(cx, cop_y+cop_h); p.close()
        canvas.drawPath(p, fill=1, stroke=0)
    # Textos portada
    canvas.setFillColor(BL)
    canvas.setFont('Helvetica-Bold', 28)
    canvas.drawCentredString(W/2, H*0.52, VERSION)
    canvas.setFont('Helvetica', 12)
    canvas.setFillColor(colors.HexColor('#C8E6C9'))
    canvas.drawCentredString(W/2, H*0.47, 'Reporte de Diagnostico Geoespacial')
    # Caja datos proyecto
    canvas.setFillColor(colors.HexColor('#0A2E14'))
    canvas.roundRect(2*cm, H*0.24, W-4*cm, H*0.20, 6, fill=1, stroke=0)
    canvas.setStrokeColor(colors.HexColor('#4CAF50'))
    canvas.setLineWidth(0.8)
    canvas.roundRect(2*cm, H*0.24, W-4*cm, H*0.20, 6, fill=0, stroke=1)
    filas = [
        ('Proyecto:', nombre_proy or 'Sin nombre'),
        ('Area analizada:', f'{area_ha:,.2f} ha'),
        ('Ubicacion:', admin.get('Departamento', 'N/D') + ', ' + admin.get('Pais','N/D')),
        ('Fecha:', datetime.now().strftime('%d/%m/%Y %H:%M')),
        ('Elaborado por:', AUTOR),
    ]
    y_f = H*0.42
    for k, v in filas:
        canvas.setFont('Helvetica-Bold', 8.5)
        canvas.setFillColor(colors.HexColor('#A5D6A7'))
        canvas.drawString(2.5*cm, y_f, k)
        canvas.setFont('Helvetica', 8.5)
        canvas.setFillColor(BL)
        canvas.drawString(6.5*cm, y_f, str(v)[:55])
        y_f -= 0.48*cm
    # Pie portada
    canvas.setFillColor(BL)
    canvas.setFont('Helvetica-Bold', 9)
    canvas.drawCentredString(W/2, H*0.12, AUTOR)
    canvas.setFont('Helvetica', 8)
    canvas.setFillColor(colors.HexColor('#A5D6A7'))
    canvas.drawCentredString(W/2, H*0.085, CORREO + '  |  ' + YAPE)
    canvas.restoreState()


def _fn_pagina(canvas, doc, nombre_proy):
    if doc.page <= 1:
        return
    W, H = A4
    canvas.saveState()
    canvas.setFillColor(CV)
    canvas.rect(0, H-1.4*cm, W, 1.4*cm, fill=1, stroke=0)
    canvas.setFillColor(BL)
    canvas.setFont('Helvetica-Bold', 8.5)
    canvas.drawString(2*cm, H-0.9*cm, VERSION)
    canvas.setFont('Helvetica', 8)
    canvas.setFillColor(colors.HexColor('#C8E6C9'))
    canvas.drawRightString(W-2*cm, H-0.9*cm,
        f'Proyecto: {(nombre_proy or "")[:35]}')
    canvas.setStrokeColor(colors.HexColor('#CFD8DC'))
    canvas.setLineWidth(0.5)
    canvas.line(2*cm, 1.6*cm, W-2*cm, 1.6*cm)
    canvas.setFont('Helvetica', 7.5)
    canvas.setFillColor(CGR)
    canvas.drawString(2*cm, 0.9*cm,
        f'{AUTOR}  |  {CORREO}')
    canvas.drawRightString(W-2*cm, 0.9*cm, f'Pagina {doc.page-1}')
    canvas.restoreState()


# ── FUNCIÓN PRINCIPAL ─────────────────────────────────────────────────────────
def generar_reporte(ruta_salida, nombre_proy, resultados, datos_ficha,
                    area_ha=0, modo_drive=False):
    E = _estilos()
    admin = resultados.get('_admin', {})

    doc = BaseDocTemplate(ruta_salida, pagesize=A4,
        rightMargin=2*cm, leftMargin=2*cm,
        topMargin=2.2*cm, bottomMargin=2.5*cm)

    fr_portada   = Frame(0, 0, A4[0], A4[1], id='portada',
                         leftPadding=0, rightPadding=0,
                         topPadding=0, bottomPadding=0, showBoundary=0)
    fr_contenido = Frame(2*cm, 2.5*cm, A4[0]-4*cm, A4[1]-4.7*cm,
                         id='contenido', showBoundary=0)

    pt_port = PageTemplate(id='Portada',   frames=[fr_portada],
        onPage=lambda c,d: _fn_portada(c,d, nombre_proy, area_ha, admin))
    pt_cont = PageTemplate(id='Contenido', frames=[fr_contenido],
        onPage=lambda c,d: _fn_pagina(c,d, nombre_proy))
    doc.addPageTemplates([pt_port, pt_cont])

    historia = [Spacer(1, A4[1]), NextPageTemplate('Contenido'), PageBreak()]

    def h1(txt, icono=''):
        historia.append(Spacer(1, 0.3*cm))
        historia.append(HRFlowable(width='100%', thickness=0.5,
                                    color=colors.HexColor('#4CAF50'), spaceAfter=4))
        historia.append(Paragraph(f'{icono}  {txt}' if icono else txt, E['h1']))

    def h2(txt): historia.append(Paragraph(txt, E['h2']))
    def p(txt):  historia.append(Paragraph(txt, E['body']))
    def sp(n=0.3): historia.append(Spacer(1, n*cm))
    def nueva_pag(): historia.append(PageBreak())

    def caja_info(txt, color_bg, color_borde):
        t = Table([[Paragraph(txt, ParagraphStyle('ci', fontName='Helvetica',
                    fontSize=8.5, textColor=CGR, leading=13))]],
                  colWidths=[15*cm])
        t.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,-1), color_bg),
            ('BOX',        (0,0), (-1,-1), 1.5, color_borde),
            ('LEFTPADDING',(0,0), (-1,-1), 10),
            ('TOPPADDING', (0,0), (-1,-1), 7),
            ('BOTTOMPADDING',(0,0),(-1,-1),7),
            ('ROUNDEDCORNERS',[5,5,5,5]),
        ]))
        historia.append(t); historia.append(Spacer(1,0.2*cm))

    # ── FICHA DEL AOI ─────────────────────────────────────────────────────────
    h1('1. Ficha Tecnica del Area de Interes', '📍')
    if datos_ficha:
        filas_ficha = {k:v for k,v in datos_ficha.items() if not str(k).startswith('_')}
        historia.append(tabla_kv(filas_ficha))
    sp()
    if admin:
        h2('Ubicacion administrativa')
        historia.append(tabla_kv(admin))
    sp()
    if modo_drive:
        caja_info('⚠ Area grande: los rasters fueron exportados a Google Drive. '
                  'Revisa tu carpeta GeoDiagnostic en drive.google.com',
                  CNRC, CNR)
    nueva_pag()

    # ── TOPOGRAFIA ────────────────────────────────────────────────────────────
    if 'topografia' in resultados:
        h1('2. Topografia', '🏔')
        res = resultados['topografia']
        historia.append(tabla_kv(res))
        sp()
        # Gráfico barras elevación
        elev_media = res.get('Elevacion media (msnm)', 0)
        elev_min   = res.get('Elevacion minima (msnm)', 0)
        elev_max   = res.get('Elevacion maxima (msnm)', 0)
        pend_media = res.get('Pendiente media (grados)', 0)
        datos_bar  = [('Elev. min', elev_min), ('Elev. media', elev_media),
                      ('Elev. max', elev_max)]
        historia.append(grafico_barras(datos_bar, 'Perfil altitudinal del area (msnm)',
                                       color_barra=CAZ))
        sp(0.3)
        # Semáforo pendiente
        h2('Aptitud de pendiente para reforestacion')
        if pend_media < 15:
            niv = 'verde'; txt_sem = f'Pendiente media de {pend_media:.1f} grados — APTO para reforestacion'
        elif pend_media < 30:
            niv = 'amarillo'; txt_sem = f'Pendiente media de {pend_media:.1f} grados — CONDICIONADO, requiere manejo de suelos'
        else:
            niv = 'rojo'; txt_sem = f'Pendiente media de {pend_media:.1f} grados — RIESGO ALTO de erosion'
        historia.append(semaforo_visual(niv))
        p(txt_sem)
        nueva_pag()

    # ── VEGETACION E INDICES ──────────────────────────────────────────────────
    if 'vegetacion' in resultados:
        h1('3. Vegetacion e Indices Espectrales', '🌿')
        res = resultados['vegetacion']
        ndvi_m = res.get('NDVI medio', 0)
        # Tabla indices medios
        indices_mostrar = ['NDVI','EVI','SAVI','NDWI','NDMI','NBR','BSI']
        filas_idx = {}
        desc_idx = {
            'NDVI': 'Indice de vegetacion (vegetation)',
            'EVI':  'Indice de vegetacion mejorado (dense veg.)',
            'SAVI': 'Indice ajustado por suelo',
            'NDWI': 'Indice de agua / humedad',
            'NDMI': 'Indice de humedad vegetal',
            'NBR':  'Indice de area quemada',
            'BSI':  'Indice de suelo desnudo',
        }
        for idx in indices_mostrar:
            med = res.get(f'{idx} medio', 'N/D')
            mn  = res.get(f'{idx} min',   'N/D')
            mx  = res.get(f'{idx} max',   'N/D')
            filas_idx[f'{idx} — {desc_idx.get(idx,"")}'] = f'Media: {med}  |  Min: {mn}  |  Max: {mx}'
        historia.append(tabla_kv(filas_idx, col_w=[8*cm, 7*cm]))
        sp()
        # Gráfico barras índices medios
        datos_idx = [(idx, float(res.get(f'{idx} medio', 0) or 0))
                     for idx in indices_mostrar]
        historia.append(grafico_barras(datos_idx, 'Valores medios de indices espectrales',
                                       color_barra=CVM))
        sp(0.3)
        h2('Interpretacion del NDVI')
        if ndvi_m > 0.6:     niv='verde';    txt_ndvi='Cobertura vegetal densa y saludable'
        elif ndvi_m > 0.4:   niv='verde';    txt_ndvi='Buena cobertura vegetal'
        elif ndvi_m > 0.2:   niv='amarillo'; txt_ndvi='Cobertura vegetal moderada o en estres'
        else:                niv='rojo';     txt_ndvi='Cobertura vegetal escasa o suelo desnudo'
        historia.append(semaforo_visual(niv))
        p(txt_ndvi)
        nueva_pag()

    # ── COBERTURA DYNAMIC WORLD ───────────────────────────────────────────────
    if 'cobertura' in resultados:
        h1('4. Cobertura y Uso del Suelo', '🗺')
        res = resultados['cobertura']
        CLASES_INFO = res.get('_clases_info', {})
        COLORES_DW = {
            'Agua':'#419BDF', 'Arboles':'#397D49', 'Cesped/Pasto':'#88B053',
            'Veg. inundada':'#7A87C6', 'Cultivos':'#E49635', 'Arbustos':'#DFC35A',
            'Construido':'#C4281B', 'Suelo desnudo':'#A59B8F', 'Nieve/Hielo':'#B39FE1'}
        DESCR_DW = {
            'Agua':'Cuerpos hidricos permanentes', 'Arboles':'Bosque nativo y plantaciones',
            'Cesped/Pasto':'Pastizales y praderas', 'Veg. inundada':'Bofedales y humedales',
            'Cultivos':'Tierras agricolas activas', 'Arbustos':'Matorrales y chaparrales',
            'Construido':'Zonas urbanas e infraestructura', 'Suelo desnudo':'Sin cobertura vegetal',
            'Nieve/Hielo':'Zonas glaciares y nevados'}
        clases_pct = {k:v for k,v in res.items()
                      if '(%)' in k and not k.startswith('_') and float(v or 0) > 0}
        # Tabla con descripción
        filas_cob = []
        for k, v in sorted(clases_pct.items(), key=lambda x: -float(x[1])):
            nombre = k.replace(' (%)','')
            descr  = DESCR_DW.get(nombre, '')
            filas_cob.append([
                Paragraph(f'<b>{nombre}</b>', ParagraphStyle('n',fontName='Helvetica-Bold',fontSize=8.5,textColor=CGR)),
                Paragraph(descr, ParagraphStyle('d',fontName='Helvetica',fontSize=8,textColor=CGR)),
                Paragraph(f'<b>{v}%</b>', ParagraphStyle('v',fontName='Helvetica-Bold',fontSize=8.5,textColor=CAZ,alignment=TA_CENTER)),
            ])
        if filas_cob:
            t_cob = Table(
                [[Paragraph('<b>Clase</b>',ParagraphStyle('th',fontName='Helvetica-Bold',fontSize=8.5,textColor=BL)),
                  Paragraph('<b>Descripcion</b>',ParagraphStyle('th2',fontName='Helvetica-Bold',fontSize=8.5,textColor=BL)),
                  Paragraph('<b>%</b>',ParagraphStyle('th3',fontName='Helvetica-Bold',fontSize=8.5,textColor=BL,alignment=TA_CENTER))],
                 *filas_cob],
                colWidths=[4*cm, 8.5*cm, 2.5*cm])
            t_cob.setStyle(TableStyle([
                ('BACKGROUND', (0,0),(-1,0), CV),
                ('ROWBACKGROUNDS',(0,1),(-1,-1),[BL, CVC]),
                ('GRID',(0,0),(-1,-1),0.3,colors.HexColor('#CFD8DC')),
                ('VALIGN',(0,0),(-1,-1),'MIDDLE'),
                ('TOPPADDING',(0,0),(-1,-1),4),
                ('BOTTOMPADDING',(0,0),(-1,-1),4),
                ('LEFTPADDING',(0,0),(-1,-1),7),
            ]))
            historia.append(t_cob)
            sp()
            # Gráfico torta cobertura
            datos_torta = [(k.replace(' (%)',''), float(v), COLORES_DW.get(k.replace(' (%)',''),'#9E9E9E'))
                           for k,v in sorted(clases_pct.items(), key=lambda x:-float(x[1]))]
            historia.append(grafico_torta(datos_torta[:8],
                'Distribucion de cobertura del suelo (%)'))
            sp()
            # Barras horizontales
            datos_barh = [(k.replace(' (%)',''), float(v))
                          for k,v in sorted(clases_pct.items(), key=lambda x:-float(x[1]))]
            historia.append(grafico_barras(datos_barh, 'Porcentaje por clase de cobertura'))
        nueva_pag()

    # ── CLIMA ─────────────────────────────────────────────────────────────────
    if 'clima' in resultados:
        h1('5. Precipitacion (CHIRPS)', '🌧')
        res = resultados['clima']
        filas_pp = {k:v for k,v in res.items() if 'Mes' not in k}
        historia.append(tabla_kv(filas_pp))
        sp()
        # Serie mensual
        meses_vals = [float(res.get(f'PP_Mes_{m:02d} (mm)', 0) or 0) for m in range(1,13)]
        if any(v > 0 for v in meses_vals):
            historia.append(grafico_lineas(meses_vals,
                'Precipitacion mensual acumulada (mm)',
                color=CAZ))
            historia.append(grafico_barras(
                [(f'M{m}', meses_vals[m-1]) for m in range(1,13)],
                'Precipitacion por mes (mm)', color_barra=CAZ))
        nueva_pag()

    # ── TEMPERATURA ───────────────────────────────────────────────────────────
    if 'temperatura' in resultados:
        h1('6. Temperatura (ERA5-Land)', '🌡')
        res = resultados['temperatura']
        filas_t = {k:v for k,v in res.items() if 'Mes' not in k}
        historia.append(tabla_kv(filas_t))
        sp()
        meses_t = [float(res.get(f'Temp_Mes_{m:02d} (C)', 0) or 0) for m in range(1,13)]
        if any(v != 0 for v in meses_t):
            historia.append(grafico_lineas(meses_t,
                'Temperatura media mensual (°C)',
                color=colors.HexColor('#E65100')))
        nueva_pag()

    # ── SUELOS ────────────────────────────────────────────────────────────────
    if 'suelos' in resultados:
        h1('7. Propiedades del Suelo (SoilGrids)', '🪨')
        res = resultados['suelos']
        historia.append(tabla_kv(res))
        sp()
        # Gráfico textura
        clay = float(res.get('Arcilla (%)', 0) or 0)
        silt = float(res.get('Limo (%)',    0) or 0)
        sand = float(res.get('Arena (%)',   0) or 0)
        if clay + silt + sand > 0:
            datos_tex = [('Arcilla', clay, '#C62828'),
                         ('Limo',    silt, '#F57F17'),
                         ('Arena',   sand, '#F9A825')]
            historia.append(grafico_torta(datos_tex, 'Composicion textural del suelo (%)'))
        sp()
        # Aptitud pH
        ph_v = float(res.get('pH del suelo (0-5cm)', 0) or 0)
        h2('Aptitud del pH para reforestacion')
        if 5.5 <= ph_v <= 7.5:   niv='verde';    txt_ph=f'pH {ph_v:.2f} — OPTIMO para la mayoria de especies forestales'
        elif 5.0 <= ph_v < 5.5 or 7.5 < ph_v <= 8.0:
            niv='amarillo'; txt_ph=f'pH {ph_v:.2f} — CONDICIONADO, algunas especies requieren enmiendas'
        else:  niv='rojo'; txt_ph=f'pH {ph_v:.2f} — ACIDO o ALCALINO extremo, requiere correccion'
        historia.append(semaforo_visual(niv)); p(txt_ph)
        nueva_pag()

    # ── EROSION ───────────────────────────────────────────────────────────────
    if 'erosion' in resultados:
        h1('8. Riesgo de Erosion RUSLE', '⚠')
        res = resultados['erosion']
        historia.append(tabla_kv(res))
        sp()
        riesgo = res.get('Riesgo erosivo', 'Bajo')
        niv_e  = {'Bajo':'verde','Medio':'amarillo','Alto':'rojo'}.get(riesgo,'amarillo')
        historia.append(semaforo_visual(niv_e))
        textos_erosion = {
            'Bajo':  'Riesgo erosivo BAJO — condiciones favorables para reforestacion',
            'Medio': 'Riesgo erosivo MEDIO — se recomiendan terrazas y cobertura vegetal permanente',
            'Alto':  'Riesgo erosivo ALTO — se requieren obras de conservacion antes de plantar',
        }
        p(textos_erosion.get(riesgo, ''))
        nueva_pag()

    # ── EVAPOTRANSPIRACION ────────────────────────────────────────────────────
    if 'evapotranspiracion' in resultados:
        h1('9. Evapotranspiracion (MOD16)', '💧')
        historia.append(tabla_kv(resultados['evapotranspiracion']))
        sp()
        nueva_pag()

    # ── DIAGNOSTICO GENERAL ───────────────────────────────────────────────────
    h1('10. Diagnostico General de Aptitud', '📊')
    resumen_items = []
    if 'topografia' in resultados:
        p_m = resultados['topografia'].get('Pendiente media (grados)',0)
        n = 'APTO' if p_m<15 else 'CONDICIONADO' if p_m<30 else 'NO APTO'
        resumen_items.append(('Topografia — Pendiente', n, p_m<15, p_m<30))
    if 'vegetacion' in resultados:
        ndvi = resultados['vegetacion'].get('NDVI medio',0)
        n = 'BUENA' if ndvi>0.4 else 'MODERADA' if ndvi>0.2 else 'BAJA'
        resumen_items.append(('Cobertura vegetal — NDVI', n, ndvi>0.4, ndvi>0.2))
    if 'suelos' in resultados:
        ph = resultados['suelos'].get('pH del suelo (0-5cm)',0)
        n = 'OPTIMO' if 5.5<=float(ph or 0)<=7.5 else 'CONDICIONADO'
        resumen_items.append(('Suelos — pH', n, 5.5<=float(ph or 0)<=7.5, True))
    if 'erosion' in resultados:
        riesg = resultados['erosion'].get('Riesgo erosivo','Bajo')
        n = 'BAJO' if riesg=='Bajo' else 'MEDIO' if riesg=='Medio' else 'ALTO'
        resumen_items.append(('Erosion — RUSLE', n, riesg=='Bajo', riesg!='Alto'))

    filas_res = [[
        Paragraph('<b>Variable</b>',  ParagraphStyle('r0',fontName='Helvetica-Bold',fontSize=8.5,textColor=BL)),
        Paragraph('<b>Estado</b>',    ParagraphStyle('r1',fontName='Helvetica-Bold',fontSize=8.5,textColor=BL)),
        Paragraph('<b>Semaforo</b>',  ParagraphStyle('r2',fontName='Helvetica-Bold',fontSize=8.5,textColor=BL,alignment=TA_CENTER)),
    ]]
    for var, estado, es_ok, es_cond in resumen_items:
        color_sem = colors.HexColor('#C8E6C9') if es_ok else colors.HexColor('#FFF9C4') if es_cond else colors.HexColor('#FFCDD2')
        emoji = '🟢' if es_ok else '🟡' if es_cond else '🔴'
        filas_res.append([
            Paragraph(var,    ParagraphStyle('rv',fontName='Helvetica',fontSize=8.5,textColor=CGR)),
            Paragraph(estado, ParagraphStyle('re',fontName='Helvetica-Bold',fontSize=8.5,textColor=CGR)),
            Paragraph(emoji,  ParagraphStyle('rs',fontName='Helvetica',fontSize=10,alignment=TA_CENTER)),
        ])
    t_res = Table(filas_res, colWidths=[7*cm, 5*cm, 3*cm])
    t_res.setStyle(TableStyle([
        ('BACKGROUND',(0,0),(-1,0),CV),
        ('ROWBACKGROUNDS',(0,1),(-1,-1),[BL,CVC]),
        ('GRID',(0,0),(-1,-1),0.3,colors.HexColor('#CFD8DC')),
        ('VALIGN',(0,0),(-1,-1),'MIDDLE'),
        ('TOPPADDING',(0,0),(-1,-1),5),
        ('BOTTOMPADDING',(0,0),(-1,-1),5),
        ('LEFTPADDING',(0,0),(-1,-1),7),
    ]))
    historia.append(t_res)
    nueva_pag()

    # ── CONCLUSIONES ─────────────────────────────────────────────────────────
    h1('11. Conclusiones y Recomendaciones', '📋')
    p('El presente diagnostico geoespacial fue generado mediante el analisis de '
      'multiples fuentes de datos satelitales y geoespaciales procesadas en '
      'Google Earth Engine. Los resultados presentados corresponden al area '
      f'de interes definida ({area_ha:,.1f} ha) durante el periodo de analisis '
      'especificado.')
    sp(0.3)
    if 'topografia' in resultados:
        elev = resultados['topografia'].get('Elevacion media (msnm)', 0)
        pend = resultados['topografia'].get('Pendiente media (grados)', 0)
        p(f'&#8226;  <b>Topografia:</b> El area presenta una elevacion media de '
          f'{elev} msnm y una pendiente media de {pend} grados, '
          f'lo que indica {"condiciones favorables" if pend<15 else "condiciones con restricciones"} '
          f'para actividades de reforestacion.')
    if 'vegetacion' in resultados:
        ndvi = resultados['vegetacion'].get('NDVI medio', 0)
        p(f'&#8226;  <b>Vegetacion:</b> El NDVI medio de {ndvi:.4f} indica '
          f'{"buena cobertura vegetal" if ndvi>0.4 else "cobertura moderada" if ndvi>0.2 else "cobertura escasa"} '
          f'en el area de estudio.')
    if 'suelos' in resultados:
        ph    = resultados['suelos'].get('pH del suelo (0-5cm)', 0)
        clase = resultados['suelos'].get('Clase textural USDA', 'N/D')
        p(f'&#8226;  <b>Suelos:</b> El suelo presenta pH {ph:.2f} con textura {clase}. '
          f'{"Condiciones quimicas optimas para la mayoria de especies forestales." if 5.5<=float(ph or 0)<=7.5 else "Se recomienda enmienda del suelo antes de plantar."}')
    if 'erosion' in resultados:
        riesg = resultados['erosion'].get('Riesgo erosivo','N/D')
        p(f'&#8226;  <b>Erosion:</b> El indice RUSLE indica riesgo erosivo {riesg}. '
          f'{"No se requieren obras especiales de conservacion." if riesg=="Bajo" else "Se recomienda implementar practicas de conservacion de suelos."}')
    sp(0.5)
    nueva_pag()

    # ── BLOQUE DE DONACION ────────────────────────────────────────────────────
    historia.append(Spacer(1, 1*cm))
    bloque_don = Table([[
        Paragraph(
            f'<b>¿Te fue util este reporte?</b><br/><br/>'
            f'Este diagnostico fue generado con <b>{VERSION}</b>, '
            f'un plugin gratuito para QGIS desarrollado por:<br/><br/>'
            f'<b>{AUTOR}</b>  —  {CORREO}<br/><br/>'
            f'Si este reporte te ayudo en tu proyecto, tesis o trabajo '
            f'profesional, puedes apoyar el desarrollo del plugin con '
            f'una donacion voluntaria por Yape o Plin:<br/><br/>'
            f'<b>📲  {YAPE}  —  {AUTOR}</b><br/><br/>'
            f'<i>Tu apoyo hace posible seguir desarrollando herramientas '
            f'gratuitas para la comunidad SIG latinoamericana.</i>',
            ParagraphStyle('don', fontName='Helvetica', fontSize=9.5,
                textColor=CGR, leading=16, alignment=TA_LEFT))
    ]], colWidths=[15*cm])
    bloque_don.setStyle(TableStyle([
        ('BACKGROUND',(0,0),(-1,-1), CVC),
        ('BOX',(0,0),(-1,-1),2,CVM),
        ('TOPPADDING',(0,0),(-1,-1),16),
        ('BOTTOMPADDING',(0,0),(-1,-1),16),
        ('LEFTPADDING',(0,0),(-1,-1),20),
        ('RIGHTPADDING',(0,0),(-1,-1),20),
    ]))
    historia.append(bloque_don)
    historia.append(Spacer(1, 0.5*cm))

    # Fuentes de datos
    fuentes = Table([[
        Paragraph(
            f'<b>Fuentes de datos:</b> SRTM v3 (NASA/USGS) · Sentinel-2 SR (ESA/Copernicus) · '
            f'CHIRPS v2.0 (UCSB) · ERA5-Land (ECMWF) · SoilGrids 250m (ISRIC) · '
            f'Dynamic World (Google/WRI) · MOD16 (NASA/MODIS) · FAO GAUL<br/>'
            f'<b>Generado con:</b> {VERSION} · QGIS 3.x · Python 3 · '
            f'Google Earth Engine · reportlab  —  {datetime.now().strftime("%d/%m/%Y")}',
            ParagraphStyle('f', fontName='Helvetica', fontSize=7.5,
                textColor=CGR, leading=12))
    ]], colWidths=[15*cm])
    fuentes.setStyle(TableStyle([
        ('BACKGROUND',(0,0),(-1,-1),CGRC),
        ('TOPPADDING',(0,0),(-1,-1),8),
        ('BOTTOMPADDING',(0,0),(-1,-1),8),
        ('LEFTPADDING',(0,0),(-1,-1),10),
    ]))
    historia.append(fuentes)

    doc.build(historia)
    return ruta_salida

import os
from qgis.PyQt.QtWidgets import QAction
from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtCore import QSettings


class GeoDiagnosticPlugin:
    def __init__(self, iface):
        self.iface = iface
        self.action = None
        self.dialog = None

    def initGui(self):
        icon_path = os.path.join(os.path.dirname(__file__), 'icon.png')
        icon = QIcon(icon_path)
        self.action = QAction(icon, 'GeoDiagnostic', self.iface.mainWindow())
        self.action.setToolTip('GeoDiagnostic — Diagnostico Geoespacial con Google Earth Engine')
        self.action.triggered.connect(self.run)
        self.iface.addPluginToWebMenu('GeoDiagnostic', self.action)
        self.iface.addToolBarIcon(self.action)

    def unload(self):
        self.iface.removePluginWebMenu('GeoDiagnostic', self.action)
        self.iface.removeToolBarIcon(self.action)
        if self.dialog:
            self.dialog.close()
            self.dialog = None

    def run(self):
        if self.dialog is None:
            from .geo_dialog import GeoDiagnosticDialog
            self.dialog = GeoDiagnosticDialog(self.iface)
        self.dialog.show()
        self.dialog.raise_()
        self.dialog.activateWindow()

# GeoDiagnostic

<p align="center">
  <img src="geodiagnostic/icon.png" width="80" alt="GeoDiagnostic logo"/>
</p>

<p align="center">
  <strong>Automated geospatial environmental diagnostics using Google Earth Engine</strong><br/>
  Free and open source QGIS plugin · Version 1.0.7 · Lenin E. Julca
</p>

<p align="center">
  <a href="https://plugins.qgis.org/plugins/geodiagnostic/"><img src="https://img.shields.io/badge/QGIS-Plugin%20Repository-green?logo=qgis"/></a>
  <a href="https://www.gnu.org/licenses/gpl-2.0"><img src="https://img.shields.io/badge/License-GPL%20v2-blue.svg"/></a>
  <img src="https://img.shields.io/badge/QGIS-3.16%2B-green"/>
  <img src="https://img.shields.io/badge/Python-3.9%2B-blue"/>
  <img src="https://img.shields.io/badge/Platform-Windows%20%7C%20Linux%20%7C%20macOS-lightgrey"/>
</p>

---

## What is GeoDiagnostic?

**GeoDiagnostic** is a free QGIS plugin that automates the generation of geospatial environmental baseline diagnostics by connecting to **Google Earth Engine (GEE)** as a cloud computing engine. It calculates multiple environmental variables within any area of interest (AOI) defined by the user, and exports the results as `.tif` raster files that are automatically loaded in QGIS with predefined color palettes.

The plugin generates a complete technical PDF report with charts, statistics, methodology, and bibliographic references — ready to be used in academic theses, technical reports, and environmental impact assessments.

---

## Key Features

| Module | Variables | Source | Resolution |
|--------|-----------|--------|-----------|
| **Topography** | DEM, slope, aspect, TWI | SRTM v3 | 30 m |
| **Vegetation** | NDVI, EVI, SAVI, NDWI, NDMI, NBR, BSI | Sentinel-2 SR | 10 m |
| **Land Cover** | 9 classes (Dynamic World) | Google/WRI | 10 m |
| **Precipitation** | Monthly series, annual total | CHIRPS v2.0 | 5 km |
| **Temperature** | Mean, min, max monthly | ERA5-Land | 11 km |
| **Soils** | pH, texture (USDA class), carbon, bulk density | SoilGrids 250m | 250 m |
| **Erosion** | RUSLE index (R·LS·C) | SRTM+CHIRPS+DW | 30 m |
| **Evapotranspiration** | ET real (8-day) | MOD16 MODIS | 500 m |

**Additional features:**
- AOI technical sheet: area (ha/km²), perimeter, centroid, UTM coordinates, bounding box
- Administrative location (country, department, district) via FAO GAUL
- Dual export mode: direct download (<8,000 ha) or Google Drive (>8,000 ha)
- Professional PDF report with charts, statistics, methodology and APA references
- Automatic color palettes for all output rasters
- Plugin minimizes automatically when drawing AOI polygon

---

## Requirements

### Software
- **QGIS 3.16** or higher (tested on QGIS 3.44 Solothurn)
- **Python 3.9+** (included with QGIS)
- **earthengine-api** Python library (see installation below)

### Accounts (free)
- **Gmail account** registered at [earthengine.google.com](https://earthengine.google.com)
- **Google Cloud Project** with Earth Engine API enabled ([console.cloud.google.com](https://console.cloud.google.com))

---

## Installation

### Step 1 — Install the plugin in QGIS

1. Download the latest ZIP from the [Releases](https://github.com/ljulcaoepg19-gif/geodiagnostic/releases) section
2. Open QGIS → **Plugins** → **Manage and Install Plugins**
3. Click **Install from ZIP** → select the downloaded ZIP
4. Click **Install Plugin**
5. The plugin appears under **Web → GeoDiagnostic**

### Step 2 — Install earthengine-api

GeoDiagnostic requires the `earthengine-api` library in QGIS's internal Python environment.

**Option A — OSGeo4W Shell (recommended for Windows):**
```bash
pip install earthengine-api
```

**Option B — QGIS Python Console (universal):**
```python
import subprocess, sys
subprocess.run([sys.executable, "-m", "pip", "install", "earthengine-api"], check=True)
```
Open via: Plugins → Python Console (Ctrl+Alt+P), paste the code and press Enter. Restart QGIS.

**Verify installation:**
```python
import ee
print(ee.__version__)  # Should print 1.7.x or higher
```

### Step 3 — Authenticate with Google Earth Engine

1. Open GeoDiagnostic → **Config GEE** tab
2. Enter your Gmail address and Google Cloud Project ID
3. Click **Authenticate with Google** — your browser opens
4. Accept Google permissions → return to QGIS
5. Click **Verify connection** → green indicator appears
6. Click **Save configuration**

---

## Usage

1. **Define AOI** — load a vector layer or draw a polygon on the map
2. **Set analysis period** — start and end dates
3. **Select modules** — check the variables to calculate
4. **Run** — click **Execute GeoDiagnostic**
5. **Results** — rasters load automatically in QGIS, results appear in the Results tab
6. **PDF Report** — click **Generate PDF Report** in the Results tab

For detailed instructions, see the [User Manual](geodiagnostic/manual.pdf) included in the plugin.

---

## Output Files

All output files are saved in the configured output folder under a subfolder named after your project:

```
OutputFolder/
  ProjectName/
    ProjectName_DEM.tif
    ProjectName_Slope.tif
    ProjectName_NDVI.tif
    ProjectName_LandCover.tif
    ProjectName_Precipitation.tif
    ProjectName_Temperature.tif
    ProjectName_SoilPH.tif
    ProjectName_Carbon.tif
    ProjectName_RUSLE.tif
    ProjectName_ET.tif
    ProjectName_Report.pdf
    ProjectName_AOISheet.txt
```

---

## Area Limits

| Area range | Mode | Resolution | Est. time |
|-----------|------|-----------|----------|
| < 1 ha | Warning (low pixel count) | Maximum | < 5 sec |
| 1 – 8,000 ha | **Direct download** (automatic) | Maximum | 10–60 sec |
| 8,000 – 50,000 ha | **Google Drive export** | Reduced (90m) | 2–10 min |
| > 50,000 ha | Google Drive (large area warning) | Reduced | > 10 min |

---

## Supported Geometry Types

- Single Polygon (Shapefile, GeoJSON, KML)
- MultiPolygon (Shapefile, GeoJSON, KML) — automatically handled
- Drawn polygon (interactive on QGIS canvas)

---

## Data Sources

| Dataset | Variable | Provider | License |
|---------|----------|----------|---------|
| SRTM v3 | Topography | NASA/USGS | Public domain |
| Sentinel-2 SR Harmonized | Vegetation | ESA/Copernicus | Free use |
| CHIRPS v2.0 | Precipitation | UCSB CHG | Free use |
| ERA5-Land | Temperature | ECMWF/Copernicus | Free use |
| SoilGrids 250m | Soil properties | ISRIC | CC-BY 4.0 |
| Dynamic World | Land cover | Google/WRI | CC-BY 4.0 |
| MOD16A2GF | Evapotranspiration | NASA/MODIS | Free use |
| FAO GAUL | Administrative boundaries | FAO | Non-commercial |

---

## Troubleshooting

| Error | Cause | Solution |
|-------|-------|----------|
| `No module named 'ee'` | earthengine-api not installed | Follow Step 2 above |
| `Project not found` | Wrong Project ID | Check ID in Google Cloud Console |
| `Permission denied` | GEE account not approved | Register at earthengine.google.com |
| `MultiPolygon error` | Complex KML geometry | Plugin handles automatically in v1.0.8+ |
| `Too many pixels` | AOI too large | Plugin reduces scale automatically |
| `No GEE connection on open` | Expired credentials | Re-authenticate in Config GEE tab |

---

## Changelog

### v1.0.7 (March 2026)
- Added evapotranspiration module (MOD16)
- Added 6 new spectral indices: EVI, SAVI, NDWI, NDMI, NBR, BSI
- Complete soil module: texture (USDA class), bulk density, carbon
- Professional PDF report with charts, statistics and APA references
- Dual export mode: direct download / Google Drive
- Plugin minimizes when drawing AOI polygon
- Yape/Plin donation block in About tab and PDF report

### v1.0.6 (March 2026)
- Author data updated: Lenin E. Julca
- Removed test area button
- Fixed QgsRubberBand API for QGIS 3.44

### v1.0.5 (March 2026)
- Fixed MultiPolygon import error
- Fixed plugin folder name conflict
- Fixed QgsRubberBand type argument

### v1.0.4 (March 2026)
- Updated About tab with real author data
- Added +51 prefix to phone number
- Fixed Python cache conflict on reinstall

### v1.0.3 (March 2026)
- Added AOI technical sheet panel
- Added fixed output folder (Option A)
- Added pine tree icon
- Full Spanish description in metadata

### v1.0.0–1.0.2 (March 2026)
- Initial release with GEE connection
- Basic topography, vegetation, climate, soil modules
- Area test button (Cajamarca ~500 ha)

---

## Contributing

Contributions, bug reports and feature suggestions are welcome! Please use the [Issues](https://github.com/ljulcaoepg19-gif/geodiagnostic/issues) section.

---

## Citation

If you use GeoDiagnostic in your research or technical work, please cite it as:

```
Julca, L. E. (2026). GeoDiagnostic: Automated geospatial environmental diagnostics
using Google Earth Engine (Version 1.0.7) [QGIS Plugin].
https://github.com/ljulcaoepg19-gif/geodiagnostic
```

---

## Author & Support

**Lenin E. Julca**
Remote Sensing and GIS Specialist
Universidad Nacional de Cajamarca, Peru

📧 ljulcao_epg19@unc.edu.pe
📱 +51 976 742 241

---

## Support the Project

GeoDiagnostic is free and open source. If it helped you in your project, thesis or professional work, you can support its development:

**📲 Yape or Plin: +51 976 742 241 — Lenin E. Julca**

*Any amount is welcome and greatly appreciated. Your support makes it possible to keep developing free tools for the Latin American GIS community.*

---

## License

This project is licensed under the **GNU General Public License v2.0** — see the [LICENSE](LICENSE) file for details.

This plugin uses Google Earth Engine, which requires a separate free account at [earthengine.google.com](https://earthengine.google.com). The `earthengine-api` library is licensed under the Apache License 2.0.

def classFactory(iface):
    try:
        from .plugin import GeoDiagnosticPlugin
        return GeoDiagnosticPlugin(iface)
    except Exception as e:
        from qgis.PyQt.QtWidgets import QMessageBox
        QMessageBox.critical(None, 'GeoDiagnostic — Error de carga',
            f'Error al cargar el plugin:\n\n{str(e)}\n\n'
            'Solucion: Desinstala el plugin, cierra QGIS completamente, '
            'vuelve a abrirlo e instala de nuevo desde el ZIP.')
        raise

import traceback, math
from qgis.PyQt.QtCore import QThread, pyqtSignal

LIMITE_DIRECTO_HA = 8000


class GeeWorker(QThread):
    progreso     = pyqtSignal(str, int)
    modulo_ok    = pyqtSignal(str, dict, str)
    error_modulo = pyqtSignal(str, str)
    terminado    = pyqtSignal(dict)
    error_fatal  = pyqtSignal(str)

    def __init__(self, geom_wkt, crs_epsg, modulos, project_id,
                 fecha_ini, fecha_fin, carpeta_salida, nombre_proyecto, area_ha=0):
        super().__init__()
        self.geom_wkt        = geom_wkt
        self.crs_epsg        = crs_epsg
        self.modulos         = modulos
        self.project_id      = project_id
        self.fecha_ini       = fecha_ini
        self.fecha_fin       = fecha_fin
        self.carpeta_salida  = carpeta_salida
        self.nombre_proyecto = nombre_proyecto
        self.area_ha         = area_ha
        self._cancelar       = False
        self.modo_drive      = area_ha > LIMITE_DIRECTO_HA

    def cancelar(self):
        self._cancelar = True

    def _escala(self, base):
        if self.area_ha > 50000: return max(base * 4, 90)
        if self.area_ha > 8000:  return max(base * 2, 60)
        return base

    def _url(self, img, aoi, scale, name):
        import ee
        if self.modo_drive:
            task = ee.batch.Export.image.toDrive(
                image=img, description=name, folder='GeoDiagnostic',
                fileNamePrefix=name, region=aoi, scale=scale,
                maxPixels=1e13, fileFormat='GeoTIFF')
            task.start()
            return f'DRIVE:{name}'
        return img.getDownloadURL({
            'region': aoi, 'scale': scale,
            'format': 'GEO_TIFF', 'maxPixels': 1e13, 'bestEffort': True})

    def run(self):
        try:
            import ee
            from qgis.core import (QgsCoordinateReferenceSystem,
                                   QgsCoordinateTransform, QgsProject, QgsGeometry)
            ee.Initialize(project=self.project_id)

            gq  = QgsGeometry.fromWkt(self.geom_wkt)
            sc_ = QgsCoordinateReferenceSystem(f'EPSG:{self.crs_epsg}')
            d4  = QgsCoordinateReferenceSystem('EPSG:4326')
            if sc_ != d4:
                gq.transform(QgsCoordinateTransform(sc_, d4, QgsProject.instance()))
            ring = gq.asPolygon()[0] if gq.asPolygon() else gq.asMultiPolygon()[0][0]
            aoi  = ee.Geometry.Polygon([[pt.x(), pt.y()] for pt in ring])

            RG   = {}
            tot  = len(self.modulos)
            paso = 0
            NM   = self.nombre_proyecto

            # ── TOPOGRAFIA ────────────────────────────────────────────────────
            if 'topografia' in self.modulos and not self._cancelar:
                try:
                    self.progreso.emit('Calculando topografia (SRTM + TWI)...', int(paso/tot*85))
                    sc  = self._escala(30)
                    dem = ee.Image('USGS/SRTMGL1_003').clip(aoi)
                    pen = ee.Terrain.slope(dem)
                    prad = pen.multiply(math.pi / 180)
                    try:
                        fa  = ee.Image('WWF/HydroSHEDS/15ACC').clip(aoi)
                        twi = fa.add(1).log().subtract(prad.tan().max(ee.Image(0.001)).log()).rename('TWI')
                        st_twi = twi.reduceRegion(ee.Reducer.mean(), geometry=aoi, scale=sc, maxPixels=1e13, bestEffort=True).getInfo()
                        twi_v = round(st_twi.get('TWI', 0) or 0, 3)
                        url_twi = self._url(twi, aoi, sc, f'{NM}_TWI')
                    except Exception:
                        twi_v, url_twi = 0, ''
                    KW = dict(geometry=aoi, scale=sc, maxPixels=1e13, bestEffort=True)
                    sd = dem.rename('e').reduceRegion(
                        ee.Reducer.mean().combine(ee.Reducer.minMax(), sharedInputs=True)
                        .combine(ee.Reducer.stdDev(), sharedInputs=True), **KW).getInfo()
                    sp = pen.rename('p').reduceRegion(
                        ee.Reducer.mean().combine(ee.Reducer.minMax(), sharedInputs=True), **KW).getInfo()
                    res = {
                        'Elevacion media (msnm)':   round(sd.get('e_mean', 0) or 0, 1),
                        'Elevacion minima (msnm)':  round(sd.get('e_min',  0) or 0, 1),
                        'Elevacion maxima (msnm)':  round(sd.get('e_max',  0) or 0, 1),
                        'Desv. estandar elev.':     round(sd.get('e_stdDev', 0) or 0, 2),
                        'Pendiente media (grados)': round(sp.get('p_mean', 0) or 0, 2),
                        'Pendiente maxima (grados)':round(sp.get('p_max',  0) or 0, 2),
                        'TWI medio':                twi_v,
                    }
                    urls = '|||'.join(filter(None, [
                        self._url(dem, aoi, sc, f'{NM}_DEM'),
                        self._url(pen, aoi, sc, f'{NM}_Pendiente'),
                        url_twi]))
                    self.modulo_ok.emit('topografia', res, urls)
                    RG['topografia'] = res
                except Exception as e:
                    self.error_modulo.emit('topografia', str(e))
                paso += 1

            # ── VEGETACION + INDICES ──────────────────────────────────────────
            if 'vegetacion' in self.modulos and not self._cancelar:
                try:
                    self.progreso.emit('Calculando indices espectrales (Sentinel-2)...', int(paso/tot*85))
                    sc = self._escala(10)
                    def add_indices(img):
                        ndvi = img.normalizedDifference(['B8','B4']).rename('NDVI')
                        evi  = img.expression('2.5*(NIR-R)/(NIR+6*R-7.5*B+1)',
                                  {'NIR':img.select('B8'),'R':img.select('B4'),'B':img.select('B2')}).rename('EVI')
                        savi = img.expression('(NIR-R)/(NIR+R+0.5)*1.5',
                                  {'NIR':img.select('B8'),'R':img.select('B4')}).rename('SAVI')
                        ndwi = img.normalizedDifference(['B3','B8']).rename('NDWI')
                        ndmi = img.normalizedDifference(['B8','B11']).rename('NDMI')
                        nbr  = img.normalizedDifference(['B8','B12']).rename('NBR')
                        bsi  = img.expression('(SWIR+R-NIR-B)/(SWIR+R+NIR+B)',
                                  {'SWIR':img.select('B11'),'R':img.select('B4'),
                                   'NIR':img.select('B8'),'B':img.select('B2')}).rename('BSI')
                        return img.addBands([ndvi,evi,savi,ndwi,ndmi,nbr,bsi])
                    s2 = (ee.ImageCollection('COPERNICUS/S2_SR_HARMONIZED')
                          .filterBounds(aoi).filterDate(self.fecha_ini, self.fecha_fin)
                          .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', 20))
                          .map(add_indices).median().clip(aoi))
                    indices = ['NDVI','EVI','SAVI','NDWI','NDMI','NBR','BSI']
                    st = s2.select(indices).reduceRegion(
                        ee.Reducer.mean().combine(ee.Reducer.minMax(), sharedInputs=True)
                        .combine(ee.Reducer.percentile([25, 75]), sharedInputs=True),
                        geometry=aoi, scale=sc, maxPixels=1e13, bestEffort=True).getInfo()
                    res = {}
                    for idx in indices:
                        res[f'{idx} medio'] = round(st.get(f'{idx}_mean', 0) or 0, 4)
                        res[f'{idx} min']   = round(st.get(f'{idx}_min',  0) or 0, 4)
                        res[f'{idx} max']   = round(st.get(f'{idx}_max',  0) or 0, 4)
                        res[f'{idx} p25']   = round(st.get(f'{idx}_p25',  0) or 0, 4)
                        res[f'{idx} p75']   = round(st.get(f'{idx}_p75',  0) or 0, 4)
                    urls = '|||'.join([
                        self._url(s2.select('NDVI'), aoi, sc, f'{NM}_NDVI'),
                        self._url(s2.select('EVI'),  aoi, sc, f'{NM}_EVI'),
                        self._url(s2.select('SAVI'), aoi, sc, f'{NM}_SAVI'),
                        self._url(s2.select('NDWI'), aoi, sc, f'{NM}_NDWI'),
                        self._url(s2.select('NBR'),  aoi, sc, f'{NM}_NBR'),
                        self._url(s2.select('BSI'),  aoi, sc, f'{NM}_BSI'),
                    ])
                    self.modulo_ok.emit('vegetacion', res, urls)
                    RG['vegetacion'] = res
                except Exception as e:
                    self.error_modulo.emit('vegetacion', str(e))
                paso += 1

            # ── COBERTURA DYNAMIC WORLD ───────────────────────────────────────
            if 'cobertura' in self.modulos and not self._cancelar:
                try:
                    self.progreso.emit('Calculando cobertura del suelo (Dynamic World)...', int(paso/tot*85))
                    sc = self._escala(10)
                    dw = (ee.ImageCollection('GOOGLE/DYNAMICWORLD/V1')
                          .filterBounds(aoi).filterDate(self.fecha_ini, self.fecha_fin)
                          .select('label').mode().clip(aoi))
                    CLASES = {
                        0:('Agua',          '#419BDF','Cuerpos hidricos permanentes'),
                        1:('Arboles',       '#397D49','Bosque nativo y plantaciones'),
                        2:('Cesped/Pasto',  '#88B053','Pastizales y praderas'),
                        3:('Veg. inundada', '#7A87C6','Bofedales y humedales'),
                        4:('Cultivos',      '#E49635','Tierras agricolas activas'),
                        5:('Arbustos',      '#DFC35A','Matorrales y chaparrales'),
                        6:('Construido',    '#C4281B','Zonas urbanas e infraestructura'),
                        7:('Suelo desnudo', '#A59B8F','Sin cobertura vegetal'),
                        8:('Nieve/Hielo',   '#B39FE1','Zonas glaciares y nevados'),
                    }
                    hist = dw.reduceRegion(
                        ee.Reducer.frequencyHistogram(),
                        geometry=aoi, scale=sc, maxPixels=1e13, bestEffort=True
                    ).getInfo().get('label', {})
                    total_px = sum(hist.values()) if hist else 1
                    res = {}
                    for k, v in hist.items():
                        ki  = int(float(k))
                        nom = CLASES.get(ki, (f'Clase_{ki}','#9E9E9E',''))[0]
                        res[f'{nom} (%)'] = round(v / total_px * 100, 2)
                    res['_clases_info'] = {str(k): {'nombre':v[0],'color':v[1],'descripcion':v[2]} for k,v in CLASES.items()}
                    self.modulo_ok.emit('cobertura', res, self._url(dw, aoi, sc, f'{NM}_Cobertura'))
                    RG['cobertura'] = res
                except Exception as e:
                    self.error_modulo.emit('cobertura', str(e))
                paso += 1

            # ── CLIMA ─────────────────────────────────────────────────────────
            if 'clima' in self.modulos and not self._cancelar:
                try:
                    self.progreso.emit('Calculando precipitacion (CHIRPS)...', int(paso/tot*85))
                    chirps = (ee.ImageCollection('UCSB-CHG/CHIRPS/DAILY')
                              .filterBounds(aoi).filterDate(self.fecha_ini, self.fecha_fin)
                              .select('precipitation'))
                    pp_tot = chirps.sum().clip(aoi)
                    st = pp_tot.reduceRegion(
                        ee.Reducer.mean().combine(ee.Reducer.minMax(), sharedInputs=True),
                        geometry=aoi, scale=5566, maxPixels=1e13, bestEffort=True).getInfo()
                    meses = {}
                    for m in range(1, 13):
                        v = (chirps.filter(ee.Filter.calendarRange(m,m,'month'))
                             .sum().reduceRegion(ee.Reducer.mean(),
                             geometry=aoi,scale=5566,maxPixels=1e13,bestEffort=True).getInfo())
                        meses[f'PP_Mes_{m:02d} (mm)'] = round(v.get('precipitation',0) or 0, 1)
                    res = {
                        'Precipitacion total (mm)':   round(st.get('precipitation_mean',0) or 0,1),
                        'Precipitacion minima (mm)':  round(st.get('precipitation_min', 0) or 0,1),
                        'Precipitacion maxima (mm)':  round(st.get('precipitation_max', 0) or 0,1),
                        **meses}
                    self.modulo_ok.emit('clima', res, self._url(pp_tot, aoi, 5566, f'{NM}_Precipitacion'))
                    RG['clima'] = res
                except Exception as e:
                    self.error_modulo.emit('clima', str(e))
                paso += 1

            # ── TEMPERATURA ───────────────────────────────────────────────────
            if 'temperatura' in self.modulos and not self._cancelar:
                try:
                    self.progreso.emit('Calculando temperatura (ERA5-Land)...', int(paso/tot*85))
                    era5 = (ee.ImageCollection('ECMWF/ERA5_LAND/MONTHLY_AGGR')
                            .filterBounds(aoi).filterDate(self.fecha_ini, self.fecha_fin)
                            .select('temperature_2m'))
                    t_med = era5.mean().subtract(273.15).clip(aoi)
                    t_min = era5.min().subtract(273.15).clip(aoi)
                    t_max = era5.max().subtract(273.15).clip(aoi)
                    def tm(img): return img.reduceRegion(ee.Reducer.mean(),geometry=aoi,scale=11132,maxPixels=1e13,bestEffort=True).getInfo().get('temperature_2m',0) or 0
                    meses = {}
                    for m in range(1,13):
                        v = (era5.filter(ee.Filter.calendarRange(m,m,'month'))
                             .mean().subtract(273.15)
                             .reduceRegion(ee.Reducer.mean(),geometry=aoi,scale=11132,maxPixels=1e13,bestEffort=True).getInfo())
                        meses[f'Temp_Mes_{m:02d} (C)'] = round(v.get('temperature_2m',0) or 0, 1)
                    res = {
                        'Temperatura media anual (C)': round(tm(t_med),1),
                        'Temperatura minima (C)':       round(tm(t_min),1),
                        'Temperatura maxima (C)':       round(tm(t_max),1),
                        **meses}
                    self.modulo_ok.emit('temperatura', res, self._url(t_med, aoi, 11132, f'{NM}_Temperatura'))
                    RG['temperatura'] = res
                except Exception as e:
                    self.error_modulo.emit('temperatura', str(e))
                paso += 1

            # ── SUELOS COMPLETOS ──────────────────────────────────────────────
            if 'suelos' in self.modulos and not self._cancelar:
                try:
                    self.progreso.emit('Calculando propiedades del suelo (SoilGrids)...', int(paso/tot*85))
                    sc = self._escala(250)
                    def gm(img, band):
                        return img.clip(aoi).reduceRegion(ee.Reducer.mean(),geometry=aoi,scale=sc,maxPixels=1e13,bestEffort=True).getInfo().get(band,0) or 0
                    ph   = ee.Image('OpenLandMap/SOL/SOL_PH-H2O_USDA-4C1A2A_M/v02').select('b0')
                    carb = ee.Image('OpenLandMap/SOL/SOL_ORGANIC-CARBON_USDA-6A1C_M/v02').select('b0')
                    clay = ee.Image('OpenLandMap/SOL/SOL_CLAY-WFRACTION_USDA-3A1A1A_M/v02').select('b0')
                    sand = ee.Image('OpenLandMap/SOL/SOL_SAND-WFRACTION_USDA-3A1A1A_M/v02').select('b0')
                    bulk = ee.Image('OpenLandMap/SOL/SOL_BULKDENS-FINEEARTH_USDA-4A1H_M/v02').select('b0')
                    v_ph   = gm(ph,   'b0') / 10.0
                    v_carb = gm(carb, 'b0')
                    v_clay = gm(clay, 'b0')
                    v_sand = gm(sand, 'b0')
                    v_silt = max(0, 100 - v_clay - v_sand)
                    v_bulk = gm(bulk, 'b0') / 100.0
                    # Clase textural USDA
                    def ctusda(c, sa, si):
                        if c>=40 and sa<=45 and si<40:   return 'Arcilloso'
                        elif c>=40 and si>=40:            return 'Arcillo limoso'
                        elif c>=35 and sa>=45:            return 'Arcillo arenoso'
                        elif c>=28 and sa<45 and si<28:  return 'Franco arcilloso'
                        elif c>=27 and si>=28 and si<40: return 'Franco arcillo limoso'
                        elif c>=20 and sa>=45:            return 'Franco arcillo arenoso'
                        elif si>=80 and c<12:             return 'Limoso'
                        elif si>=50 and c<27:             return 'Franco limoso'
                        elif sa>=85:                      return 'Arenoso'
                        elif sa>=70 and c<15:             return 'Franco arenoso'
                        else:                             return 'Franco'
                    res = {
                        'pH del suelo (0-5cm)':       round(v_ph,   2),
                        'Carbono organico (g/kg)':    round(v_carb, 1),
                        'Arcilla (%)':                round(v_clay, 1),
                        'Limo (%)':                   round(v_silt, 1),
                        'Arena (%)':                  round(v_sand, 1),
                        'Clase textural USDA':        ctusda(v_clay, v_sand, v_silt),
                        'Densidad aparente (g/cm3)':  round(v_bulk, 2),
                    }
                    urls = '|||'.join([
                        self._url(ph.clip(aoi),   aoi, sc, f'{NM}_pH'),
                        self._url(clay.clip(aoi), aoi, sc, f'{NM}_Arcilla'),
                        self._url(carb.clip(aoi), aoi, sc, f'{NM}_Carbono'),
                    ])
                    self.modulo_ok.emit('suelos', res, urls)
                    RG['suelos'] = res
                except Exception as e:
                    self.error_modulo.emit('suelos', str(e))
                paso += 1

            # ── EROSION RUSLE ─────────────────────────────────────────────────
            if 'erosion' in self.modulos and not self._cancelar:
                try:
                    self.progreso.emit('Calculando riesgo de erosion RUSLE...', int(paso/tot*85))
                    sc   = self._escala(30)
                    dem  = ee.Image('USGS/SRTMGL1_003').clip(aoi)
                    pend = ee.Terrain.slope(dem)
                    prad = pend.multiply(math.pi/180)
                    ls   = prad.sin().divide(0.0896).pow(0.6).multiply(prad.tan().divide(0.0896).pow(1.3)).rename('LS')
                    chirps_r = (ee.ImageCollection('UCSB-CHG/CHIRPS/DAILY')
                                .filterBounds(aoi).filterDate(self.fecha_ini,self.fecha_fin)
                                .select('precipitation').mean().clip(aoi))
                    dw_e = (ee.ImageCollection('GOOGLE/DYNAMICWORLD/V1')
                            .filterBounds(aoi).filterDate(self.fecha_ini,self.fecha_fin)
                            .select('label').mode().clip(aoi))
                    c_factor = dw_e.remap(list(range(9)),[0.001,0.003,0.01,0.005,0.2,0.02,0.6,0.4,0.0]).rename('C').toFloat()
                    rusle = chirps_r.multiply(0.04).multiply(ls).multiply(c_factor).rename('RUSLE')
                    st = rusle.reduceRegion(
                        ee.Reducer.mean().combine(ee.Reducer.minMax(),sharedInputs=True),
                        geometry=aoi,scale=sc,maxPixels=1e13,bestEffort=True).getInfo()
                    media = st.get('RUSLE_mean') or 0
                    res = {
                        'Indice RUSLE medio':  round(media, 4),
                        'Indice RUSLE maximo': round(st.get('RUSLE_max',0) or 0, 4),
                        'Riesgo erosivo': 'Bajo' if media<0.02 else 'Medio' if media<0.1 else 'Alto',
                    }
                    self.modulo_ok.emit('erosion', res, self._url(rusle, aoi, sc, f'{NM}_RUSLE'))
                    RG['erosion'] = res
                except Exception as e:
                    self.error_modulo.emit('erosion', str(e))
                paso += 1

            # ── EVAPOTRANSPIRACION ────────────────────────────────────────────
            if 'evapotranspiracion' in self.modulos and not self._cancelar:
                try:
                    self.progreso.emit('Calculando evapotranspiracion (MOD16)...', int(paso/tot*85))
                    sc = self._escala(500)
                    et = (ee.ImageCollection('MODIS/061/MOD16A2GF')
                          .filterBounds(aoi).filterDate(self.fecha_ini,self.fecha_fin)
                          .select('ET').mean().multiply(0.1).clip(aoi))
                    st = et.reduceRegion(
                        ee.Reducer.mean().combine(ee.Reducer.minMax(),sharedInputs=True),
                        geometry=aoi,scale=sc,maxPixels=1e13,bestEffort=True).getInfo()
                    res = {
                        'ET media (mm/8dias)':  round(st.get('ET_mean',0) or 0,2),
                        'ET minima (mm/8dias)': round(st.get('ET_min', 0) or 0,2),
                        'ET maxima (mm/8dias)': round(st.get('ET_max', 0) or 0,2),
                    }
                    self.modulo_ok.emit('evapotranspiracion', res, self._url(et, aoi, sc, f'{NM}_ET'))
                    RG['evapotranspiracion'] = res
                except Exception as e:
                    self.error_modulo.emit('evapotranspiracion', str(e))
                paso += 1

            # ── ADMINISTRATIVO ────────────────────────────────────────────────
            if not self._cancelar:
                try:
                    self.progreso.emit('Obteniendo datos administrativos (FAO GAUL)...', 93)
                    info = (ee.FeatureCollection('FAO/GAUL/2015/level2')
                            .filterBounds(aoi).first()
                            .toDictionary(['ADM0_NAME','ADM1_NAME','ADM2_NAME']).getInfo())
                    RG['_admin'] = {
                        'Pais':         info.get('ADM0_NAME','N/D'),
                        'Departamento': info.get('ADM1_NAME','N/D'),
                        'Distrito':     info.get('ADM2_NAME','N/D'),
                    }
                    if 'topografia' in RG:
                        RG['_admin']['Altitud media (msnm)'] = RG['topografia'].get('Elevacion media (msnm)','N/D')
                except Exception:
                    RG['_admin'] = {}

            self.progreso.emit('Diagnostico completado.', 100)
            self.terminado.emit(RG)

        except Exception as e:
            self.error_fatal.emit(f'{str(e)}\n\n{traceback.format_exc()}')

import os, json, math, subprocess, sys, urllib.request, shutil
from datetime import datetime, date

from qgis.PyQt.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTabWidget, QWidget,
    QLabel, QLineEdit, QPushButton, QCheckBox, QProgressBar,
    QTableWidget, QTableWidgetItem, QFileDialog, QMessageBox,
    QGroupBox, QGridLayout, QDateEdit, QComboBox, QTextEdit,
    QSizePolicy, QScrollArea, QFrame, QSplitter
)
from qgis.PyQt.QtCore import Qt, QDate, QSettings, QTimer, QUrl
from qgis.PyQt.QtGui import QColor, QFont, QDesktopServices, QPixmap, QPainter, QBrush, QPen

from qgis.core import (
    QgsProject, QgsRasterLayer, QgsVectorLayer,
    QgsGeometry, QgsPointXY, QgsCoordinateReferenceSystem,
    QgsCoordinateTransform, QgsDistanceArea
)
try:
    from qgis.core import QgsUnitTypes
except ImportError:
    QgsUnitTypes = None
try:
    from qgis.core import QgsLayerTreeGroup
except ImportError:
    QgsLayerTreeGroup = None
from qgis.gui import QgsMapToolEmitPoint, QgsRubberBand

try:
    import ee
    EE_DISPONIBLE = True
except ImportError:
    EE_DISPONIBLE = False


# ── Colores ──────────────────────────────────────────────────────────────────
VERDE      = '#1B5E20'
VERDE_M    = '#2E7D32'
VERDE_C    = '#E8F5E9'
AZUL       = '#0D47A1'
AZUL_C     = '#E3F2FD'
NARANJA    = '#E65100'
NARANJA_C  = '#FFF3E0'
ROJO       = '#C62828'
ROJO_C     = '#FFEBEE'
GRIS       = '#37474F'
GRIS_C     = '#ECEFF1'


def estilo_boton_primario():
    return (f'QPushButton {{background:{VERDE_M};color:white;border:none;'
            f'border-radius:5px;padding:8px 16px;font-weight:bold;font-size:12px;}}'
            f'QPushButton:hover {{background:{VERDE};}}'
            f'QPushButton:disabled {{background:#9E9E9E;}}')

def estilo_boton_secundario():
    return (f'QPushButton {{background:white;color:{GRIS};border:1px solid #B0BEC5;'
            f'border-radius:5px;padding:6px 14px;font-size:11px;}}'
            f'QPushButton:hover {{background:{GRIS_C};}}')

def estilo_boton_naranja():
    return (f'QPushButton {{background:{NARANJA};color:white;border:none;'
            f'border-radius:5px;padding:7px 14px;font-weight:bold;font-size:11px;}}'
            f'QPushButton:hover {{background:#BF360C;}}')


class GeoDiagnosticDialog(QDialog):
    def __init__(self, iface):
        super().__init__(iface.mainWindow())
        self.iface = iface
        self.canvas = iface.mapCanvas()
        self.setWindowTitle('GeoDiagnostic v1.0.7 — Diagnostico Geoespacial')
        self.setMinimumSize(820, 680)
        self.resize(900, 720)
        self.setStyleSheet('QDialog {background:#FAFAFA;} QTabWidget::pane {border:1px solid #CFD8DC;}')

        self._aoi_geom = None
        self._aoi_crs_epsg = None
        self._rubber = None
        self._puntos_poly = []
        self._tool_dibujo = None
        self._worker = None
        self._resultados = {}

        self._settings = QSettings('GeoDiagnostic', 'GeoDiagnostic')
        self._construir_ui()
        self._cargar_config()
        QTimer.singleShot(600, self._auto_conectar_gee)

    # ══════════════════════════════════════════════════════════════════════════
    # UI PRINCIPAL
    # ══════════════════════════════════════════════════════════════════════════
    def _construir_ui(self):
        layout_main = QVBoxLayout(self)
        layout_main.setContentsMargins(0, 0, 0, 0)
        layout_main.setSpacing(0)

        # ── Barra de estado GEE ───────────────────────────────────────────────
        self._barra_estado = QLabel('  ⬤  Sin conexion a GEE — Configure en la pestana Config GEE')
        self._barra_estado.setStyleSheet(
            f'background:{ROJO};color:white;padding:6px 12px;font-size:11px;font-weight:bold;')
        self._barra_estado.setFixedHeight(32)
        layout_main.addWidget(self._barra_estado)

        # ── Tabs ──────────────────────────────────────────────────────────────
        self._tabs = QTabWidget()
        self._tabs.setStyleSheet(
            'QTabBar::tab {padding:8px 18px;font-size:11px;min-width:120px;}'
            f'QTabBar::tab:selected {{background:{VERDE_C};color:{VERDE};font-weight:bold;'
            f'border-bottom:2px solid {VERDE_M};}}'
        )
        layout_main.addWidget(self._tabs)

        self._tabs.addTab(self._tab_config(),      '⚙  Config GEE')
        self._tabs.addTab(self._tab_herramienta(), '🛰  Herramienta')
        self._tabs.addTab(self._tab_resultados(),  '📊  Resultados')
        self._tabs.addTab(self._tab_acerca(),      'ℹ  Acerca de')

    # ══════════════════════════════════════════════════════════════════════════
    # PESTAÑA 1 — CONFIG GEE
    # ══════════════════════════════════════════════════════════════════════════
    def _tab_config(self):
        w = QWidget()
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        contenido = QWidget()
        vl = QVBoxLayout(contenido)
        vl.setContentsMargins(20, 20, 20, 20)
        vl.setSpacing(14)

        def grupo(titulo, color=VERDE):
            g = QGroupBox(titulo)
            g.setStyleSheet(
                f'QGroupBox {{font-weight:bold;color:{color};border:1px solid #CFD8DC;'
                f'border-radius:6px;margin-top:8px;padding:10px;}}'
                f'QGroupBox::title {{subcontrol-origin:margin;left:10px;padding:0 4px;}}')
            return g

        # ── Conexion GEE ──────────────────────────────────────────────────────
        g1 = grupo('Conexion a Google Earth Engine')
        gl1 = QGridLayout(g1)

        gl1.addWidget(QLabel('Gmail:'), 0, 0)
        self._inp_gmail = QLineEdit(); self._inp_gmail.setPlaceholderText('tu.correo@gmail.com')
        gl1.addWidget(self._inp_gmail, 0, 1)

        gl1.addWidget(QLabel('Project ID:'), 1, 0)
        self._inp_project = QLineEdit(); self._inp_project.setPlaceholderText('mi-proyecto-123456-ab')
        gl1.addWidget(self._inp_project, 1, 1)

        hl_btn = QHBoxLayout()
        self._btn_auth = QPushButton('🔑  Autenticar con Google')
        self._btn_auth.setStyleSheet(estilo_boton_primario())
        self._btn_auth.clicked.connect(self._autenticar_gee)
        self._btn_verificar = QPushButton('🔗  Verificar conexion')
        self._btn_verificar.setStyleSheet(estilo_boton_secundario())
        self._btn_verificar.clicked.connect(self._verificar_gee)
        hl_btn.addWidget(self._btn_auth)
        hl_btn.addWidget(self._btn_verificar)
        hl_btn.addStretch()
        gl1.addLayout(hl_btn, 2, 0, 1, 2)
        vl.addWidget(g1)

        # ── Carpeta de salida ─────────────────────────────────────────────────
        g2 = grupo('Archivos de salida')
        gl2 = QGridLayout(g2)

        gl2.addWidget(QLabel('Nombre del proyecto:'), 0, 0)
        self._inp_nombre_proy = QLineEdit()
        self._inp_nombre_proy.setPlaceholderText('Ej: Microcuenca_Cajamarca_2026')
        gl2.addWidget(self._inp_nombre_proy, 0, 1)

        gl2.addWidget(QLabel('Carpeta de salida:'), 1, 0)
        hl_carp = QHBoxLayout()
        self._inp_carpeta = QLineEdit()
        self._inp_carpeta.setPlaceholderText('Selecciona la carpeta donde se guardaran los rasters...')
        self._btn_carpeta = QPushButton('📁')
        self._btn_carpeta.setFixedWidth(36)
        self._btn_carpeta.clicked.connect(self._seleccionar_carpeta)
        hl_carp.addWidget(self._inp_carpeta)
        hl_carp.addWidget(self._btn_carpeta)
        gl2.addLayout(hl_carp, 1, 1)
        vl.addWidget(g2)

        # ── Guardar config ────────────────────────────────────────────────────
        self._btn_guardar = QPushButton('💾  Guardar configuracion')
        self._btn_guardar.setStyleSheet(estilo_boton_primario())
        self._btn_guardar.clicked.connect(self._guardar_config)
        vl.addWidget(self._btn_guardar)

        # ── Info GEE ──────────────────────────────────────────────────────────
        info = QLabel(
            '<b>Primera vez:</b> Necesitas una cuenta Gmail registrada en '
            '<a href="https://earthengine.google.com">earthengine.google.com</a> '
            'y un Google Cloud Project con la Earth Engine API habilitada.<br>'
            'Consulta la Seccion 2 del manual para instrucciones detalladas.')
        info.setStyleSheet(f'background:{AZUL_C};color:{GRIS};padding:10px;'
                           f'border-radius:5px;font-size:11px;')
        info.setOpenExternalLinks(True)
        info.setWordWrap(True)
        vl.addWidget(info)
        vl.addStretch()

        scroll.setWidget(contenido)
        lv = QVBoxLayout(w)
        lv.setContentsMargins(0, 0, 0, 0)
        lv.addWidget(scroll)
        return w

    # ══════════════════════════════════════════════════════════════════════════
    # PESTAÑA 2 — HERRAMIENTA
    # ══════════════════════════════════════════════════════════════════════════
    def _tab_herramienta(self):
        w = QWidget()
        hl_main = QHBoxLayout(w)
        hl_main.setContentsMargins(12, 12, 12, 12)
        hl_main.setSpacing(10)

        # ── Panel izquierdo (controles) ───────────────────────────────────────
        panel_izq = QWidget()
        panel_izq.setMaximumWidth(420)
        vl = QVBoxLayout(panel_izq)
        vl.setContentsMargins(0, 0, 0, 0)
        vl.setSpacing(10)

        def grupo(titulo, color=VERDE):
            g = QGroupBox(titulo)
            g.setStyleSheet(
                f'QGroupBox {{font-weight:bold;color:{color};border:1px solid #CFD8DC;'
                f'border-radius:6px;margin-top:8px;padding:10px;}}'
                f'QGroupBox::title {{subcontrol-origin:margin;left:10px;padding:0 4px;}}')
            return g

        # AOI
        g_aoi = grupo('Area de estudio (AOI)')
        vl_aoi = QVBoxLayout(g_aoi)

        hl_capa = QHBoxLayout()
        hl_capa.addWidget(QLabel('Capa vectorial:'))
        self._cmb_capas = QComboBox(); self._cmb_capas.setMinimumWidth(180)
        self._btn_refrescar_capas = QPushButton('↻')
        self._btn_refrescar_capas.setFixedWidth(28)
        self._btn_refrescar_capas.clicked.connect(self._refrescar_capas)
        hl_capa.addWidget(self._cmb_capas)
        hl_capa.addWidget(self._btn_refrescar_capas)
        vl_aoi.addLayout(hl_capa)

        self._btn_usar_capa = QPushButton('✔  Usar capa seleccionada')
        self._btn_usar_capa.setStyleSheet(estilo_boton_secundario())
        self._btn_usar_capa.clicked.connect(self._usar_capa)
        vl_aoi.addWidget(self._btn_usar_capa)

        self._btn_dibujar = QPushButton('✏  Activar dibujo de poligono')
        self._btn_dibujar.setStyleSheet(estilo_boton_secundario())
        self._btn_dibujar.clicked.connect(self._activar_dibujo)
        vl_aoi.addWidget(self._btn_dibujar)

        self._btn_limpiar_aoi = QPushButton('🗑  Limpiar AOI')
        self._btn_limpiar_aoi.setStyleSheet(estilo_boton_secundario())
        self._btn_limpiar_aoi.clicked.connect(self._limpiar_aoi)
        vl_aoi.addWidget(self._btn_limpiar_aoi)

        vl.addWidget(g_aoi)

        # Fechas
        g_fechas = grupo('Periodo de analisis')
        gl_f = QGridLayout(g_fechas)
        gl_f.addWidget(QLabel('Fecha inicio:'), 0, 0)
        self._fecha_ini = QDateEdit()
        self._fecha_ini.setDate(QDate.currentDate().addMonths(-12))
        self._fecha_ini.setCalendarPopup(True)
        gl_f.addWidget(self._fecha_ini, 0, 1)
        gl_f.addWidget(QLabel('Fecha fin:'), 1, 0)
        self._fecha_fin = QDateEdit()
        self._fecha_fin.setDate(QDate.currentDate())
        self._fecha_fin.setCalendarPopup(True)
        gl_f.addWidget(self._fecha_fin, 1, 1)
        vl.addWidget(g_fechas)

        # Modulos
        g_mod = grupo('Modulos de analisis')
        vl_mod = QVBoxLayout(g_mod)
        self._chk_modulos = {}
        modulos_lista = [
            ('topografia',         '🏔  Topografia — DEM, pendiente, TWI (SRTM 30m)'),
            ('vegetacion',         '🌿  Vegetacion — NDVI, EVI, SAVI, NDWI, NBR, BSI (S2 10m)'),
            ('cobertura',          '🗺  Cobertura del suelo (Dynamic World 10m)'),
            ('clima',              '🌧  Precipitacion mensual (CHIRPS)'),
            ('temperatura',        '🌡  Temperatura media/minima mensual (ERA5)'),
            ('suelos',             '🪨  Suelos — pH, textura, carbono, densidad (SoilGrids)'),
            ('erosion',            '⚠  Riesgo de erosion RUSLE'),
            ('evapotranspiracion', '💧  Evapotranspiracion real (MOD16 500m)'),
        ]
        for key, label in modulos_lista:
            chk = QCheckBox(label)
            chk.setChecked(True)
            chk.setStyleSheet('QCheckBox {font-size:11px;}')
            self._chk_modulos[key] = chk
            vl_mod.addWidget(chk)
        vl.addWidget(g_mod)

        # Boton ejecutar
        self._btn_ejecutar = QPushButton('▶  Ejecutar GeoDiagnostico')
        self._btn_ejecutar.setStyleSheet(estilo_boton_primario())
        self._btn_ejecutar.setFixedHeight(42)
        self._btn_ejecutar.clicked.connect(self._ejecutar)
        vl.addWidget(self._btn_ejecutar)

        self._btn_cancelar = QPushButton('⏹  Cancelar')
        self._btn_cancelar.setStyleSheet(estilo_boton_secundario())
        self._btn_cancelar.setEnabled(False)
        self._btn_cancelar.clicked.connect(self._cancelar_ejecucion)
        vl.addWidget(self._btn_cancelar)

        self._progreso_global = QProgressBar()
        self._progreso_global.setStyleSheet(
            f'QProgressBar {{height:18px;border-radius:4px;background:#E0E0E0;}}'
            f'QProgressBar::chunk {{background:{VERDE_M};border-radius:4px;}}')
        self._progreso_global.setValue(0)
        vl.addWidget(self._progreso_global)

        self._lbl_progreso = QLabel('')
        self._lbl_progreso.setStyleSheet(f'color:{GRIS};font-size:10px;')
        vl.addWidget(self._lbl_progreso)
        vl.addStretch()

        # ── Panel derecho (ficha AOI) ─────────────────────────────────────────
        panel_der = QWidget()
        panel_der.setMinimumWidth(280)
        vl_der = QVBoxLayout(panel_der)
        vl_der.setContentsMargins(0, 0, 0, 0)

        lbl_ficha_titulo = QLabel('📍  Ficha del Area de Interes')
        lbl_ficha_titulo.setStyleSheet(
            f'background:{VERDE_M};color:white;padding:8px 12px;'
            f'font-weight:bold;font-size:12px;border-radius:5px 5px 0 0;')
        vl_der.addWidget(lbl_ficha_titulo)

        self._ficha_widget = QWidget()
        self._ficha_widget.setStyleSheet(
            f'background:white;border:1px solid #CFD8DC;border-top:none;'
            f'border-radius:0 0 5px 5px;')
        self._ficha_layout = QVBoxLayout(self._ficha_widget)
        self._ficha_layout.setContentsMargins(12, 10, 12, 10)
        self._ficha_layout.setSpacing(4)

        self._lbl_sin_aoi = QLabel(
            'Defina un area de interes\n'
            'para ver la ficha geometrica.')
        self._lbl_sin_aoi.setStyleSheet(
            f'color:#9E9E9E;font-size:11px;padding:20px;')
        self._lbl_sin_aoi.setAlignment(Qt.AlignCenter)
        self._ficha_layout.addWidget(self._lbl_sin_aoi)
        self._ficha_layout.addStretch()

        vl_der.addWidget(self._ficha_widget)

        self._btn_exportar_ficha = QPushButton('💾  Exportar ficha AOI (.txt)')
        self._btn_exportar_ficha.setStyleSheet(estilo_boton_secundario())
        self._btn_exportar_ficha.setEnabled(False)
        self._btn_exportar_ficha.clicked.connect(self._exportar_ficha_txt)
        vl_der.addWidget(self._btn_exportar_ficha)
        vl_der.addStretch()

        hl_main.addWidget(panel_izq)
        hl_main.addWidget(panel_der, 1)
        self._refrescar_capas()
        return w

    # ══════════════════════════════════════════════════════════════════════════
    # PESTAÑA 3 — RESULTADOS
    # ══════════════════════════════════════════════════════════════════════════
    def _tab_resultados(self):
        w = QWidget()
        vl = QVBoxLayout(w)
        vl.setContentsMargins(14, 14, 14, 14)

        lbl = QLabel('📊  Tabla de indicadores del diagnostico')
        lbl.setStyleSheet(f'font-weight:bold;font-size:13px;color:{VERDE};')
        vl.addWidget(lbl)

        self._tabla_resultados = QTableWidget(0, 4)
        self._tabla_resultados.setHorizontalHeaderLabels(
            ['Modulo', 'Indicador', 'Valor', 'Aptitud'])
        self._tabla_resultados.horizontalHeader().setStretchLastSection(True)
        self._tabla_resultados.setColumnWidth(0, 120)
        self._tabla_resultados.setColumnWidth(1, 260)
        self._tabla_resultados.setColumnWidth(2, 120)
        self._tabla_resultados.setEditTriggers(QTableWidget.NoEditTriggers)
        self._tabla_resultados.setAlternatingRowColors(True)
        self._tabla_resultados.setStyleSheet(
            'QTableWidget {font-size:11px;} '
            'QHeaderView::section {background:#37474F;color:white;padding:6px;font-weight:bold;}')
        vl.addWidget(self._tabla_resultados)

        hl_btns = QHBoxLayout()
        self._btn_exportar_csv = QPushButton('📄  Exportar CSV')
        self._btn_exportar_csv.setStyleSheet(estilo_boton_secundario())
        self._btn_exportar_csv.clicked.connect(self._exportar_csv)
        self._btn_exportar_json = QPushButton('📋  Exportar JSON')
        self._btn_exportar_json.setStyleSheet(estilo_boton_secundario())
        self._btn_exportar_json.clicked.connect(self._exportar_json)
        self._btn_generar_pdf = QPushButton('📑  Generar Reporte PDF')
        self._btn_generar_pdf.setStyleSheet(estilo_boton_primario())
        self._btn_generar_pdf.clicked.connect(self._generar_pdf)
        self._btn_limpiar_tabla = QPushButton('🗑  Limpiar tabla')
        self._btn_limpiar_tabla.setStyleSheet(estilo_boton_secundario())
        self._btn_limpiar_tabla.clicked.connect(self._limpiar_tabla)
        hl_btns.addWidget(self._btn_generar_pdf)
        hl_btns.addWidget(self._btn_exportar_csv)
        hl_btns.addWidget(self._btn_exportar_json)
        hl_btns.addWidget(self._btn_limpiar_tabla)
        hl_btns.addStretch()
        vl.addLayout(hl_btns)

        self._lbl_estado_result = QLabel('')
        self._lbl_estado_result.setStyleSheet(f'color:{GRIS};font-size:11px;')
        vl.addWidget(self._lbl_estado_result)
        return w

    # ══════════════════════════════════════════════════════════════════════════
    # PESTAÑA 4 — ACERCA DE
    # ══════════════════════════════════════════════════════════════════════════
    def _tab_acerca(self):
        w = QWidget()
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        contenido = QWidget()
        vl = QVBoxLayout(contenido)
        vl.setContentsMargins(30, 24, 30, 24)
        vl.setSpacing(16)

        # ── Cabecera con pino ────────────────────────────────────────────────
        hl_cab = QHBoxLayout()
        lbl_pino = QLabel()
        lbl_pino.setFixedSize(72, 72)
        pix = self._generar_pino_pixmap(72)
        lbl_pino.setPixmap(pix)
        hl_cab.addWidget(lbl_pino)
        vl_cab = QVBoxLayout()
        lbl_nombre = QLabel('GeoDiagnostic')
        lbl_nombre.setStyleSheet(f'font-size:22px;font-weight:bold;color:{VERDE};')
        lbl_version = QLabel('Version 1.0.6  |  Plugin para QGIS 3.x')
        lbl_version.setStyleSheet(f'font-size:11px;color:{GRIS};')
        lbl_desc = QLabel('Diagnostico geoespacial automatico con Google Earth Engine')
        lbl_desc.setStyleSheet(f'font-size:12px;color:{GRIS};')
        vl_cab.addWidget(lbl_nombre)
        vl_cab.addWidget(lbl_version)
        vl_cab.addWidget(lbl_desc)
        hl_cab.addLayout(vl_cab)
        hl_cab.addStretch()
        vl.addLayout(hl_cab)

        vl.addWidget(self._separador())

        # ── Autor ─────────────────────────────────────────────────────────────
        autor_widget = QWidget()
        autor_widget.setStyleSheet(
            f'background:{AZUL_C};border:1px solid #90CAF9;border-radius:6px;')
        autor_vl = QVBoxLayout(autor_widget)
        autor_vl.setContentsMargins(16, 12, 16, 12)
        autor_vl.setSpacing(4)
        lbl_autor_titulo = QLabel('Desarrollado por')
        lbl_autor_titulo.setStyleSheet(
            f'font-size:10px;font-weight:bold;color:{AZUL};text-transform:uppercase;')
        autor_vl.addWidget(lbl_autor_titulo)
        lbl_autor_nombre = QLabel('Lenin E. Julca')
        lbl_autor_nombre.setStyleSheet(
            f'font-size:17px;font-weight:bold;color:{AZUL};'
            f'background:#E3F2FD;border-radius:4px;padding:4px 10px;'
            f'border-left:4px solid {AZUL};')
        autor_vl.addWidget(lbl_autor_nombre)
        for icono, dato in [
            ('✉', 'ljulcao_epg19@unc.edu.pe'),
            ('📱', '+51 976 742 241'),
        ]:
            lbl_d = QLabel(f'  {icono}  {dato}')
            lbl_d.setStyleSheet(f'font-size:11px;color:{GRIS};')
            lbl_d.setTextInteractionFlags(Qt.TextSelectableByMouse)
            autor_vl.addWidget(lbl_d)
        vl.addWidget(autor_widget)

        vl.addWidget(self._separador())

        # ── Descripcion ───────────────────────────────────────────────────────
        desc = QLabel(
            'GeoDiagnostic automatiza la generacion de diagnosticos ambientales de '
            'linea base conectandose a Google Earth Engine como motor de calculo en la '
            'nube. Calcula topografia, vegetacion, cobertura, clima, suelos, carbono '
            'organico y riesgo de erosion RUSLE para cualquier area de interes definida '
            'en el mapa, y exporta los resultados como archivos raster .tif con paletas '
            'de color predefinidas, cargados automaticamente en QGIS.')
        desc.setWordWrap(True)
        desc.setStyleSheet(f'font-size:11px;color:{GRIS};line-height:1.6;')
        vl.addWidget(desc)

        vl.addWidget(self._separador())

        # ── Bloque de apoyo ───────────────────────────────────────────────────
        apoyo_widget = QWidget()
        apoyo_widget.setStyleSheet(
            f'background:{VERDE_C};border:2px solid {VERDE_M};border-radius:8px;')
        apoyo_vl = QVBoxLayout(apoyo_widget)
        apoyo_vl.setContentsMargins(20, 16, 20, 16)

        lbl_apoyo_titulo = QLabel('¿Te fue util GeoDiagnostic?')
        lbl_apoyo_titulo.setStyleSheet(
            f'font-size:14px;font-weight:bold;color:{VERDE};')
        apoyo_vl.addWidget(lbl_apoyo_titulo)

        lbl_apoyo_texto = QLabel(
            'Este plugin es gratuito y de codigo abierto. Si te ayudo en tu proyecto, '
            'tesis o trabajo profesional, puedes apoyar su desarrollo:')
        lbl_apoyo_texto.setWordWrap(True)
        lbl_apoyo_texto.setStyleSheet(f'font-size:11px;color:{GRIS};')
        apoyo_vl.addWidget(lbl_apoyo_texto)

        # Caja Yape / Plin destacada
        yape_widget = QWidget()
        yape_widget.setStyleSheet(
            'background:white;border:1px solid #A5D6A7;border-radius:6px;')
        yape_vl = QVBoxLayout(yape_widget)
        yape_vl.setContentsMargins(14, 10, 14, 10)
        yape_vl.setSpacing(4)
        lbl_yape_titulo = QLabel('📲  Apoya con Yape o Plin')
        lbl_yape_titulo.setStyleSheet(
            f'font-size:12px;font-weight:bold;color:{VERDE};')
        yape_vl.addWidget(lbl_yape_titulo)
        lbl_yape_inst = QLabel('  Abre Yape o Plin y busca este número:')
        lbl_yape_inst.setStyleSheet(f'font-size:10px;color:#757575;')
        yape_vl.addWidget(lbl_yape_inst)
        lbl_yape_num = QLabel('  +51 976 742 241  —  Lenin E. Julca')
        lbl_yape_num.setStyleSheet(
            f'font-size:14px;font-weight:bold;color:{VERDE};letter-spacing:1px;'
            f'background:{VERDE_C};border-radius:4px;padding:4px 8px;')
        lbl_yape_num.setTextInteractionFlags(Qt.TextSelectableByMouse)
        yape_vl.addWidget(lbl_yape_num)
        lbl_yape_nota = QLabel('  Cualquier monto es bienvenido — gracias por tu apoyo.')
        lbl_yape_nota.setStyleSheet(f'font-size:10px;color:#757575;font-style:italic;')
        yape_vl.addWidget(lbl_yape_nota)
        apoyo_vl.addWidget(yape_widget)

        for icono, texto in [
            ('🐛', 'Reporta errores o sugiere mejoras por correo'),
            ('📢', 'Compartelo con colegas que trabajen con SIG'),
        ]:
            lbl_item = QLabel(f'  {icono}  {texto}')
            lbl_item.setStyleSheet(f'font-size:11px;color:{GRIS};padding:2px 0;')
            apoyo_vl.addWidget(lbl_item)

        lbl_apoyo_final = QLabel(
            '<i>Tu apoyo hace posible seguir desarrollando herramientas gratuitas '
            'para la comunidad SIG latinoamericana.</i>')
        lbl_apoyo_final.setWordWrap(True)
        lbl_apoyo_final.setStyleSheet(f'font-size:10px;color:{GRIS};margin-top:6px;')
        apoyo_vl.addWidget(lbl_apoyo_final)

        hl_apoyo_btns = QHBoxLayout()
        btn_contacto = QPushButton('✉  Contactar por correo')
        btn_contacto.setStyleSheet(estilo_boton_primario())
        btn_contacto.clicked.connect(
            lambda: QDesktopServices.openUrl(
                QUrl('mailto:ljulcao_epg19@unc.edu.pe?subject=GeoDiagnostic%20Plugin')))
        btn_manual = QPushButton('📖  Abrir Manual PDF')
        btn_manual.setStyleSheet(estilo_boton_secundario())
        btn_manual.clicked.connect(self._abrir_manual)
        hl_apoyo_btns.addWidget(btn_contacto)
        hl_apoyo_btns.addWidget(btn_manual)
        hl_apoyo_btns.addStretch()
        apoyo_vl.addLayout(hl_apoyo_btns)
        vl.addWidget(apoyo_widget)

        vl.addWidget(self._separador())

        # ── Creditos ──────────────────────────────────────────────────────────
        creditos = QLabel(
            '<b>Autor:</b> Lenin E. Julca<br>'
            '<b>Correo:</b> ljulcao_epg19@unc.edu.pe<br>'
            '<b>Telefono:</b> 976 742 241<br><br>'
            '<b>Fuentes de datos:</b><br>'
            'SRTM v3 — NASA/USGS (dominio publico)<br>'
            'Sentinel-2 SR Harmonized — ESA/Copernicus (libre uso)<br>'
            'CHIRPS v2.0 — UCSB Climate Hazards Group (libre uso)<br>'
            'ERA5-Land — ECMWF/Copernicus (libre uso)<br>'
            'SoilGrids 250m — ISRIC (CC-BY 4.0)<br>'
            'Dynamic World — Google/WRI (CC-BY 4.0)<br>'
            'FAO GAUL — FAO (uso no comercial)<br><br>'
            '<b>Tecnologias:</b> QGIS 3.x · Python 3 · PyQt5 · '
            'Google Earth Engine API · reportlab')
        creditos.setWordWrap(True)
        creditos.setStyleSheet(
            f'background:{GRIS_C};padding:14px;border-radius:6px;'
            f'font-size:10px;color:{GRIS};line-height:1.6;')
        vl.addWidget(creditos)
        vl.addStretch()

        scroll.setWidget(contenido)
        lv = QVBoxLayout(w)
        lv.setContentsMargins(0, 0, 0, 0)
        lv.addWidget(scroll)
        return w

    def _separador(self):
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setStyleSheet('color:#CFD8DC;')
        return line

    def _generar_pino_pixmap(self, size):
        pix = QPixmap(size, size)
        pix.fill(Qt.transparent)
        p = QPainter(pix)
        p.setRenderHint(QPainter.Antialiasing)
        cx = size // 2
        # Tronco
        from qgis.PyQt.QtGui import QPolygon
        from qgis.PyQt.QtCore import QPoint
        p.setPen(Qt.NoPen)
        # Tronco — abajo del todo
        p.setBrush(QBrush(QColor('#5D4037')))
        p.drawRect(cx - size//14, size - size//4, size//7, size//4)
        # Copa base — parte baja del arbol
        p.setBrush(QBrush(QColor('#2E7D32')))
        p.drawPolygon(QPolygon([
            QPoint(int(cx - size*0.46), int(size*0.78)),
            QPoint(int(cx + size*0.46), int(size*0.78)),
            QPoint(cx, int(size*0.44))]))
        # Copa media
        p.setBrush(QBrush(QColor('#1B5E20')))
        p.drawPolygon(QPolygon([
            QPoint(int(cx - size*0.34), int(size*0.60)),
            QPoint(int(cx + size*0.34), int(size*0.60)),
            QPoint(cx, int(size*0.28))]))
        # Copa superior — punta arriba
        p.setBrush(QBrush(QColor('#33691E')))
        p.drawPolygon(QPolygon([
            QPoint(int(cx - size*0.22), int(size*0.42)),
            QPoint(int(cx + size*0.22), int(size*0.42)),
            QPoint(cx, int(size*0.04))]))
        p.end()
        return pix

    # ══════════════════════════════════════════════════════════════════════════
    # LOGICA GEE
    # ══════════════════════════════════════════════════════════════════════════
    def _auto_conectar_gee(self):
        if not EE_DISPONIBLE:
            return
        project = self._settings.value('gee_project', '')
        if not project:
            return
        try:
            import ee
            ee.Initialize(project=project)
            self._set_estado_gee(True, project)
        except Exception:
            pass

    def _autenticar_gee(self):
        if not EE_DISPONIBLE:
            QMessageBox.warning(self, 'Libreria no encontrada',
                'La libreria earthengine-api no esta instalada.\n\n'
                'Abre la consola de Python de QGIS y ejecuta:\n\n'
                'import subprocess, sys\n'
                'subprocess.run([sys.executable, "-m", "pip",\n'
                '    "install", "earthengine-api"], check=True)')
            return
        try:
            import ee
            ee.Authenticate()
            QMessageBox.information(self, 'Autenticacion',
                'Autenticacion completada.\nAhora haz clic en "Verificar conexion".')
        except Exception as e:
            QMessageBox.critical(self, 'Error de autenticacion', str(e))

    def _verificar_gee(self):
        if not EE_DISPONIBLE:
            self._set_estado_gee(False)
            return
        project = self._inp_project.text().strip()
        if not project:
            QMessageBox.warning(self, 'Falta Project ID',
                'Escribe tu Google Cloud Project ID antes de verificar.')
            return
        try:
            import ee
            ee.Initialize(project=project)
            img = ee.Image(1)
            img.getInfo()
            self._set_estado_gee(True, project)
            QMessageBox.information(self, 'Conexion exitosa',
                f'✅ Conectado correctamente al proyecto:\n{project}')
        except Exception as e:
            self._set_estado_gee(False)
            QMessageBox.critical(self, 'Error de conexion',
                f'No se pudo conectar a GEE:\n\n{str(e)}\n\n'
                'Verifica que el Project ID sea correcto y que la '
                'Earth Engine API este habilitada en Google Cloud Console.')

    def _set_estado_gee(self, ok, project=''):
        if ok:
            self._barra_estado.setText(
                f'  ⬤  GEE conectado  ·  proyecto: {project}')
            self._barra_estado.setStyleSheet(
                'background:#1B5E20;color:white;padding:6px 12px;'
                'font-size:11px;font-weight:bold;')
        else:
            self._barra_estado.setText(
                '  ⬤  Sin conexion a GEE — Configure en la pestana Config GEE')
            self._barra_estado.setStyleSheet(
                f'background:{ROJO};color:white;padding:6px 12px;'
                f'font-size:11px;font-weight:bold;')

    # ══════════════════════════════════════════════════════════════════════════
    # CONFIG — GUARDAR / CARGAR
    # ══════════════════════════════════════════════════════════════════════════
    def _guardar_config(self):
        self._settings.setValue('gee_gmail',   self._inp_gmail.text().strip())
        self._settings.setValue('gee_project', self._inp_project.text().strip())
        self._settings.setValue('carpeta_salida', self._inp_carpeta.text().strip())
        self._settings.setValue('nombre_proyecto', self._inp_nombre_proy.text().strip())
        QMessageBox.information(self, 'Configuracion guardada',
            'La configuracion se guardo correctamente.\n'
            'No necesitaras volver a ingresarla la proxima vez.')

    def _cargar_config(self):
        self._inp_gmail.setText(self._settings.value('gee_gmail', ''))
        self._inp_project.setText(self._settings.value('gee_project', ''))
        self._inp_carpeta.setText(self._settings.value('carpeta_salida', ''))
        self._inp_nombre_proy.setText(self._settings.value('nombre_proyecto', ''))

    def _seleccionar_carpeta(self):
        carpeta = QFileDialog.getExistingDirectory(
            self, 'Seleccionar carpeta de salida para los rasters', '')
        if carpeta:
            self._inp_carpeta.setText(carpeta)

    # ══════════════════════════════════════════════════════════════════════════
    # AOI
    # ══════════════════════════════════════════════════════════════════════════
    def _refrescar_capas(self):
        self._cmb_capas.clear()
        self._cmb_capas.addItem('-- Seleccionar capa --', None)
        for nombre, capa in QgsProject.instance().mapLayers().items():
            if isinstance(capa, QgsVectorLayer):
                self._cmb_capas.addItem(capa.name(), nombre)

    def _usar_capa(self):
        idx = self._cmb_capas.currentIndex()
        if idx <= 0:
            QMessageBox.warning(self, 'Sin capa', 'Selecciona una capa vectorial primero.')
            return
        nombre_id = self._cmb_capas.currentData()
        capa = QgsProject.instance().mapLayer(nombre_id)
        if not capa:
            return
        geom = None
        for feat in capa.getFeatures():
            geom = feat.geometry()
            break
        if geom is None:
            QMessageBox.warning(self, 'Sin geometria', 'La capa no tiene geometrias.')
            return
        self._aoi_geom = geom.asWkt()
        self._aoi_crs_epsg = capa.crs().postgisSrid()
        self._dibujar_rubber(geom, capa.crs())
        self._calcular_ficha_aoi(geom, capa.crs())

    def _activar_dibujo(self):
        self._puntos_poly = []
        if self._rubber:
            self._rubber.reset()
        from qgis.core import QgsWkbTypes
        self._rubber = QgsRubberBand(self.canvas, QgsWkbTypes.LineGeometry)
        self._rubber.setColor(QColor(30, 94, 32, 160))
        self._rubber.setWidth(2)
        self._tool_dibujo = QgsMapToolEmitPoint(self.canvas)
        self._tool_dibujo.canvasClicked.connect(self._click_mapa)
        self.canvas.setMapTool(self._tool_dibujo)
        self._btn_dibujar.setText('✏  Dibujando... (doble clic para cerrar)')
        self._btn_dibujar.setStyleSheet(
            f'QPushButton {{background:{NARANJA};color:white;border:none;'
            f'border-radius:5px;padding:6px 14px;font-size:11px;}}')
        self._click_count = 0
        self.showMinimized()

    def _click_mapa(self, point, button):
        self._click_count = getattr(self, '_click_count', 0) + 1
        if button == Qt.RightButton or self._click_count > 1:
            if len(self._puntos_poly) >= 3:
                self._cerrar_poligono()
            return
        self._puntos_poly.append(QgsPointXY(point.x(), point.y()))
        self._rubber.addPoint(point)
        self._click_count = 0

    def _cerrar_poligono(self):
        if len(self._puntos_poly) < 3:
            return
        ring = [(p.x(), p.y()) for p in self._puntos_poly]
        ring.append(ring[0])
        wkt = 'POLYGON((' + ','.join(f'{x} {y}' for x, y in ring) + '))'
        geom = QgsGeometry.fromWkt(wkt)
        self._aoi_geom = wkt
        self._aoi_crs_epsg = self.canvas.mapSettings().destinationCrs().postgisSrid()
        crs = self.canvas.mapSettings().destinationCrs()
        self._dibujar_rubber(geom, crs)
        self._calcular_ficha_aoi(geom, crs)
        self.canvas.unsetMapTool(self._tool_dibujo)
        self._btn_dibujar.setText('✏  Activar dibujo de poligono')
        self._btn_dibujar.setStyleSheet(estilo_boton_secundario())
        self.showNormal()
        self.raise_()
        self.activateWindow()

    def _area_prueba(self):
        wkt = ('POLYGON((-78.52 -7.12, -78.48 -7.12, -78.48 -7.08, '
               '-78.52 -7.08, -78.52 -7.12))')
        geom = QgsGeometry.fromWkt(wkt)
        crs = QgsCoordinateReferenceSystem('EPSG:4326')
        self._aoi_geom = wkt
        self._aoi_crs_epsg = 4326
        self._dibujar_rubber(geom, crs)
        self._calcular_ficha_aoi(geom, crs)
        # Zoom al area
        try:
            xform = QgsCoordinateTransform(crs,
                self.canvas.mapSettings().destinationCrs(),
                QgsProject.instance())
            extent = geom.boundingBox()
            extent = xform.transformBoundingBox(extent)
            self.canvas.setExtent(extent)
            self.canvas.refresh()
        except Exception:
            pass

    def _dibujar_rubber(self, geom, crs):
        from qgis.core import QgsWkbTypes
        if self._rubber:
            self._rubber.reset()
        self._rubber = QgsRubberBand(self.canvas, QgsWkbTypes.PolygonGeometry)
        self._rubber.setColor(QColor(30, 94, 32, 80))
        self._rubber.setStrokeColor(QColor(30, 94, 32, 220))
        self._rubber.setWidth(2)
        dst_crs = self.canvas.mapSettings().destinationCrs()
        if crs != dst_crs:
            geom_t = QgsGeometry(geom)
            xform = QgsCoordinateTransform(crs, dst_crs, QgsProject.instance())
            geom_t.transform(xform)
            self._rubber.setToGeometry(geom_t, dst_crs)
        else:
            self._rubber.setToGeometry(geom, crs)

    def _limpiar_aoi(self):
        self._aoi_geom = None
        self._aoi_crs_epsg = None
        if self._rubber:
            self._rubber.reset()
        self._limpiar_ficha()

    def _calcular_ficha_aoi(self, geom, crs):
        try:
            d = QgsDistanceArea()
            d.setSourceCrs(crs, QgsProject.instance().transformContext())
            d.setEllipsoid('WGS84')

            area_m2 = d.measureArea(geom)
            area_ha = area_m2 / 10000.0
            area_km2 = area_m2 / 1e6
            perim_m = d.measurePerimeter(geom)
            perim_km = perim_m / 1000.0

            # Centroide en WGS84
            geom_ll = QgsGeometry(geom)
            crs_wgs84 = QgsCoordinateReferenceSystem('EPSG:4326')
            if crs != crs_wgs84:
                xf = QgsCoordinateTransform(crs, crs_wgs84, QgsProject.instance())
                geom_ll.transform(xf)
            centroide = geom_ll.centroid().asPoint()
            lat, lon = centroide.y(), centroide.x()

            # Zona UTM
            zona_num = int((lon + 180) / 6) + 1
            hemisferio = 'N' if lat >= 0 else 'S'
            zona_utm = f'{zona_num}{hemisferio}'
            epsg_utm = (32600 + zona_num) if lat >= 0 else (32700 + zona_num)

            # Coordenadas UTM del centroide
            crs_utm = QgsCoordinateReferenceSystem(f'EPSG:{epsg_utm}')
            geom_utm = QgsGeometry(geom_ll)
            xf_utm = QgsCoordinateTransform(crs_wgs84, crs_utm, QgsProject.instance())
            geom_utm.transform(xf_utm)
            cent_utm = geom_utm.centroid().asPoint()

            # Bounding box
            bb = geom_ll.boundingBox()
            n_verts = len(geom.asPolygon()[0]) if geom.asPolygon() else 0

            # Alerta de area
            if area_ha < 1:
                alerta = ('⚠ Area muy pequeña — resultados pueden no ser representativos '
                          '(minimo recomendado: 1 ha)')
                color_alerta = NARANJA
            elif area_ha > 50000:
                alerta = ('⛔ Area muy grande — descarga directa no recomendada '
                          '(maximo: ~50,000 ha). Considere usar Google Drive.')
                color_alerta = ROJO
            elif area_ha > 5000:
                alerta = ('🟡 Area grande — resolucion se reducira automaticamente a 90m')
                color_alerta = '#F57F17'
            else:
                alerta = '✅ Area dentro del rango optimo (1 – 5,000 ha)'
                color_alerta = VERDE_M

            self._datos_ficha = {
                'Area': f'{area_ha:.2f} ha  /  {area_km2:.4f} km2',
                'Perimetro': f'{perim_km:.3f} km  ({perim_m:.1f} m)',
                'Centroide Lat': f'{lat:.6f}°',
                'Centroide Lon': f'{lon:.6f}°',
                'Zona UTM': zona_utm,
                'Centroide UTM E': f'{cent_utm.x():.1f} m',
                'Centroide UTM N': f'{cent_utm.y():.1f} m',
                'Bbox Norte': f'{bb.yMaximum():.6f}°',
                'Bbox Sur': f'{bb.yMinimum():.6f}°',
                'Bbox Este': f'{bb.xMaximum():.6f}°',
                'Bbox Oeste': f'{bb.xMinimum():.6f}°',
                'Numero de vertices': str(n_verts),
            }
            self._alerta_area = alerta
            self._color_alerta = color_alerta
            self._actualizar_panel_ficha()

        except Exception as e:
            pass

    def _actualizar_panel_ficha(self):
        # Limpiar layout
        while self._ficha_layout.count():
            item = self._ficha_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        if not hasattr(self, '_datos_ficha'):
            self._ficha_layout.addWidget(self._lbl_sin_aoi)
            self._ficha_layout.addStretch()
            self._btn_exportar_ficha.setEnabled(False)
            return

        # Alerta
        lbl_alerta = QLabel(self._alerta_area)
        lbl_alerta.setWordWrap(True)
        lbl_alerta.setStyleSheet(
            f'background:{self._color_alerta};color:white;'
            f'padding:6px 8px;border-radius:4px;font-size:10px;font-weight:bold;')
        self._ficha_layout.addWidget(lbl_alerta)

        # Tabla de datos
        for k, v in self._datos_ficha.items():
            hl = QHBoxLayout()
            lbl_k = QLabel(k + ':')
            lbl_k.setStyleSheet(f'font-size:10px;color:{GRIS};font-weight:bold;min-width:120px;')
            lbl_v = QLabel(v)
            lbl_v.setStyleSheet(f'font-size:10px;color:{GRIS};')
            lbl_v.setTextInteractionFlags(Qt.TextSelectableByMouse)
            hl.addWidget(lbl_k)
            hl.addWidget(lbl_v)
            hl.addStretch()
            self._ficha_layout.addLayout(hl)

        # Nota: datos admin se completaran al ejecutar
        lbl_nota = QLabel('Departamento, provincia y altitud media se\ncompletan al ejecutar el diagnostico.')
        lbl_nota.setStyleSheet(f'font-size:9px;color:#9E9E9E;margin-top:4px;')
        self._ficha_layout.addWidget(lbl_nota)
        self._ficha_layout.addStretch()
        self._btn_exportar_ficha.setEnabled(True)

    def _limpiar_ficha(self):
        if hasattr(self, '_datos_ficha'):
            del self._datos_ficha
        self._actualizar_panel_ficha()

    # ══════════════════════════════════════════════════════════════════════════
    # EJECUTAR DIAGNOSTICO
    # ══════════════════════════════════════════════════════════════════════════
    def _ejecutar(self):
        if not EE_DISPONIBLE:
            QMessageBox.warning(self, 'Libreria no encontrada',
                'Instala earthengine-api siguiendo la Seccion 4 del manual.')
            return
        if not self._aoi_geom:
            QMessageBox.warning(self, 'Sin AOI',
                'Define un area de interes antes de ejecutar.')
            return
        project = self._settings.value('gee_project', '').strip()
        if not project:
            project = self._inp_project.text().strip()
        if not project:
            QMessageBox.warning(self, 'Sin Project ID',
                'Configura tu Google Cloud Project ID en la pestana Config GEE.')
            return
        carpeta = self._inp_carpeta.text().strip() or self._settings.value('carpeta_salida', '').strip()
        if not carpeta:
            carpeta = QFileDialog.getExistingDirectory(
                self, 'Selecciona la carpeta donde guardar los rasters', '')
            if not carpeta:
                return
            self._inp_carpeta.setText(carpeta)
        nombre_proy = self._inp_nombre_proy.text().strip() or \
                      self._settings.value('nombre_proyecto', '').strip()
        if not nombre_proy:
            nombre_proy = datetime.now().strftime('%Y%m%d_%H%M')

        # Sanitizar nombre
        nombre_proy = ''.join(c for c in nombre_proy
                              if c.isalnum() or c in '_- ')[:50].strip().replace(' ', '_')

        modulos = [k for k, chk in self._chk_modulos.items() if chk.isChecked()]
        if not modulos:
            QMessageBox.warning(self, 'Sin modulos',
                'Selecciona al menos un modulo de analisis.')
            return

        self._carpeta_salida_actual = carpeta
        self._nombre_proy_actual = nombre_proy
        self._btn_ejecutar.setEnabled(False)
        self._btn_cancelar.setEnabled(True)
        self._progreso_global.setValue(0)
        self._limpiar_tabla()

        from .gee_worker import GeeWorker, LIMITE_DIRECTO_HA
        area_ha = 0
        if hasattr(self, '_datos_ficha'):
            try:
                area_ha = float(str(self._datos_ficha.get('Area','')).split('ha')[0].replace(',','').strip())
            except Exception:
                area_ha = 0
        self._area_ha_actual = area_ha
        modo_drive = area_ha > LIMITE_DIRECTO_HA
        if modo_drive:
            resp = QMessageBox.question(self, 'Area grande — Modo Google Drive',
                f'El area ({area_ha:,.0f} ha) supera los {LIMITE_DIRECTO_HA:,} ha.\n\n'
                'Los rasters se exportaran a tu carpeta "GeoDiagnostic" en Google Drive.\n'
                'Podras descargarlos desde drive.google.com al terminar.\n\n'
                '¿Continuar con exportacion a Drive?',
                QMessageBox.Yes | QMessageBox.No)
            if resp != QMessageBox.Yes:
                self._btn_ejecutar.setEnabled(True)
                return
        self._worker = GeeWorker(
            geom_wkt=self._aoi_geom,
            crs_epsg=self._aoi_crs_epsg,
            modulos=modulos,
            project_id=project,
            fecha_ini=self._fecha_ini.date().toString('yyyy-MM-dd'),
            fecha_fin=self._fecha_fin.date().toString('yyyy-MM-dd'),
            carpeta_salida=carpeta,
            nombre_proyecto=nombre_proy,
            area_ha=area_ha,
        )
        self._worker.progreso.connect(self._on_progreso)
        self._worker.modulo_ok.connect(self._on_modulo_ok)
        self._worker.error_modulo.connect(self._on_error_modulo)
        self._worker.terminado.connect(self._on_terminado)
        self._worker.error_fatal.connect(self._on_error_fatal)
        self._worker.start()
        self._tabs.setCurrentIndex(1)

    def _cancelar_ejecucion(self):
        if self._worker:
            self._worker.cancelar()
        self._btn_ejecutar.setEnabled(True)
        self._btn_cancelar.setEnabled(False)
        self._lbl_progreso.setText('Cancelado.')

    def _on_progreso(self, msg, pct):
        self._progreso_global.setValue(pct)
        self._lbl_progreso.setText(msg)

    def _on_modulo_ok(self, modulo, datos, urls):
        self._resultados[modulo] = datos
        semaforo = self._evaluar_semaforo(modulo, datos)
        for indicador, valor in datos.items():
            row = self._tabla_resultados.rowCount()
            self._tabla_resultados.insertRow(row)
            item_mod = QTableWidgetItem(modulo.capitalize())
            item_mod.setBackground(QColor(VERDE_C))
            self._tabla_resultados.setItem(row, 0, item_mod)
            self._tabla_resultados.setItem(row, 1, QTableWidgetItem(str(indicador)))
            self._tabla_resultados.setItem(row, 2, QTableWidgetItem(str(valor)))
            item_sem = QTableWidgetItem(semaforo['texto'])
            item_sem.setBackground(QColor(semaforo['color']))
            self._tabla_resultados.setItem(row, 3, item_sem)

        # Descargar rasters
        QTimer.singleShot(100, lambda: self._descargar_rasters(modulo, urls))

    def _on_error_modulo(self, modulo, error):
        row = self._tabla_resultados.rowCount()
        self._tabla_resultados.insertRow(row)
        item = QTableWidgetItem(modulo.capitalize())
        item.setBackground(QColor(ROJO_C))
        self._tabla_resultados.setItem(row, 0, item)
        self._tabla_resultados.setItem(row, 1, QTableWidgetItem('ERROR'))
        self._tabla_resultados.setItem(row, 2, QTableWidgetItem(error[:80]))
        self._tabla_resultados.setItem(row, 3, QTableWidgetItem('⚠ Error'))

    def _on_terminado(self, resultados_globales):
        self._resultados = resultados_globales
        admin = resultados_globales.get('_admin', {})
        if admin and hasattr(self, '_datos_ficha'):
            for k, v in admin.items():
                self._datos_ficha[k] = str(v)
            self._actualizar_panel_ficha()
        self._btn_ejecutar.setEnabled(True)
        self._btn_cancelar.setEnabled(False)
        self._progreso_global.setValue(100)
        self._lbl_progreso.setText('Diagnostico completado.')
        self._lbl_estado_result.setText(
            f'Diagnostico completado. {self._tabla_resultados.rowCount()} indicadores calculados.')
        self._tabs.setCurrentIndex(2)

    def _on_error_fatal(self, error):
        self._btn_ejecutar.setEnabled(True)
        self._btn_cancelar.setEnabled(False)
        QMessageBox.critical(self, 'Error en el diagnostico',
            f'Ocurrio un error:\n\n{error[:500]}')

    def _evaluar_semaforo(self, modulo, datos):
        # Semaforo simplificado
        if modulo == 'topografia':
            pend = datos.get('Pendiente media (grados)', 0)
            if pend < 15:
                return {'texto': '🟢 Apto', 'color': '#C8E6C9'}
            elif pend < 30:
                return {'texto': '🟡 Condicionado', 'color': '#FFF9C4'}
            else:
                return {'texto': '🔴 No apto', 'color': '#FFCDD2'}
        if modulo == 'vegetacion':
            ndvi = datos.get('NDVI medio', 0)
            if ndvi > 0.4:
                return {'texto': '🟢 Buena cobertura', 'color': '#C8E6C9'}
            elif ndvi > 0.2:
                return {'texto': '🟡 Cobertura moderada', 'color': '#FFF9C4'}
            else:
                return {'texto': '🔴 Cobertura baja', 'color': '#FFCDD2'}
        if modulo == 'erosion':
            riesgo = datos.get('Riesgo erosivo', 'Bajo')
            colores = {'Bajo': ('#C8E6C9', '🟢'), 'Medio': ('#FFF9C4', '🟡'), 'Alto': ('#FFCDD2', '🔴')}
            bg, emoji = colores.get(riesgo, ('#C8E6C9', '🟢'))
            return {'texto': f'{emoji} {riesgo}', 'color': bg}
        return {'texto': '✅ Calculado', 'color': '#C8E6C9'}

    # ══════════════════════════════════════════════════════════════════════════
    # DESCARGA Y CARGA DE RASTERS
    # ══════════════════════════════════════════════════════════════════════════
    def _descargar_rasters(self, modulo, urls_str):
        try:
            import os
            carpeta_proy = os.path.join(
                self._carpeta_salida_actual, self._nombre_proy_actual)
            os.makedirs(carpeta_proy, exist_ok=True)

            nombres = {
                'topografia':  [f'{self._nombre_proy_actual}_DEM.tif',
                                f'{self._nombre_proy_actual}_Pendiente.tif'],
                'vegetacion':  [f'{self._nombre_proy_actual}_NDVI.tif'],
                'cobertura':   [f'{self._nombre_proy_actual}_Cobertura.tif'],
                'clima':       [f'{self._nombre_proy_actual}_Precipitacion.tif'],
                'temperatura': [f'{self._nombre_proy_actual}_Temperatura.tif'],
                'suelos':      [f'{self._nombre_proy_actual}_SuelosPH.tif',
                                f'{self._nombre_proy_actual}_Carbono.tif'],
                'erosion':     [f'{self._nombre_proy_actual}_Erosion_RUSLE.tif'],
            }
            paletas = {
                '_DEM': 'RdYlGn',
                '_Pendiente': 'YlOrRd',
                '_NDVI': 'RdYlGn',
                '_Cobertura': 'Paired',
                '_Precipitacion': 'Blues',
                '_Temperatura': 'RdYlBu',
                '_SuelosPH': 'BrBG',
                '_Carbono': 'YlOrBr',
                '_Erosion_RUSLE': 'RdYlGn_r',
            }

            urls = urls_str.split('|||')
            noms = nombres.get(modulo, [f'{self._nombre_proy_actual}_{modulo}.tif'])

            # Obtener o crear grupo en QGIS
            root = QgsProject.instance().layerTreeRoot()
            grupo_nombre = f'GeoDiagnostic — {self._nombre_proy_actual}'
            grupo = root.findGroup(grupo_nombre)
            if not grupo:
                grupo = root.insertGroup(0, grupo_nombre)

            for i, (url, nom) in enumerate(zip(urls, noms)):
                ruta = os.path.join(carpeta_proy, nom)
                try:
                    urllib.request.urlretrieve(url, ruta)
                    capa = QgsRasterLayer(ruta, nom.replace('.tif', ''))
                    if capa.isValid():
                        QgsProject.instance().addMapLayer(capa, False)
                        grupo.addLayer(capa)
                except Exception as e_dl:
                    pass
        except Exception:
            pass

    # ══════════════════════════════════════════════════════════════════════════
    # EXPORTAR
    # ══════════════════════════════════════════════════════════════════════════
    def _exportar_ficha_txt(self):
        if not hasattr(self, '_datos_ficha'):
            return
        ruta, _ = QFileDialog.getSaveFileName(
            self, 'Guardar ficha AOI', 'FichaAOI.txt', 'Texto (*.txt)')
        if not ruta:
            return
        nombre_proy = self._inp_nombre_proy.text().strip() or 'Sin nombre'
        lineas = [
            '=' * 55,
            f'  FICHA TECNICA DEL AREA DE INTERES',
            f'  GeoDiagnostic v1.0.3',
            f'  Proyecto: {nombre_proy}',
            f'  Fecha: {datetime.now().strftime("%d/%m/%Y %H:%M")}',
            '=' * 55, '',
        ]
        for k, v in self._datos_ficha.items():
            lineas.append(f'  {k:<30} {v}')
        lineas += ['', '=' * 55,
                   '  Generado con GeoDiagnostic para QGIS',
                   '  https://github.com/geodiagnostic/geodiagnostic',
                   '=' * 55]
        with open(ruta, 'w', encoding='utf-8') as f:
            f.write('\n'.join(lineas))
        QMessageBox.information(self, 'Exportado', f'Ficha guardada en:\n{ruta}')

    def _exportar_csv(self):
        if self._tabla_resultados.rowCount() == 0:
            QMessageBox.warning(self, 'Sin datos', 'No hay resultados para exportar.')
            return
        ruta, _ = QFileDialog.getSaveFileName(
            self, 'Exportar resultados', 'resultados_geodiagnostic.csv', 'CSV (*.csv)')
        if not ruta:
            return
        with open(ruta, 'w', encoding='utf-8') as f:
            f.write('Modulo,Indicador,Valor,Aptitud\n')
            for r in range(self._tabla_resultados.rowCount()):
                fila = [self._tabla_resultados.item(r, c).text()
                        if self._tabla_resultados.item(r, c) else ''
                        for c in range(4)]
                f.write(','.join(fila) + '\n')
        QMessageBox.information(self, 'Exportado', f'CSV guardado en:\n{ruta}')

    def _exportar_json(self):
        if not self._resultados:
            QMessageBox.warning(self, 'Sin datos', 'No hay resultados para exportar.')
            return
        ruta, _ = QFileDialog.getSaveFileName(
            self, 'Exportar JSON', 'resultados_geodiagnostic.json', 'JSON (*.json)')
        if not ruta:
            return
        salida = {
            'plugin': 'GeoDiagnostic v1.0.3',
            'fecha': datetime.now().isoformat(),
            'proyecto': self._inp_nombre_proy.text().strip(),
            'resultados': {k: v for k, v in self._resultados.items()
                           if not k.startswith('_')},
        }
        if hasattr(self, '_datos_ficha'):
            salida['ficha_aoi'] = self._datos_ficha
        with open(ruta, 'w', encoding='utf-8') as f:
            json.dump(salida, f, ensure_ascii=False, indent=2)
        QMessageBox.information(self, 'Exportado', f'JSON guardado en:\n{ruta}')

    def _generar_pdf(self):
        if not self._resultados:
            QMessageBox.warning(self, 'Sin datos',
                'Ejecuta el diagnostico primero para poder generar el reporte PDF.')
            return
        nombre_proy = self._inp_nombre_proy.text().strip() or \
                      self._settings.value('nombre_proyecto','').strip() or \
                      datetime.now().strftime('%Y%m%d')
        carpeta = self._inp_carpeta.text().strip() or \
                  self._settings.value('carpeta_salida','').strip()
        if carpeta:
            import os
            carpeta_proy = os.path.join(carpeta, nombre_proy)
            os.makedirs(carpeta_proy, exist_ok=True)
            ruta_default = os.path.join(carpeta_proy, f'{nombre_proy}_Reporte.pdf')
        else:
            ruta_default = f'{nombre_proy}_Reporte.pdf'
        ruta, _ = QFileDialog.getSaveFileName(
            self, 'Guardar reporte PDF', ruta_default, 'PDF (*.pdf)')
        if not ruta:
            return
        try:
            from .pdf_reporte import generar_reporte
            area_ha = getattr(self, '_area_ha_actual', 0)
            modo_drive = area_ha > 8000
            ficha = getattr(self, '_datos_ficha', {})
            generar_reporte(ruta, nombre_proy, self._resultados,
                            ficha, area_ha, modo_drive)
            QMessageBox.information(self, 'Reporte generado',
                f'El reporte PDF fue guardado en:\n{ruta}')
            QDesktopServices.openUrl(QUrl.fromLocalFile(ruta))
        except Exception as e:
            QMessageBox.critical(self, 'Error al generar PDF',
                f'No se pudo generar el reporte:\n\n{str(e)}\n\n'
                'Asegurate de que reportlab este instalado:\n'
                'pip install reportlab --break-system-packages')

    def _limpiar_tabla(self):
        self._tabla_resultados.setRowCount(0)
        self._lbl_estado_result.setText('')

    def _abrir_manual(self):
        manual = os.path.join(os.path.dirname(__file__), 'manual.pdf')
        if os.path.exists(manual):
            QDesktopServices.openUrl(QUrl.fromLocalFile(manual))
        else:
            QMessageBox.information(self, 'Manual no encontrado',
                'El manual PDF no esta incluido en esta instalacion.\n'
                'Puedes descargarlo desde:\n'
                'https://github.com/geodiagnostic/geodiagnostic')

    def closeEvent(self, event):
        if self._rubber:
            self._rubber.reset()
        if self._worker and self._worker.isRunning():
            self._worker.cancelar()
        event.accept()

%PDF-1.4
%���� ReportLab Generated PDF document (opensource)
1 0 obj
<<
/F1 2 0 R /F2 3 0 R /F3 7 0 R /F4 10 0 R /F5 18 0 R /F6 19 0 R
>>
endobj
2 0 obj
<<
/BaseFont /Helvetica /Encoding /WinAnsiEncoding /Name /F1 /Subtype /Type1 /Type /Font
>>
endobj
3 0 obj
<<
/BaseFont /Helvetica-Bold /Encoding /WinAnsiEncoding /Name /F2 /Subtype /Type1 /Type /Font
>>
endobj
4 0 obj
<<
/Contents 25 0 R /MediaBox [ 0 0 595.2756 841.8898 ] /Parent 24 0 R /Resources <<
/Font 1 0 R /ProcSet [ /PDF /Text /ImageB /ImageC /ImageI ]
>> /Rotate 0 /Trans <<

>> 
  /Type /Page
>>
endobj
5 0 obj
<<
/Contents 26 0 R /MediaBox [ 0 0 595.2756 841.8898 ] /Parent 24 0 R /Resources <<
/Font 1 0 R /ProcSet [ /PDF /Text /ImageB /ImageC /ImageI ]
>> /Rotate 0 /Trans <<

>> 
  /Type /Page
>>
endobj
6 0 obj
<<
/Contents 27 0 R /MediaBox [ 0 0 595.2756 841.8898 ] /Parent 24 0 R /Resources <<
/Font 1 0 R /ProcSet [ /PDF /Text /ImageB /ImageC /ImageI ]
>> /Rotate 0 /Trans <<

>> 
  /Type /Page
>>
endobj
7 0 obj
<<
/BaseFont /Symbol /Name /F3 /Subtype /Type1 /Type /Font
>>
endobj
8 0 obj
<<
/Contents 28 0 R /MediaBox [ 0 0 595.2756 841.8898 ] /Parent 24 0 R /Resources <<
/Font 1 0 R /ProcSet [ /PDF /Text /ImageB /ImageC /ImageI ]
>> /Rotate 0 /Trans <<

>> 
  /Type /Page
>>
endobj
9 0 obj
<<
/Contents 29 0 R /MediaBox [ 0 0 595.2756 841.8898 ] /Parent 24 0 R /Resources <<
/Font 1 0 R /ProcSet [ /PDF /Text /ImageB /ImageC /ImageI ]
>> /Rotate 0 /Trans <<

>> 
  /Type /Page
>>
endobj
10 0 obj
<<
/BaseFont /Courier /Encoding /WinAnsiEncoding /Name /F4 /Subtype /Type1 /Type /Font
>>
endobj
11 0 obj
<<
/Contents 30 0 R /MediaBox [ 0 0 595.2756 841.8898 ] /Parent 24 0 R /Resources <<
/Font 1 0 R /ProcSet [ /PDF /Text /ImageB /ImageC /ImageI ]
>> /Rotate 0 /Trans <<

>> 
  /Type /Page
>>
endobj
12 0 obj
<<
/Contents 31 0 R /MediaBox [ 0 0 595.2756 841.8898 ] /Parent 24 0 R /Resources <<
/Font 1 0 R /ProcSet [ /PDF /Text /ImageB /ImageC /ImageI ]
>> /Rotate 0 /Trans <<

>> 
  /Type /Page
>>
endobj
13 0 obj
<<
/Contents 32 0 R /MediaBox [ 0 0 595.2756 841.8898 ] /Parent 24 0 R /Resources <<
/Font 1 0 R /ProcSet [ /PDF /Text /ImageB /ImageC /ImageI ]
>> /Rotate 0 /Trans <<

>> 
  /Type /Page
>>
endobj
14 0 obj
<<
/Contents 33 0 R /MediaBox [ 0 0 595.2756 841.8898 ] /Parent 24 0 R /Resources <<
/Font 1 0 R /ProcSet [ /PDF /Text /ImageB /ImageC /ImageI ]
>> /Rotate 0 /Trans <<

>> 
  /Type /Page
>>
endobj
15 0 obj
<<
/Contents 34 0 R /MediaBox [ 0 0 595.2756 841.8898 ] /Parent 24 0 R /Resources <<
/Font 1 0 R /ProcSet [ /PDF /Text /ImageB /ImageC /ImageI ]
>> /Rotate 0 /Trans <<

>> 
  /Type /Page
>>
endobj
16 0 obj
<<
/Contents 35 0 R /MediaBox [ 0 0 595.2756 841.8898 ] /Parent 24 0 R /Resources <<
/Font 1 0 R /ProcSet [ /PDF /Text /ImageB /ImageC /ImageI ]
>> /Rotate 0 /Trans <<

>> 
  /Type /Page
>>
endobj
17 0 obj
<<
/Contents 36 0 R /MediaBox [ 0 0 595.2756 841.8898 ] /Parent 24 0 R /Resources <<
/Font 1 0 R /ProcSet [ /PDF /Text /ImageB /ImageC /ImageI ]
>> /Rotate 0 /Trans <<

>> 
  /Type /Page
>>
endobj
18 0 obj
<<
/BaseFont /ZapfDingbats /Name /F5 /Subtype /Type1 /Type /Font
>>
endobj
19 0 obj
<<
/BaseFont /Helvetica-Oblique /Encoding /WinAnsiEncoding /Name /F6 /Subtype /Type1 /Type /Font
>>
endobj
20 0 obj
<<
/Contents 37 0 R /MediaBox [ 0 0 595.2756 841.8898 ] /Parent 24 0 R /Resources <<
/Font 1 0 R /ProcSet [ /PDF /Text /ImageB /ImageC /ImageI ]
>> /Rotate 0 /Trans <<

>> 
  /Type /Page
>>
endobj
21 0 obj
<<
/Contents 38 0 R /MediaBox [ 0 0 595.2756 841.8898 ] /Parent 24 0 R /Resources <<
/Font 1 0 R /ProcSet [ /PDF /Text /ImageB /ImageC /ImageI ]
>> /Rotate 0 /Trans <<

>> 
  /Type /Page
>>
endobj
22 0 obj
<<
/PageMode /UseNone /Pages 24 0 R /Type /Catalog
>>
endobj
23 0 obj
<<
/Author (\(anonymous\)) /CreationDate (D:20260321024044+00'00') /Creator (\(unspecified\)) /Keywords () /ModDate (D:20260321024044+00'00') /Producer (ReportLab PDF Library - \(opensource\)) 
  /Subject (\(unspecified\)) /Title (\(anonymous\)) /Trapped /False
>>
endobj
24 0 obj
<<
/Count 14 /Kids [ 4 0 R 5 0 R 6 0 R 8 0 R 9 0 R 11 0 R 12 0 R 13 0 R 14 0 R 15 0 R 
  16 0 R 17 0 R 20 0 R 21 0 R ] /Type /Pages
>>
endobj
25 0 obj
<<
/Filter [ /ASCII85Decode /FlateDecode ] /Length 935
>>
stream
Gb"/$9lJKG&A@sBbRo/'G4s+ka.S0c;Y__\\JsS+5u(\5<$9,?kO&+%D36es7$6isfl-#tm(<Xg`.ugLg(D"Nkg^V!<`Iic)e#\TUh,[:b61K(]cs/@G:FuVb*kSN9t!i6)lulHFlWu>mt7N*9fH\u:P!(.GeqMW%n,HbO?/bcYB)A0Q"JrIbrXJ7al%^WM6p/DPF*p0CZ;+LW:7M2,a)IZNcC;[O/kt%GEAp?/uZQ!ECX&V@6MaPZ%ggIC,WVEW51e'DJTolPG!:7!Lh+[(*Vj37GF%=UC`GHciN?"nY[C(7L>FFBNlPB44<gWerU5aO6&ZHLYZS6r]YBUb$*a;ak9E.K'OQ'#rW1Z,bG:%WgRoEcODgspORB$.L#?c</m(&#rW<q_LSJuBKA>5Pm1!7*!Ztu*sN37pTquu#TT?^a;0%`S74uA<crc'/N<S#rj](:;Xp$0Z_!O2=JlJ6_Y!rG1n$-`kn'6OgFI,f%:_#6+p=f8A#`f#CWnX^C'f1Oqn'/fQ45DeNpWuCE7OAje[CsEVIb$4hU6GZg$\1H_A'7K_UK\Y:6rk`HAi,>38?LM1KfS]c<#;.77^H3anesYm^L9\!`+Z%&Ue=6OHo7V6V1@[M`#5=@jW?[/L;8];Pp=e1X-KAZ\-7XZ@ue3RFS=D_h^1c0N94J#ocU6USE4(+\)1o<8!,9F<8"q,A'20hoFqgF`36X7\lK[NYl4/HuhEfAd0?OcRn%p)R3.T1LX3N6hIYKVu<X$hDB^e4Mo.`o=riUUt+cY>9kJ08TadM&lHZdC@'nu%?FXe%XPa3GJ1M^o-I\GY8896hEP9k5/n#[)YknuEko8EHOn:\TQZm3p$PMnN,C64VZ'I8l`,gpNlZUq/9[Ypp&8&OVjbVWE[NEYFXqIP<ppAF%mO8r;Rm\2$@gr\nja4HZJXlQ[V,~>endstream
endobj
26 0 obj
<<
/Filter [ /ASCII85Decode /FlateDecode ] /Length 796
>>
stream
Gaua>9lHOU&;KZOME*#Ki\JM3k*S']<MEMo&rsL^i8$@:Ql'M+J)=Be]@jRUTnaI.cn:^]GSn[e7S)dZkup4MHn++8(BieqXoJV=:k"*eR62hk]M`aH$=4k9$CTtcUA*k+_c1BqJRqG(Sc_>470-hfO@e5S3DiU:O:)Ps-Pq0j!/4m6(BlB=CH*fgD.B6InCb:'D-cQ+@jpf>quA+JQVq@\FM&?Z&-pT+r1rp.@D's$<WJV@PS>]]3L=]m9\RV*!shm\XU@jQ)S#da]U"L_cZ7**I:,70*cH+jn>.eK]nQd_^Mo#mXf]S,EuZ@XiV4pQOg5ZIA[_3J;3D/l4P(cEns9sinLmE-g<k1-"CI3ija7FpSDno9/_D,1et4t/DLFaZlA]1(ke']Y7a)TEefmm9;;\0!-JC#G0="*n-,W%a#KYeUY-aQ,3faICb!(igGD#@X$hf@&.K9&HXO?nEBCW"5+&$1AU98>8>r/Wh$atc4jnX$]fU80=[[7:X:g\.rD6UhoYU0d&[O(Y@`,mUQGi\IIQa+>iG-9VH$sWA,Fd4`l4FnAA;Q4GMmk5K8B\WpJI,%^QmUp]3YQI^30u6UpN2%gKOD<VlSUNf<3K=>Lc)?tS/E#E!6>8tA$++D@6deQ@?/PJ/h)70_GY0]cGj:)0Ta`iF%/Z>cPs%$XW?]\;&ndHS+r9I_YKhn*cDDu]4gjdEX6pBm08Tm<'Ji?.VQkqaqe"XB[NYE?dp<2^NMMpR4,HdTDD%^O/l+S/jFN&K0)-eu%A$2($F\f-IGT`:,ej@@jf!A~>endstream
endobj
27 0 obj
<<
/Filter [ /ASCII85Decode /FlateDecode ] /Length 1705
>>
stream
Gatm;968iI%)2U?i0\UkQ;<>uFqZg(ST^HWGC.GcOVpY08TaSqg\pdQ;R.mb<n$GX1)$&W#^jDm!Yb`oIk:Ln$\1I-nE(_n`aSZC9G.ZTpTRcFSn>Z(HU0umr]LiUOf2!M?m6B]N&CTfC@*sahR]F9TeqWm84&`%'eB_P\MEKP1r)jpq&,L%]Xd!mLdVPFfQb_rFm#/qQ`b53'V6297)0i+0mkZdCN<N[pq(E<Q+;HKU)Ak6"[pP$WW\q+O/7GtM]#C]AQJ648PPT'M1u(rcpVS)]mH*`m>Na![)RnjjK/Dj>fjnh>U&Sq8Vi0O_G:m)Z&1eeU0&&%L4tCa1X%Fee+;]BLEn.6'&=r-=9^Sq6qJQ9cbMM_a7os_80A4-&.EN[\PNP/#Y@V3F?K8=Q+'9qCeSEuqVq(SbOaT$"2n[7NCbp"I-O>6==aZ4Y-D`M*[9I]Ji"%]7>02LV19,'Kr9qP#(Ol':G`eW?-#')l0F<6$HlhO!#[(.cpRt5f+[kg)VUfoF-%FMdO2u^`?Lp]:47Fa(kKl9WSFLJdgX,)q0?^,fG^W#RQqV,I#*Y9Km3SJ.%DV.-q5l)K-`49%N.XZ<@B0TTtR=VC)SD.pi:Um&6t-pG3#eVe$N9<"t]WO9\[(o1tfVJEW^)]g<,'[nT_20"]1t-<rluYA[de"mhenU:47@.7@odq^qH^ak:FU4qUB,c!`Pcm/SAX).pEZHF/;SMe('\(leK@o<6ZX=8d'"imK>'-mM+c:K>KLKo%R*,Vetk;Q3_d>jJ6V\m2Tr6("dNKQ1IkH$X76oZO0"O3]5IA<'DNQY2J!pD1R8i6#7GJ[PeS`BRHc>-R_t$2Qe<sXRq=RS\f='S8aa$#PR,Jq7M\XhmCr>jmF)6V,%\8U@gf`jb'Uk*P7<c3)%.UB'/T!f<u!K3M`$(Hr[X6G;V#/]rda3)WquJO>N7(_`+ML>HaSVC+EA4qZjcP>b8''ksELoliV9,HY><m_JBX3pP9=fU<OX`o(bdK?T5-&9\E9]Wq8#mG4h5=dUWm)AF4.68M,/ZS/S31Z//'NF^JO!>9g?l,7RVM0#r"d<&O`nqY1r2<?e\&0m:XG`b$S2JKoh:4,"c!*T,%BXDqu'&uNZa/e9="cr"h^_g<D?o:]hg&lC2)I!/e9]1_X']>g-Sr<:AJ^M#TaI_i0L)Wo*ns)C`-3QlWuR2nY^b2iSn_#5s[h(:&aK/9Ur'`1toc^U=R)($"0$SHmpgN0IN4LYRpB\9_PSfL3`0T4m_)Q*Ht[dn)'pgn9&]%7E.YN*3-P3JW]k)'Th])19TWY[8]S&2]M":)'HUUe3oic2Umq35=Br_gWQG`RjM.mC4NID!6TSH=pA_;'ful0nb3Ib4+`PIB++b][TeC#<pglK"Mf*t45II.t6jDjDL-E/RrJC]9dKiU"n6S#b:(/8j;oPdi9ZW3R.]iU^ua.BpF6E`KiB!i'uoHXgi]BVE[0fk+K`a3aJ5(bIH4r?Sm7SV%4:p63A.j!q_.k/2:Q6ruQjrPWoL#%u'd0_u4e*Xrr_F%Rn\S2/ued,c`u0,j7X(O13S>s?V`$J.uVT7?Xd+Mq2If;jgXs7&a3pY9%G[fSU:9a?OXPmKglf+1<[gki8/%n4"`M:gH'gI'=4b^/^a>P(12X0"XI&BI!754[%/m[7TkQ9BuY@N3hie/4Gb^U3!fG@M>!rrEDKT7H~>endstream
endobj
28 0 obj
<<
/Filter [ /ASCII85Decode /FlateDecode ] /Length 2171
>>
stream
GauHL>BA7a(4Q"]35q)L)LD7[$Z?SM-<i#7Lj,Hgdb'Q,PUni+GSYc,Ibg/ufnglO+^:qu<i^B>gqW;K&BCCKT?@\klT+q;<fiD"s%Ga8:%NQcRnmoLrLLma86OHG1F5tZh+T>m@YO81_,%)^rW1D>2`t]B7klI;\1k1]q1bcuG+BA6jE$di7Ism!\FD?eMc,t#j(BuMq'NH6U9'i#8NXaJ;m_WAVLR?p[5k?/rMOOMQ'ET!/.j(d%'`4@gna_*A?65g]UUZCInts>Bf]ZH8^`8MA5pE>!n"nh:,`h5\4I<8X<K<OR#je8hV\H]a(`[qbb9K#R#Fa-=u%>N#Wj#Srac/gdb[.%]p4fd7rt!g%_^0jM,;E0V=&ZffQHr--\Oi#90&4JK^2#UEtTRk3K$<=+.mYG[g3O^D.VtLjjd)gkJQ7)5o3U@m4s=SQXrILZe7mE&'14<$'FRk5o:H*.RLS7gAhub%C]Vf"T<,QA=@IkcipTtPWmu8#[n<5Ce.&F$Xr$<:`n!(QY%fKCc"ZMiM=.SI(2T*r@>F&mo2(=k\f.VcC2&9D<5qD=W]Z^?4EVS*bumP_:aKX$'iCBLSaj-$Bd3oBd"$p'@OmF2-;EiPiLra1jr@\Y4a`7'm4#->L@H,'Q30.Xf\RBKrZWJC4DB+^WtDIk/-`5(>i6jl@\pNlP2`k(9V7+WuD::98FGmN/+1o1,#VM89:85h^l/`m@F-o*oIQmNr?d'*,ojee2<Q`&a<J!e42pR7F9mQiNb#d\YGRpRP-KJONd+ng.;0@UEd:3M%2.)GnAcCY&)Q2A\-$!l]R,<T&-t,'[gHZ'g%1iXb55T-+gN7\&n!?oZ-jP`H+Le>Rg!EQP$lir,ZO'D6Z%o+tq^$EGVeYnh7Ig+K<J+j[2AOa$hbh'WjcIQG*oZA\R_.Y]F@MH(WK++l\mgFCZgK&NX=oeC=:J\I^'q%]1p>V;F0:T->f#fPe.@Oj:,&B:#cpRg.3Me[)qtHe$C\BThuo%D4/GKG)g3,ClID2Jlf$FLeYZrWkr&on83/PacOXTU!^bF'3A6g`r`#S]\(^)lbZh,Ef<G]4CQu)EM0[P`+^cYf"CTBZE2-(1$0'W#46s%Mg07<bR#&H70;GkY5*b^/KM-WTd&Yg%l<WCOcecnLSSB7'K)%`,C0\WU[n49Om!J`C,'?RV4-P+9[3D>UZIp&ipq].BEmfd`LHOdrI3K6sr@hXX,&@78.Gl;tdMkUt[\qZsS?RiHIKMce0u@5nG,5=\a@Bc10J*m_AZL#ik!h"I*NV(()<[qo=%=jEL!fGO24T4g>N416B\+"cQB5HS-#NG[Bt+c(D>'o@a#!X&o&bT>(,A-MPq1eA?3[*h@;7NCrmplJoW^5X's\5RY%)g2i14gni_Alh8]jI%$bH=1Q#:fA[pL%L8]d(TlGWZmf'/01W5]qKV5pJDHa(*?0VD(<,I!UX#N)j3A\J9H&qB=t&p;X\ZP.I>Jq69Gh`eZ^L7WE51?Rj0_!-GE5_;B9$u$?<pp3msiK#Ya:XR0nO,-Ng0JA+;g=I$Nb-i;bf(66!Zs4Im9LT(Z8ns.!,cNIea_]0$2SNgb!s?oXE"-fo&44rE+')`_WQ.XROoTECK3ZUTci3EMJja/UTdtERbP\Mr*:q71Ce!*&_(n':i$XrYE2m535r#\>=V,^$,/cBCG/p?<VYu=oclD\BjVl4]IKh)roN`-<Rh'!ggECK0\OR'O+6o]<G$*&mTYPWH'Zc[pB?>[##hk,o!;2:;-hLMPI@oN3h0POoR*7A=[bbH"dU1ih)"H7ee^qUglYJOHDqNH9c"NqH_!I_huLqiF2fK@>,f!n\\cG_e&7+I>'AO&Wb>6j,T=^d!7V5]C:2Sc3]$$?CFBSX7pQ4po3ba`mSLDEt%!;+)f!^W-]i<9s:I)n@#F4LRO!.[T/'eX;b\aNq(b1<XqgV^')_'Z5EBCUjfS-IY=jZNL3SB5+B1tN+p&c+/>n%?JGN[,2_Nen<`L_p+n!AiTu10pJ/;mMV<m)c^3I`qnP[@*!uYR!AfOKd">UhrI_tFl0l&/b+5RKc[EFC'V'f#3JM^<KZ/!<aN@<*#]T3a</#V`h>AL7%c"c;J[%GPh-b?l.@YfYJf\-unRsne+3NujDt5gf1j8s!(,HOQX7`$WoQ6n+ao;?),:.O~>endstream
endobj
29 0 obj
<<
/Filter [ /ASCII85Decode /FlateDecode ] /Length 1729
>>
stream
Gatm<>>O<<'RnB339#dt>2sDXoSn$F;Jdj6doNJL67-3pTUB=]-EMB?I?,BrP705u6kp=j[a4(,3Bjo\5k0p2s4J%CQPgd6112)6GJGJd0`(htZfj+N-e]T:,S']>n5LShOb/EXi+JeS.oc8'JHb:q-A9f,!?hb\.T%m(_Vq?%cO0j7#FIZim%"eKjG?Huns#,Zc><;?2toaDYO`0o(nj@5-dED#_\A)5^tce6F^qGa*/Go0Yp<@8ZqRDjnMB<a<:KE/+pu%P`C??HKP?ul=Fq0S.#jtu]`hY2KMeR'hH7]k$4t4B9\kC1`1<\Q&ICo$W?OH%0h>%R94Od%E;(tOgHoPEUJhZ%2`)gA(j))J1_W8K+eDnGCq<pOna;K(;MlS6i*(2q[eq?q,mi&B=OZB+5mP6K<!KMNcECG6Dj6T==DYZ+=cS6_ao]j`:'QNWnC;V!@NOrhDBP1%(gl#]!e_*j*aA@mpcTf`ePr4-][bDpm_*W/_SV45JrEXfh*erOY4fs"C++S82[AK=+Itfg]3+FdbGd;dTce;\e8)BU$fLF8FoeYpB"%1E)]<-5RQ+#rBW.Y]+!6LR+qh@N[3&*^VK"l=[c#XP%&V02k>*E%H[bbt2#(p<L,4Naft\1*Nll!R3$kRn`:2k;%nScPS8^*Z_XCj?,Ib*8cg,_=h_ngn^7AgA9ecbYO,\9]H$^d3Y&(O)93\K7\/Lgjba3V6jHt3qiHBE6l;aS2e\XA5Z?D)@\V.W4$AoFT;6^!e283=X$Hr_WJsW!.GiPI3nB(J?n.V/CBu&,(DApsm5XVmh>)ZaT;LG3QM@N4(-7*jjN<K\R5qo(k's.)_ji0A83>*id?Kl%+I-25gVchkXZehUq1jdtuhaAQ'MklEJ92h1(T9c4F#5h9>N\_L1>O&/")@Kq%8JGpT*5R%uB?r*JfJKA'h4Y>&mqnV`lJD<W$_]Tgl^P=*hje%Yc]140J%ReP\FDlZ/RN?FhY,&de<5-sHkP_[I!f/Om;2]H"AF.c@M4:.r&:M3"^iBdIYM3b3QVXl3Yb"bLS))6_nemc+WU70XodA>qJ%9rarN4D*(i6QMLkL\o*qu/k&i5&R&j@)Tj__\csplJ2Wj[b.0pS/#)?q#_SA6$GX)NpJ?N'](=l"(kXE,C1Cl-e?;?'Pg2MnH^^[q$\@Xjdac<*TLh$js^jDU)e_8ac@FXGU'k8f4:UXH]!ZOG7XR1F7j`<5MK!>b&4U#<<HI@"G#$Y/u=_GVfDZg$lgUBZ.^4uO4pSA9>?5tVO+"u>3@(E79DX!V>^3ArS`nPT#3$?m!aRp-t,Id$#YZhqciNb\b-=M.PbPm<WFLbt,V"O4Fli&"J@>HiRj9U=l!8o+#SG2aeDJ_+]7<dXiIGLBWJd@(,FPhTl&r"5U:*%.YX[OM+i^e+@3sHLQ8?.)HmZ$3qW^/_"MPJGhEHW)L$nhfh1#^OiQ(>!Y[ktdqD?K"mh\T/:dr!H<&FHl9O_YdLpcf=F&%@JWIIoO?h%Xu6+AV2GNG3umCSKSihmHCC[aWX4;B^&o(DFC[6/Vo$_l0GMMY4hkBV&S$rjcNL%5S)4?#[Q]4*#c75ksr\^GQP`..UGN'ugTN<o#_9"rGfgN^]V\1pQqE#h1*;7M"(ZU:IZ7Y&d]Fp+Eh>XeB!$V-!:6@.>aUeQC%KR9AD/VQ,%S\nfkkAa6s$E/s4K?p:]t0\MnBDkIk*ou8`r"#WLH!R9ODI/~>endstream
endobj
30 0 obj
<<
/Filter [ /ASCII85Decode /FlateDecode ] /Length 1814
>>
stream
Gau0C>Ar7S'RnZ;3:N-dV(='X\n#K*Zuq!2CR6qcq_/N],;Y07=`SUUQi6c/Ub6gg]5&I>!0K^4kBuIl;%Ud?E<"B%dAo8jIk+(b1qt.VRABY^1n/jD?N2=[*tf@_lR_N=M;:i0,)?:_UDQ4p]!M]104"+(E?7R`8B-@@'[9]94jfU!Th.GAq-Pt.C;k%^$!EYjM7@opfT^;0I9DeWPGN@G(hWk$Hp=A"\nH4]91-JGXfesM9.Z!TLdFN]Q4[1)StR5t7A#T'VWb'^Cp_<OM)\7>>*0/$VIG?&f5`qFR,BHS@;ui^.E$nCA7?!#J3-@9(.9/3'?0l?Kd;)D6kWsaTo5fiHqT*=T"jqIEK904mN&m^"0i-!P!ST>#O]0@=+"74,dE")KHRqJI\?,J-]jie,*))+3ltS/Lt9/co^V_4C$4Z=nreOBe8(UeE-th)F?H%0+o7"r))R"qD[XFt\0$CF[XB(pU#0hFKh'KC*qPS_#7-ml3^RQPc$(<^S;7p%0OZS-g]d!'*r3P(QG5AI>OLGqX[?p76tlPbF6h\^AG!%')kFkKYTBd1CWa!Tb#FcUUT<P"'QBakVUsKAa6Z20`mH\"?RT;+A<Eo@(3"L`IKRjX9QfP%iiZNI.18p*5DCm`Lp&XXnS;o7F\D&#>\>@NU+*.;Um'Qq$L"g*C"B.`Alq!r-)Wf))mdtO:<JGf>oqcU&(Vegj^i=CAdtT)ZZNF740;.sDBRTBW2^;[XA,-hA>rlq/Z'ZS)$)S6idkKqQMl?O<3kmFY2H"5^V[,um13d[j'8EShj^KJQDi3<"LP"3QA>+D/F#!7QM(l:BKq"U"gpY)V&uN^]6HIPG%JCp90f]r^AX1lks@cM*?bQ0J./0d"3?gi#jAT<D>gkGkJg!"XN<bTr\bU7dKuHsHkl@I`4\r.r4SJ`aAu67\hq*<Wr/ci]_Uf&n`0_*oCrn,T=G(o6*8]I]mTX=f&fkoX.@GBX!AsT/s'8G)bXd$dgmO0"6K^>o%ot;<&AL&rnhG1P*!R&])T,^bS,QpV4PWp)1!`<i'W>RM<[rdNtj4-W1EH!]"Q?]kY;S*&IT?7O(-JU8,;qN>,?K+T'3$1"^W(lfq4toKr<bF#N`jH/6LE$GNHMal9)EoB:S6k,^-`n8rEN@MLI%d=TXXUO;SYBph$RL=Z,E0k6Q!@lM?%rgY)hU7W#a4^oFhF9`Mn0B)XN!gZ\7a*73d"C4cKOCcsf2*1M';0Xm\B9o-o`#F&P_o^<UfW\p7khk(b.0b^rZ0*6XurWp&qAe&FGl+/a*KO2J'4!Co3Ogpcncj,aQRT-.uX!0-^joq@g#f?he?_74sX+uqG'&hkRoK"eY^i`Q,baNuWh9o#5nf+qrdcXV2jlHReUO"!knn60U4&><,*c12)q@kjMBCm7(f>Z5VG'8%=.bfa(c5ttiR91N2U:n)a0k"VJocO6/Pe@p,pPeit_NS8@nHEuefX2JZ@$8QJ0S>b'F^[jV]QojP[1"]3D?BnF:;4+M11+4R50+)kDU57q=Fcq32]>8cB3=)e+?jO34\HW4Nt7o[LL'9c%Oh:sXTPq9Boi"T!P<-/hQd*PoLCgJnT_Uu.H#(O6b@GL/2'56o6L%D55XjGh9c`3hp59Ir'C/i&P;2J><5M8\hUU`A1.c2^WD7o<opUjh();89-i$jK=YBufS+l^RB4JK&#]sXb;B%_9:]q>_+)VJ@pM.)bYL1N%9St*jQ<pM>V5"Q3k[;Z^!kM.!A#Y=QCK-l'DJL,,p$'6!O")ieu2tTVc@nX%LF/dYEf$t,^iaWM\spNDn+m,#Fls9_#~>endstream
endobj
31 0 obj
<<
/Filter [ /ASCII85Decode /FlateDecode ] /Length 1864
>>
stream
GauHL?ZX[U&:aGPf]c=C%TSZ<>OEG39!:o!au+D;dMLG2;_sFSA@i!dm^(fRlm,>?JBSQO1N=rp]>+<Z.fgVS,(/QpJDV_noNHd,0Y%@\R"EE`S5,f>dBI+o,@ej"c=31j4O$hVi\\YfC@EVG)>ui0e2:#>k=H#c@U/+r_dj74QZcD/(A'DMI"9=[+ufKs_NIT)@e2fsY'sC'=]ICtOi+k?SAfG!AI<q@Wj=!F*W4`8eee"8/2KVgM$@Qkb&rHb7&ESo?Y9u"n.8T8DTXYA9P.ZB3]9YN,e[A3i@8;gCL^3#3$BceK[_IrJLe[0Af6M*NpnjLA?$;>P%g%)Gf%;ao*BIH9D':<QB28=F(PW15,A9)@]!-FJ$"8reNIK9?k*>kis7sO^)IsU8+qcSB;mTL-E#%m6Nb0AH402fcEDOWYF4!m=Br2:H%Ck!lO(p4:Ig5tUXq%W,]\tMc+piJ'D/_M#8"aki+$[H!H0//1W*]Z?-kX$P5J#Y'39\&*)r*+?mZp'omR9sWQ4Y?>'$J\%Z1rejq8!b=)q4-Tk87A=1?/Mo;DbU^Sm$_MpGeCelAZDIf6NXSck@HF::hMNK=.2-j16B3@[:BKhQNaHZ0&2Y(JZI6H@MB(l@\R!/DAVbVK=S3-7Yp(1/V7(kPIf>.Ac`0R=WG+FI>%VR<pTcjNAW*8k]@Mr59X/o1X#G>hS*`3+ZPSX\>J.4,RQB,HG'42mscosXR8AE=("\-gq"6-U3OCT"SLlj"6#Za#+l7ZFMBPOo/p]B/mRQ40&mE*gf%CTN;s7XVYH"%q(,qh-Hq!B:oQCH*Q9(iH?4apUKcP:8(,gQ@K(RhlR<7@M*:)pB*;Z$m+&=*=#9]7BtMk]OPDGT_K\/TigbM+:e>AD1/&qhC21m8:rS*8#,b[KB!:p5&7G!d+=pc52l:k-c\!_)8bVDHuYHhRf3rkH(h!-&'mNBNgH\9g1`Jr9qh&1\lsi\FfG!Qa^r5l54Y.Za=fQMPNM"#!l#,\sk<JmN=odr$!:ZXC&Kg'']["g!h(\Sc&V8M2d&okHI?S_)D+.oJ<Wc1C)C?_UUh3p$qKfdlQCQ+D8"+kTA"D[[pDM5emb7In!qtCCfb]W;>mXV2Hc;SQdX,*\E4H\Y^l+^[<:J/:UulQ1/fs#^tSR"R#W1En)AjUO)smoTPcU7;)p%6JWdqW@ZjMjt"Z@2nhO-@uOI^*lAcZ-9PZr+LG+f(O\Za8k(m-2e&u;9:&T7&[:F=C>&<kFIb&OcKS4QqA6]`_56bpU+Q:/+(j^hIYM0<o@u2\QEX<RgH,gI<<"RC=4ocQCZiieWita>S_?#0#L)BVRk8C868qqCR`(bCDJ9J?Ncl4qV"f5G,KBGm&':o[4#CQ,n$A$l35ulq'&F,o+u]<LPue-r20C(p>4l_><Xrs:Z-jXkTEW7o'o1X+f#=KQ?7]Gi'[n)`8bZ@#2tVPWPjXO1Ar'25q;,Pj00I?OQ*I<4&-@>!*.bTEV_V2p8878f:=T@jb7]i>n_"GLF;YW=)G24]M(nqh:l6n\;qqMZa"]EP$Q@.3qHZB.X^2XZG`;6!3Ef%B<-0RoUm7>Hb_jki!U6\7QdNT]\\M:"pkh]c;)FU64WGLa[*!C_0"QIk'/RnlFQ4%;'S(G&nB21N3kOJ#hfoPG*@Y.EX=faO6"]IDS8LUo0tNK,H2%$toZauqDEW__LL\@Zd/Tg8)<n16r<rKN/'_CR!CL^ip%_m5hfk:EZ*tfc02J1R`'X<?]V^1,ptl\LIJ1`Zc#B@e*;("MUtAp:UY2*1nP_12LN8odWV#3b9r\'"XdgYDF';<'I:<_Lm_?p2d*V`ORpr<q=G#6#/oRQ-R*`,+K*.kJ!B_Cj8H~>endstream
endobj
32 0 obj
<<
/Filter [ /ASCII85Decode /FlateDecode ] /Length 2710
>>
stream
Gau`U>>sT@(4PFJSDoAs:#(nJq3!Z<$p,mj6X[>P.:.[31a[(?`tpM#L]-Ue,g/,U[l_r:4-ug]8Oq[KIhEG$rh\a5:'#gXK>f2FPel0#:s\[imK1]%%_`t9O\cQVNc3f:/rMi^m<C7+!uHFk+b#,mV&)rYSWgi4`"0ZV*("qdi@]hZ04L2W!rNRJpC)71BQ<u.^>h^7U;JkO;Oo.DQ)UKO@X+RVEEp"d/:^BU<FQD1$"&T_jGE/YF[A\&T7[f'!T=XioNC*lq"=R#iUH"rf'VUR%Lp<(KG:p83]ogXmCP72*]TDR0LUn+?V:ET1@@S7i=']2;<54f622%9=MT@SR)<Y!isZ6T59->5TeXmQ'8+@CRQ-uuka2N?l8m^Ah7m0%BY#qu(jC5_6j,eP^upfir0;b:O#R.LKAfR4eeL4O2BirVF8l!D[WApg!lQ:@NJJ6)I&o(_5<J0S]"t=ZG4:pM"l8)Jk5#p3;\K^oSa`b)%u"@#*#=7H7FrEXUFUK"1#p-pLe,AR,KI<N(e<CUaCi.=J'sfLo+:Du6+"8&YO0Mh2Xcds^o;]TZ6T[c#*DQP__9,(REG["O,gD.hgZI[A/(.J#(8muEl8"r4XQ@4Q_<Kth]OZ5n/<$1Irc8m>f6E#3!?RN+jrU6k\LkKi)bTF;<qbh1'NAX^_"IDZ-K+QU7m6_ns9i>;CtlLC]#94F^3lA#JO.M`@l"*'XH,R(]ZNnl<PK3Sr1D<_&PT&RtG\0^U&Z%f9p=XeWn=e%\dpUM%c-t!#*Drc<k7<8MD:lW>iAKE(n,SU.**F_XoOl9X=\Sk'rZcVED*^'[KOjj>8K4,+kNspp5ut]>tB#((K?agMKjn[>)(8^"!mMn=KkkB5UU+$=iKsWM<tOW"ciDUM-%nlul9`CoO'W7)#8LP[QSG1o1$&<2Hem,%aDVAbsQl4ddJ_^_G?5Yn?ILj&4u@3QKl]CFm*[2b^nQl8Yq%.%\?]"*lK7eDO\OYHKXclV&B:f:'O5]9R.Llbj@=(7<5M87jn5Q<;McE[;c'pn7_G$/AJk=d7Gl;2=1YKO>b>C%>(`Mqgou;94]VG25lXQia[C<E)oGg/Ek$CIUB9k[]Z1$[4ftNm$JeOXr@6V,_3Oh;QENV<FVk=%_d!lfG!K`%oY-5,E.-2ES@eg#SEGR+&EKng.(0RHk^b$U&0Hg>qNb(mR%WmER*u%J7S=&$!PPS=ukiFZLLoJeRZ*;N]!$MuS8e+n-cF5P3e,bqrQ1cWdrCCUfP,FD4fq/2:noE:]Y0?B]85DoT:(/<daJHtiku_8]fj!c)+\!2&NWA7NXGHDBVL]+<r72PqO4+7/LA<.!WG#*DO^P6?VMB5T'/]72R1Pf-A7A2cEJRY!+[M>d0Q-)$F)_P2QUTC8hPDJC2ppX0IdM]=aPl1)g[Ia0i#p<c!Y$pW>FWCP4YZ.s0"NX2^Ks3fSc@T=p5a")OoGp'+bV#iZ40_qlL58jp2Ue53dj1oGZ;-/UHk*nC)nXVd@#LrI5C??WLm*/s53tDeR`]!6R"N`tETrirZ&KT:&2C97Sn-su[2_WfpD\,T4eJni)8!Vd\f,n"5+P%K3BtIJ*WoEGOL`uBD"&h1u,b:f!N&kjtpU?PAi]JqhGB-J\+(Ot(H;An=r9N`\L_7DhT+bM:[?@),>A[o2jWK\slTHDDd[=IXJ)HBPNQ^Om[PC$Z](k2JWM]MQ%DB>I9AQMhHt$OmYF0m6Z;lJba].R2PqNTj5>oFdcCer@m"3MqFn<ZMR&aaX_213pc$Z?"AR_WQ%5,V?Hm-W9Jk!CmP"maZ%\jcG$V$2EWP<5#q=X/r%\fMCpA>TT^>"]^%fI!qc69LZG!Vp.e\DO20#3oUNNKTU9h5t;<g7WEV=H'5g7bl?G!Hqq1&A5VZ=T3$0SmHh+LEZqC<>phi5W)]>V0h0B8c'nGgXf^&_&Q3Djb*b7[f8ab8GPJa]4%B\)uSX7MR7;)P/X80A&9@GTEES&fGh+pqpA!g(i3MV9G+!!VkpS)U=DY?>*+Fn$C$L=TM'DjKjfGEr*#u&ki2R99R8NJ-DGi89pA$OETa?6!=:NJ.1h`dZh"9/sEiogodU@6]>?Hg;Bj\QQhp"Ic2&is6O9jC"qPgi9b\GkpDE4:ATQ!mHY:f:)G"CN+hZRUH)V0#TqeE4oh],gECc['[i'0&08R5O3LK\5S8/^quI#:K.o.:5hVj6G(<K"p:nVo5'0iR2p0.JHG"Z>`[;9uGe.n)k&OCU.uL77B#;.j="[`'Bi:B=LH8[]).Ne^9<hI8r-9Js#0T,uWnfOYpU:NgNm')M'Br.UY$%sUqV<]KX4VD-4`aO^KuJnYr\Y:"D#;t\Bj>tq2Pku%s6PZr8+&QSn#mp>m6L%4ZPdclZ/nH?l-jp2Ib9j!Z;Bk%q]Wh!*Sf#tduJX/9K,T$.jG"@cXF\RKM.^NEe3\NjuSi7EkHcc4sP2CT"&iWN83bC^*D9eNn0T\2'*6]>g;aRNOcd]i?*oeUYCpECs[JA,bbH\kLSSMreQ_ZiKA<Pql);=)Jl3=k*'Y>=JA[1Y;IK8WFAr#i*f$d,fQ93G'ZR)m_WXp7lHgg267"ZS*/9QCVsm>7I@]-Ff6*^WI>YOdA(%=[1G?g/%&PR36dYRW<5SaM;;ibr+;CnS'caJYh`tj2fY?7o`b</84\Me;-'1>>jsW^h7/@UNBn"FBc``5R\[a8rrBb:[#b~>endstream
endobj
33 0 obj
<<
/Filter [ /ASCII85Decode /FlateDecode ] /Length 1990
>>
stream
Gatm<968iI%)2U?i3G.e3%Q/G7-uS\\Cktmeqr5VdL.Q]=`sCV,s0rVf.SOLY>gD5:<,/r8:U\(J04kIT_N$I1J.]Ig;:04$lFce%5<ifY^H\UmGd`S;3WA[`-:f@nBaO?iX$q5JcC;<="%tR!p6:O)A#O>!/*ijPC\C($BNd72U4,^O(%nl[SO!7rYhF(+V37Fc+1sB@XXa-jWTZBNY+kdI,I,;9:[)G!]pL&bG-]L]I0!n`WBKK;-lM!M#TXL4:0X&$R4QQ,3uU]MD1kn"Y!!9Lf>e6SP*@s+H/ph&@(`,'Hi?-0=66cZo\O\+p*YaLQ_-lqVZ?;=m.)cJX\"poIVofH1lhW=?2f_jW$>D!Q>2(Se0e+@-G2,pf-5AJ:nVr@";b+KtJ3DiDC4A'aut%P9U8;p:AUiFagTprS/jJ!GsRQ?:Q_250>Z@?`eVi?/_r#2#,j7_(ZGCKo`i_M?-Fj%%lkT0R1,N4B,9fkUNcG..)KD<=#p'6jfM-Ot'/4$ImUZHnP<e-_o@9%gC9?`.j3Gf"[_YpHAoi>irY.P*^@HktEIE)<6'Kmdi"/R$_pPNDXbE(%fc09VN\\>Gk(<+t1>%^9`Sn,&<AZ#$Y,T86VK:+f&LS!8B1$P9hl"FV]JU@-rqq&lj[U$rVl>?rCjZ=qXpZc-DQHUI0F,$cioefaK(<dr<NO.*_-6K1*0sBr*[COX]=][K=f-LEl/Dr2YYa3LOuE_G)1?@8i0c:is"c#oFM<AsHXLgq01eQ3YmQcbgb6VF0HH')E;*NW8ZhC0!oECt2@fi4gJ(d94R`rISF,'^%`a2[X:h/g!MBIZ![hZ=r8*9X15Eg0L`+q@9N'Xj48pr=^Xn:k_+.:$UTo"eoi8]0sIe5Fot;:Fp)ms!Hh\N[?iT8Tb*\%O#NT]@:,U1/Ep-S7hRqdV<2(A9KWI4inOPT3#+62W*],Kt`E:pncidaXoJV>qTQ&Z<_9$0B#W6?aR4Q$/>-l\<tS%:<_jHHO8$Vp$(TQ-&sYDr8nb$]JRW2&WfL5Sp0>JeE4sUEXQ3G]t7C`b!%_]pA$iNBSs\>n'J[=<\ap%$/2$oiliYq*&cDiLtipB&0du$T%9Jn5`Yk]Bi"a3b+hOKq!]\b#`j@3IX&MY5@C*"olpt3PBQXWdj\Tmn+.aVc(T/n*^UV<25hcqk5[NnF^_"h+4if4Wb>X(C,.=Yk<dWGqtoB!]n&7?kR7O%5f1:"!!9?!*0]ebTmn1;]`eQ+hSm&.;*q9U\/?'s@n<,Oeb,n(H)7jX82te4*WRBi-JE<7c<tV(qnJJ"FSoc;0Cb^CKd;rn[V1J=\t?me.*U`4]SLbXE(MFYCOruQa>pr17%HusFn%34-B)W#%%1C\'b)sRSd672+!/bdEM@mhO'D2uSiV^/7:+93@Q!TX*ljColaN?b.k'G"T>WZCQ@3fd;;GCQ'O6qdKsUM0+Oo%Xr4/j()16b7GnX3L<gSDP=/acFD#rA9THO`ABofO>1*O`)P!+sK[Nqpjq]m/i,V0W+,TO6<2UH#j%8!N_7B)U2%rC_s'>/l"?=s6[ki[s%OLgNX)qmT5QV1Hde^E2<7i0USUM&iYTV5^e[6%]&]6Wa=VV49$!XKTI=GDT'dtMEl00IP6aPoGrO&e/_?F:elYFtS3>-rpt7k,Qt8T.4`0N>KJG-VgaH!3qe"NkH9PD.K79[HfOD7)b>>Cn0rFNj1!c;LJ;Z`rONZYclDTMfq!@!*[gVB!(XNK1RaG85@1M_in4YB`B,0*Q@9q5P32SRQMDDcSOKN-nTD/LDc<p%MrB-d%c=q.ojRTkO_3k--NuH!s<h).P>r/^Nnje&`cR>:I#L;4cq>>^t2$/g@tK5>,fo,s+PlQ&H*UQGd+;Bj>din+jWo'=orA$!i8:X4=)t#i;QF?/"c_g^-V]<?CW2YWXbmI'K6K+SH,AZ'Z33BRbgK7si]ZPT6WXKq4rj.13G0fKYECO8YI(M`SCVnNUAhSHo~>endstream
endobj
34 0 obj
<<
/Filter [ /ASCII85Decode /FlateDecode ] /Length 2110
>>
stream
Gatm;968QQ&AJ$CFE%X%))NRt1tnrm"Cb9&P)qYX^#UriA!^*!jQL"ZIf8t&X@HaYA2cb^b;7uQp")u:nF/(gs!MT4O)t*cR0$qR?NL[-!:pScc6j,9G9ZZF9LAJ8nQ?jiD%cWnO*pka"Fc&FV$3gHcFo$Y?5S58&<HC<_gDn`f5d/='#\"Aho#A_<nEZE8Jne$%V<pbELP$M?;u'9^m5Uopi+8U"ICl^A-NDFhl9/3C!fjP"Jnu:JVYH>G`87<MZOBpZO,U[F-:au!^WarZ%+]N?P"hdFo,AI[hD(k/d-LeLKY&sb'4J5LNCBS`A-m-&)kR!Y_\&G0Z%NDiXH(7G8'$QG4^1WbTJf3HUKh[pG!eh:O(gp:Dk!I[kBol*!)/R6P't$=YQI4MN8j(,bcJ$>.Vut$kR5c.H0FUr7:Go)(tupW+mQ@'T#VC*6tG1*hjUtR[o.o3F=HK`++7Pff"!S+h.mj2EV\f9F-Q1k@<]alPN6bDp3kg2_*AiKJ>2ink>]o7eALnf0:1u*^(PIRLgJl)JX_hVs->W"O?UBQ((\%8-0ESfiP2Ra_J@7WW<i]Z%O=d@ptTH$Ga;/2+2g&I1Dj!@34AC&&h(\P<`@T,+d+J/Ah3Y34^N<*Ya\Q7?sekn6[MNUT.L,mCepq=5Eo]EJXjeV8$RJ$;7@V1kAj7k[pZ3Pf$V,$YWANQ9S4#6LA%NN9rH/U^?>)q^*n`*%J@^bG$OE6ZQ,'FgKFbbB2:!W'c\[ON$6D=WU(V3j(g(J&VS'4'LhL8(""XLn90K"g8dtW`oT5B[T)dKnPaPW)Jt^a3<)&d6-6b$pPgP"_oQo7REC*Gi<i\`"T[X8V:2_l/G95C%2V37V0Om<YamlFRJGkG=SK5lEJr`ILgI!V?nRT#3ig]=/F'A3P'S7f-ji)/)63a#WSU*@nTlW"uF'C1p->9Ks"]jh_LNh*-s#fT=4*1m?[F!K!r^_3!t:/[l[gFmWp"qY%qk+>[h(?fj2W;H`uo(i2dr`/I`8JQfUf*XI^HI-<WPJ(tMQi.?7FuOg!@kG+5Z*FD5c7e>2PQ/@XiNr&ZXtLZDoG;>C::i/qTs.+f,,*tdA9+FlsoEdaS*:8`8?SS[S#s+8WRkCf^8YP`JK@*.JPBe-*Gq5SrHqo!e_<nJ+qBf0LtV97K$/rN+L<,(&1C=nci09t#jj@-VF)>[^@rL*l!WI/`31-<7\phJX^<+s@]Hk3aOjIa#_%$W;KVmUj1liFkk;M7oDkSF_h[9B@6=m:*`$Ib7\N!7<"VDA"qkXHktWl?$<NQTr+0@%V=69"*qm_pF-/K9B9;R[VK[E0[`"MMs"DoPYh<Oq]KOm=*g*L&Neq`4O]()@8OJ)!,6ZZhkP\*ht/>;FruB(rnrpt>!$oks+tK.XBQJ5<e0?sktX,d>bj%e.R]i+?b\eqSA*><=Br/9CZpI;m4cA)ig6\qtcJ1qF)"HBu&Ks*Nla\<\"MC*kkQh,X-79J9!N;mRHNf\22EHgFm[1lX=1R5Sr1Qof[L@b>S`$+$ep4:5O.Qd]'_VfmqpTC!:1.`N8$@`:YRe/O,q<u^N!EM/WrfqX1`Q==jI_C1k@4?,H=?ceg4a&-mdhh3BmoX2mPhc9[QOJRM@g>hGinj$"-h41OOPkZ_RG9hYsg$r+.$['+JAZ6KfrAm"&SW6A=$O^!Ip>+\GW!du3JMgJLK!-`Cf<$3$.dZN@jWY]eYT7D$rr`A"=]QMLiOI5&jmfF^+.4&g==7n#DKZd-Xp/'i._o(&)SrK'n)oH1S\;#M*4Hd"CJ#+fF+P1^<ipNuXVT]8>Q\kiJQlK#E,X/P$+(5?'D[Ft1dRcOG:9Je.1];>j=JG)CUU31KK=#[9Ke+$C6V35>f*U%3;3#lbG"%D$>=f-S'QntPHut/cJ13BmG!;cQ:7Y7T7+>bQlau;XGD`(MdZD[i[Jm3_@>]_6K+6A+0%.]Sc3[1T?DP.;bWBK<XL??[NegQ#:nS4e*k%PfY77:$,'";0OM7mkn2]TAb>#h[]AiUrq3:p8<<9>&J)GtJ$=:aa7b<!("*SD(gn,M-(MZ^"+4iB\H.;T"2G-7)>h;uf=AgZ[rF.'h!STpDKe+.r!Tk!?*a~>endstream
endobj
35 0 obj
<<
/Filter [ /ASCII85Decode /FlateDecode ] /Length 1850
>>
stream
Gb!SkgMZ%0&:N/3b[\4T),d7UWc*6(dO_u_m)CXR:nV3,`iFeGN\7q8^V5JfA31U^.>khR!Fh00c4"@2S/DXmp_3XV<YE*6e&eR3&^pT3KOTi$^X-d<g]ldXm9ZS>*qu'2;[$m4Ul^GODkcbmc-dUDU\9KkN:T"PW>HFK'%+@fUJ%r;.mrP32#g2>=&.TFR@(s-R#6Z3c><G32p84=]0)j,JoN.%O"a8kK;j/qd)+57D/YlUhGVP(&4miRdjj<RMVgBe<(*A)!Z'2XT\<LHRL-)p9dN5+ZUdIVHEX!BJ-d92N>p'nBd"h?8>Yak(&UhTPf\TrrA7tl'#gY5(5Xl&KVb/>!Fe]#GYV"$8q!?mdpkY8MguS+77t_#&U5/(kORZ^TnoNb:'e^?LGF1?+/q4mKMERl\h&.QLfUB-o]b`?C5DK$GYR\H[O[R'#^fZSF>fV*H1VEAR4Q;8GSd0,nPI4jgF`N:0FHSFkn3PO?t$(G7-]0LO\1D<d&4,=.S<TYb']Yf:Xl9_qSQuNs3>FuKnkk4!HI?:Z&<PA?$ME.7^K^,h/nGQD@bqgVX83KdQQFIfb[#Z5Ft(FaKlr,BsR+<O#ZP-nG#=ZnPE?"4W6pM*^(/.H1\o_XtAq)9]+Bs6-;l8X3SGp-2#'M:dbT8`[;''\U*8!6t?P3"<\P,^EVjmNuW.6,R@fWSW7"mLe_N=r%HN\7EKEYF\J3+(b4i??drVl0)nu$dT.+plmjhcp;QF'0#++7hGS,$oenVNdQgN:ZYm:HgI4/R8%P=1bFNWX:e#FAHUi%$$*&MA>>\g:]33h43%3\FbJ&NXN.,d:)sk#Y?<*?DNN!u>Pkrs1Mq["-9/m`F#H!P_9mmN_l^qJpIi1&%6JP]i8uHHUgOoFDd[28%o_@%#<Zn3=Sj7jEVWtu!e>H+Z!*V3[Q!dJjB'V<j#Fh&p34<-#(.YU5<[?Vhg4W[@cEMXD!\p]u/&=0"rA/Y\^m:2EP7uCOCcLmii(NS%Q&jE1+ItK\LPI.nJA[RL7="q\$@a0d:Ep.966?jZ+eb[?:N:@5F68X/FQ(\q3@8h1Ma-+D4uf)#I",k27IHhT=6ef$Ds)HNhU^;el/:WOA#PB7Pn-Qr=)r3%(!>p:`iIr3Fh:^cf$s(1F/P$G6'JC^lOMO#dU3\.m4JbY1(d)2J<oA$C'4=+@sHA$!V<!m^,LE.L6=!g4h7:WpjM,tV;A;=_u-lt0pkKC>d:[OZV\2h@F>nV6"XtJg45df1QXcPR5XhD&RSba!_<)U^aH&"+1F=2!2^,,#>NX+A%piaZ\ck$dts9ZC^f@F3/&W\,kQE:gS<n>IA*=I1,ghurHN<>HiNW(O^r83S;!1+(Guoj='POa[;0?hgq([\NBQr!-"HF)Lj3J\lR0QnXA"P-k9j!E/okIBNB5*jQ;,-bc1BY:I73BX1&8)HHJ6)eW</$`f1*h?2R9om)nIt=<^lF[?HWff:5[(ckrgUa-@.95YK)H\:8\-4"`s\?r,?XJ-+=n>iR!+Z4?kY&I$'6H0JY1ql(bk]s'l:aEQZt+%Ns<T]<:kLl"[SLo_,r/WLIoFe<[NqD:]p"(t?d(bcADD5^E/ao<`;&`aT:B[FBDG0atsFPne`(Ga.$dm(hU4N+Nf:)#,s*_cDcA2LgtHkCY-LFRe22(4lc(4YiKJb;)M7U.WlKYtk;U`5^VG$be:U^dK`1gkY&W-FV`FFq`X+`T_lnC8SWJIV@89bcDJJ)[G&cm0_),EI6I'[_ZqL33F;mg^RN_P1i0TKgFN'+3DmEZ>F7D!WKEB)H/[.)t9GSZ;^\OAprhioG:BYeeF1^.p(ZHqB2bk(`7s'i;e33rW`!D)5I~>endstream
endobj
36 0 obj
<<
/Filter [ /ASCII85Decode /FlateDecode ] /Length 2009
>>
stream
Gb!kugN)%,&:N/3m,Z:5,R?sQ]]:Ye'TY&\.$]th+Yt.+Jn90T;?9A0maq15]L[&gkL+J-WLU5(&dr)#kNjf4T03&Ch.O/AqK58'?MNRd1cm'LA0K3(d<ISG2!ROC4-6bHHd?quL6-!jpNb!Q*@LWGbed-E]@DTO0HlUHGfW!S`.DSo3h"-D/gU8L0/U;:fgEC.k+mf%Bor2GP>5*Q>g#Q5<jg6:b%DdUoJ$V\H7b%Ejtp03^1sIkji4SWnbkE[`0)hJ7#LF]LdOJCSW&r/c_Fs_>F7*/8^`9X,^@0oJu+6H3DE#fpI(1[A00E(M"uT-;ep@R^#Lq\4SGFs.Td7?LdKb^V\(0gSNe+1\^^N>abt[Ik@ou'SO[mL+RqH*+m33Y@,#h9!p&>Q&kbA9i=hfHJ;[V4ih=D%*s(*LBp(E2&?Vajo^:d^gA6*.GtH@O<@aJO3'Ji#3Z3u;1jTDZoK,H,B+)Sl]RWM&gHGY:cj>)7_rK4h&I[%*is;4I3^RN](Ut"lDM]Zn;9E.24;Xr?He&_Gk5'G"\`"Tj6L,1%/jHZ@%6Wt5,D;&RA_pr9[KCcsR*qpjcAfsb<Re&&o#@Of$,"&P*`EbjWe1;JJM2NhQ?)jYi$n_g"EQhS*!EaeA4;0\.3^eb"<NT0!/NaF!T1$:\k2[4a!AuFfn0ucGRgRdO:;CM8;L=</U'5Q[,M2-=WBq?$j0pE'(Or8/Egb`*VYfTPdE")9s1FV9/S)npA9o\[prqCdVURjXmHL4*k:%qh<$*)>Hc](O(D83Vf!ktCH(:0?:i<4R8HFH;UX&2WW4'hA%C#ePbb<_OtQ6lb;ggT;E7HhlAHDcQ8%Y8olmt68$qaT\&3`q?8RQ1Z3#_1HpXl=dSscfY@1)jc2rW\X>Bop%G(]n]6&OZhoe*F.<in`_0*9m(7m'##G1YX]rfoC>&H]:pG-2n5cbb'KJs,)e7XB(\KF4n%me':\S*+`Ln]@rd(,"_:)0c0d_*0"pd*&hB1ABfV!&XVR-[.HPnr/C;0,ai@Y>^0L/uC:KhKA"3='uFd\aZi:4?"bl*r:iotn93L+_OoPiZRjO?jpMCMKfK1MPQh>*b(O4eSNH<sM,d+j`U`3--/p_`/J9mN<hpR]d;Zg<$V'&2W*P1EO9"R.2e<r#d_,-*!gnDJ5lM<F-iB'1s!]=oa+tJ3Eg5BYTb$9%$t:24(I6g(LcWQ'V$)(.K(tXK+Xc4_U>]7]K@3>G<h7HeB<^XT8D'E]8='cTdE"0PAoo`(2[Yk%^lq1=T'^9jKBJV/=CQ<*n;f\9<s7b#GsPeYCD%e.f#li/-;OcRO7J;P0&PG1ul]'F3bZR"hMWUA,k?S)PC16sE?F`%Va?bm;"p.3@Ic&>8shV)XO"6/^*=4u).F)DfmMRa0*RR%p*EPZd:OC/5n)<qC[8HEZAnF3AW1FNn>&<Pad%m@S+Z)JFFT3?9%%$[JUj?2k#,#L&)oR%us1lQ=LGT7bFT`R^]r'%:i,2KN*;Of]=T\#e)R0sXigs*u]DX=[Tp^.n4,(Cl&]4SG0bUIj+YoH6j5JOAn3a5]D)IiOLsZdZC%gj-E\$<UFkZBoc?-iEkTp8fFh92!mG(;4H<b>>e;Bj`Q/d%Md_6YDDZpYK\0/4Nd=H;G]/VeqJES.!]0JAj$;T(Rm6ogtc-*9gU,/e=]D%T;B9eGJ6?DTu/Agg8psR@9>%5a&CmbdhQnc(_R5/M/n,qHB0;o;B2+qN%//U$8;6#*fL@c#o:o$D5L(GLahSZ.[FZ4+Zd-)8;naN;$iL%S%TC&`'&0%FHu%+#K#*G'Xt()_0p6Z5.W'Xq^F-.X*1[4gu58p0?IA4l+3ZO75>GT"S+\7sI8j#D#5ir:C34j4ZZKC=h@4hS'oB:T@3@D-Pe[rSNtgcI_!`?<OSGgKiR@b5R:P^2+S3+7MLDrVW7Trk=Op2.rl*kU%ck)LKlAF;[^fF4Z6b>F3s&E3=^)kjA"1Q/V0g]hj!'&>\tZ#>J[aP*SRe"%$YnOo~>endstream
endobj
37 0 obj
<<
/Filter [ /ASCII85Decode /FlateDecode ] /Length 2597
>>
stream
Gau0E>>sRl&q801ka/Eo:+[AW^@05\'-P1.ZNj$gWNG/KEC:@L>8bKD*;8!VQ7QAU@KNl';8JCFh-]'hC+0i:r1iD(Oo]s!_oFP?Pem8-W(/t;?bkoRoR17_,!?O%^qM0KM`mj_SkInd`Fg%H="%+<JQh<P_hdbO+h/S5W#tjicX;.B=#/r(l)udjJGBF%YKmoE+D*@aAss'L,5E]iRo1U&8;T]=\7I4E00HF_$;1CYRu/"[ou*#LdP10A6sf*P0g5[TH9PS08&U2_Nq*\)M[5<:3._Qd2^3^(U>'l@bXR7HIMAKtDP3g+U!37?D/kS^LN-#Ccp@>7T<QZQ^dHjj*$Brc]+6-./i<S'GfCjaSp!Y84hArA&Trs!\aFMLCqFRlJ4r'f+L-Pk:r%(h>^n+dY31n.@XtnK0%1.P"D_=_\=0#8C-Qq#$;_PD=n>%UitI]qo^oMgd1rNQK+K_P$\j3lbRH8^L'UTZ9CTV)%u!5<KZ0)6@d&d&0pF`XQjI2=6tG3Z0em*W9VANmj>4P(Ik[<SpGh)FLZi^)5l6m.g:^ug#op/!P6/+@?)T-5PR=!).E#,MC:!#[^+p;s^l@0sW8&inb<fltQ[Fo&9UDQ.,aE/P0<4E7+YfC\mIM/@!KCBe**Qn0UZ93Fkf+2[h10c.><BdRc'[)h@U@PMkWse%oJ:=el[dN)3_!_5:JKk+<;,8fXV84"D]^)Dr?Cgo1WqI&0rd8r!s]JST63ut@PSiZ$6SM0]nRNe`b#\=H?.4R@VrAbr/>Wif!elBA58d"9$O(d@5SZ'UHYOU53j[fgfhC#"lhTe<s#C"VQdH2s"I=<eBe6JTCM0C'X4alOP%@Ki+43/IUJ.-e5EG'D\c4bV'7UWJCOLr=t1)N!`b^c^Z!+#DEpKjn-+;Tle31)mVke[4T,`?Puo4;a)pAGCaoS@n=i`nWdZlHNF!^Qr5N0br,KG\J:.n#FlT"^H2]3bStQ[88GJb.@2mh[iGZFGn.@;Kdj7doi+J^T?O;%q;[pgqK4Q4SPWqN(DbXg=\QTDo^"1&9YuX;M=Qm4\Cn<pAo]lhd-6Ns4Wo+g*/lKp9[G##%Rn`'Q.5=[;<npTKl5@;gZ&))l$B`)51=caTE\fF3TC0WXBGfotaU8:H4Md7M?1fu.LfGaZ/l-_P\Ta+Co1Y%SjDE'!2mWab*.bCFQV5&/P7V/BU6N4*e0nkEF&)GY]g)&Yn59jrVUE5A49n>\O6XmKPJG3GP%"1&/P[+b:tPC@r+6r%EgCNC3NS&o-CtlJ>An12YQD&[Oi[:Q%O;q:HI2>["X[+5Gn"Le"Lh$JKBI>i2-1#_$f)=me%,uT%k=hA3AjTeoh>*lL0Res1YhY*NNnD#]++A9rh6eQ:g8bSSajn8N)cU;f'9NtXTP'$kNabC%gT]N/\`IE?/>%UEd)XgW4UO;?+oZM:"(p_X"aFUP[]nanlP5<bbKUU(E5a\DXV;OD5!Zn]fln31^A1slEYhCgQJQ-"-TGCT\psf!P.&n1UlGNQYkGkU7^oS&\9a+;&S0DLN9,ldcL[cgCRCO;%BH)F[?4=_9^!qM?b!S.h)P8jq'aHQi88Gb<e?!YuJ[bU?fAn!SsB%GTd`_j2k^7E4<=2%W+uo`YN?L5,ZW-k?m/ph1(CM,%IV8C9;Gb]9=4Pa![clDL^KgfQl+)rcL=b`m3^Y2P'6ukWEB9:/iQ]WN\<cUj-.uc\6Q+<^>DjF[tR<4^p+W5%KZ7q'oF>_ugi7!4V"':;3;A2TKj0)J^[7/W*d[e`MrfQL.!kE",j;6#0rY>)t&'c`]!7nApE,^_Ft2M8o\.QF/FPCp5HLPM%=NI%DBUh,5?E4S3C/>T`i5(YB0;d+a`07><G57]G;NZu4r#^3i"hMsDtP62c44Vid/,[#iH?0]0t^(h%]/q6-X1^<Z(l.JC;Hs#FnUANcYkT2,r!?qD`0UJHAl2j=md\9?[jjk,24n4aY^TdX$/M-Ah'$=iR?oe#3'WE#ro/DmVV%p74E*O;DG-tgU#Ja)^L`<#q,<L$/3F7?$/(jOQHNquT^,XuQ9$ZnZ(RdOd_+BQ..(PTT.kqVj7mMBc`>gm]E/PO`4bBg,U>M<k[B#<5ImIU[2,QiX?$e1fc@690k:4EV+m1e@l837Q\/Y/XH.1#b`3,0eQ/If?f!Od^.)Yc:p,H=aW^3:p_YR[+nD?o"1Mt0QGoR&`6k-'LX@tl^]FDW(6N1&_8"TPb^Sr4jqWEMkU&F+TRq%$j'iV'c]JOVq$L&N:3rf<Fnh'8rWba5au0H7cuH214tQA/gr1[1)&e^k=I4H&bl<Ff>VLnES3i%FhR,r\4,X)=hO^gAc=FPbCJ>D#]@fRFF0q$NUAg6t^#8tXH2:XuGo[m7"NN@Q(JnOT6Q$`"gObq'8V=W)Jf=8JD&oY#IUna`Zla!Sc3eu,H\`?0cAD-c@S/?>6W?+oPcZSs<#7dmAP<U&+=90="+GPiO:rF<]o9NsXR^7VjI1cXK1Bt^W1#<Yg>5sV@:8\$dIi4S6)0$GnPaqqJV/!4=gAWoJg!t*-7T6`+cc<d\qN*eo<\V#SkVM$i1rSJWM2oN3(mLZ()*&mS+"^ptPD`qMK~>endstream
endobj
38 0 obj
<<
/Filter [ /ASCII85Decode /FlateDecode ] /Length 554
>>
stream
Gasak9l&KK&A@C2]OMoEA7r[O>2ko7$?<3'HJ-Gu;3@\SNa!q-nJsW1Cpti-JbESsB&7n+(eR!Ks/QUuZ,G`]K/LdVYU,4u(:1=A?;-J@"qparSr?EF?B[6_JrqoYfj\'E#s;438s=<N^fXM$Jj[)b]=Y^n\h(POU\ol;@]XdBjN/d?pcN7spK('qGQ%67WUPO3Ohhj9"$YgaQWpP+gi%C^B_mpu'UaStTP/su8QN$IFne'PaPgdZ*P9uq*+OlY^mR_G9'Os>(<_;3\JU%+nRE:FCM2,;\.dX@,r.amr8^BRk@''+-SI,f4BrRE/e7__?>H@MdYd%[kZ\B^2WUqoIk,Ijh-1!8cbk?t&eGI37r@$'"#<nS?l@<oVn7+"'>e6#1)BJNjbqF)juii?]m\+),JmN1L\Yb0JnQ=93HXb:iY"A;e%psu,lE/k;6V:<=*gW)Ddf#b<A@+U>lDPXcXMgk<tDF?Qc$b?D8+.HNkCs'<H%I_oPL(!rC`g._J$:ART3[&Gr(eFVl&eOVB20UGPT&G_`<Z=m6uTc2c5jc\,~>endstream
endobj
xref
0 39
0000000000 65535 f 
0000000061 00000 n 
0000000145 00000 n 
0000000252 00000 n 
0000000364 00000 n 
0000000569 00000 n 
0000000774 00000 n 
0000000979 00000 n 
0000001056 00000 n 
0000001261 00000 n 
0000001466 00000 n 
0000001572 00000 n 
0000001778 00000 n 
0000001984 00000 n 
0000002190 00000 n 
0000002396 00000 n 
0000002602 00000 n 
0000002808 00000 n 
0000003014 00000 n 
0000003098 00000 n 
0000003214 00000 n 
0000003420 00000 n 
0000003626 00000 n 
0000003696 00000 n 
0000003977 00000 n 
0000004128 00000 n 
0000005154 00000 n 
0000006041 00000 n 
0000007838 00000 n 
0000010101 00000 n 
0000011922 00000 n 
0000013828 00000 n 
0000015784 00000 n 
0000018586 00000 n 
0000020668 00000 n 
0000022870 00000 n 
0000024812 00000 n 
0000026913 00000 n 
0000029602 00000 n 
trailer
<<
/ID 
[<74ac807129b3f39d320c29ed15884854><74ac807129b3f39d320c29ed15884854>]
% ReportLab generated PDF document -- digest (opensource)

/Info 23 0 R
/Root 22 0 R
/Size 39
>>
startxref
30247
%%EOF

[general]
name=GeoDiagnostic
qgisMinimumVersion=3.16
description=Automated geospatial environmental diagnostics using Google Earth Engine
version=1.0.7
author=Lenin E. Julca
email=ljulcao_epg19@unc.edu.pe
about=Plugin for QGIS that generates environmental baseline diagnostics using Google Earth Engine. Calculates topography (SRTM), vegetation and spectral indices (Sentinel-2: NDVI/EVI/SAVI/NDWI/NDMI/NBR/BSI), land cover (Dynamic World 9 classes), precipitation (CHIRPS), temperature (ERA5-Land), soils (SoilGrids: pH/texture/carbon/bulk density), evapotranspiration (MOD16) and erosion risk (RUSLE). Results exported as .tif rasters loaded automatically in QGIS. Generates technical PDF report with charts, statistics, methodology and APA references. REQUIRED DEPENDENCY: earthengine-api (install with: pip install earthengine-api in OSGeo4W Shell or QGIS Python Console). Requires free Gmail account at earthengine.google.com and Google Cloud Project ID with Earth Engine API enabled.

tracker=https://github.com/ljulcaoepg19-gif/geodiagnostic/issues
repository=https://github.com/ljulcaoepg19-gif/geodiagnostic
homepage=https://github.com/ljulcaoepg19-gif/geodiagnostic

tags=GEE, google earth engine, remote sensing, teledeteccion, diagnostico ambiental, topography, vegetation, NDVI, EVI, soils, precipitation, raster, land cover, reforestation, erosion, RUSLE, Dynamic World, Sentinel-2, CHIRPS, ERA5, SoilGrids, environmental, baseline, Peru

icon=icon.png
experimental=True
deprecated=False
server=False

category=Web
hasProcessingProvider=no
