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
        self.setWindowTitle('GeoDiagnostic v1.0.0 — Diagnóstico Geoespacial')
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

        self._btn_exportar_vertices = QPushButton('📋  Exportar vértices (.csv)')
        self._btn_exportar_vertices.setStyleSheet(estilo_boton_secundario())
        self._btn_exportar_vertices.setEnabled(False)
        self._btn_exportar_vertices.clicked.connect(self._exportar_vertices_csv)
        vl_der.addWidget(self._btn_exportar_vertices)
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
    # PESTAÑA 4 — ACERCA DE (rediseñada v1.0.0)
    # ══════════════════════════════════════════════════════════════════════════
    def _tab_acerca(self):
        w       = QWidget()
        scroll  = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        contenido = QWidget()
        contenido.setStyleSheet('background:#FAFAFA;')
        vl = QVBoxLayout(contenido)
        vl.setContentsMargins(0, 0, 0, 0)
        vl.setSpacing(0)

        # ── BLOQUE HERO — fondo verde oscuro ─────────────────────────────────
        hero = QWidget()
        hero.setFixedHeight(170)
        hero.setStyleSheet(
            'background:qlineargradient(x1:0,y1:0,x2:1,y2:1,'
            'stop:0 #1B5E20, stop:0.6 #2E7D32, stop:1 #1B5E20);'
            'border:none;')
        hero_hl = QHBoxLayout(hero)
        hero_hl.setContentsMargins(32, 20, 32, 20)
        hero_hl.setSpacing(20)

        # Pino grande a la izquierda
        lbl_pino = QLabel()
        lbl_pino.setFixedSize(90, 90)
        lbl_pino.setPixmap(self._generar_pino_pixmap(90))
        lbl_pino.setAlignment(Qt.AlignCenter)
        hero_hl.addWidget(lbl_pino)

        # Texto central
        hero_vl = QVBoxLayout()
        hero_vl.setSpacing(4)

        lbl_geo = QLabel('GeoDiagnostic')
        lbl_geo.setStyleSheet(
            'font-size:28px;font-weight:bold;color:white;'
            'letter-spacing:1px;background:transparent;border:none;')
        hero_vl.addWidget(lbl_geo)

        lbl_sub = QLabel('Diagnóstico Geoespacial Automatizado con Google Earth Engine')
        lbl_sub.setStyleSheet(
            'font-size:11px;color:#C8E6C9;background:transparent;border:none;')
        lbl_sub.setWordWrap(True)
        hero_vl.addWidget(lbl_sub)

        # Badge versión
        lbl_ver = QLabel('  v 1.0.0  —  QGIS 3.16+  —  GPL-2.0  ')
        lbl_ver.setStyleSheet(
            'font-size:10px;font-weight:bold;color:#1B5E20;'
            'background:#C8E6C9;border-radius:10px;'
            'padding:3px 10px;border:none;')
        lbl_ver.setFixedHeight(22)
        hero_vl.addWidget(lbl_ver)
        hero_hl.addLayout(hero_vl)
        hero_hl.addStretch()
        vl.addWidget(hero)

        # ── CONTENEDOR INTERIOR con márgenes ─────────────────────────────────
        inner = QWidget()
        inner.setStyleSheet('background:#FAFAFA;border:none;')
        inner_vl = QVBoxLayout(inner)
        inner_vl.setContentsMargins(28, 22, 28, 28)
        inner_vl.setSpacing(18)

        # ── FILA: Autor + Módulos ─────────────────────────────────────────────
        fila1 = QHBoxLayout()
        fila1.setSpacing(14)

        # Tarjeta Autor
        card_autor = QWidget()
        card_autor.setStyleSheet(
            'background:white;border:1px solid #E0E0E0;'
            'border-radius:10px;border-top:4px solid #0D47A1;')
        ca_vl = QVBoxLayout(card_autor)
        ca_vl.setContentsMargins(18, 16, 18, 16)
        ca_vl.setSpacing(8)

        lbl_sec_autor = QLabel('DESARROLLADOR')
        lbl_sec_autor.setStyleSheet(
            'font-size:9px;font-weight:bold;color:#0D47A1;'
            'letter-spacing:1.5px;background:transparent;border:none;')
        ca_vl.addWidget(lbl_sec_autor)

        lbl_nombre_a = QLabel('Lenin E. Julca')
        lbl_nombre_a.setStyleSheet(
            'font-size:18px;font-weight:bold;color:#1A237E;'
            'background:transparent;border:none;')
        ca_vl.addWidget(lbl_nombre_a)

        lbl_cargo = QLabel('Ingeniero Forestal  |  Especialista GIS')
        lbl_cargo.setStyleSheet(
            'font-size:10px;color:#546E7A;background:transparent;border:none;')
        ca_vl.addWidget(lbl_cargo)

        sep_a = QFrame(); sep_a.setFrameShape(QFrame.HLine)
        sep_a.setStyleSheet('color:#E3F2FD;background:#E3F2FD;border:none;max-height:1px;')
        ca_vl.addWidget(sep_a)

        for icono_txt, dato, copiable in [
            ('✉  Correo:',   'ljulcao_epg19@unc.edu.pe', True),
            ('📞  Teléfono:', '+51 976 742 241',           True),
        ]:
            fila_d = QHBoxLayout()
            fila_d.setSpacing(6)
            l_ic = QLabel(icono_txt)
            l_ic.setStyleSheet(
                'font-size:10px;font-weight:bold;color:#0D47A1;'
                'background:transparent;border:none;min-width:70px;')
            l_val = QLabel(dato)
            l_val.setStyleSheet(
                'font-size:10px;color:#37474F;background:transparent;border:none;')
            if copiable:
                l_val.setTextInteractionFlags(Qt.TextSelectableByMouse)
                l_val.setCursor(Qt.IBeamCursor)
            fila_d.addWidget(l_ic)
            fila_d.addWidget(l_val)
            fila_d.addStretch()
            ca_vl.addLayout(fila_d)

        ca_vl.addStretch()
        fila1.addWidget(card_autor, 2)

        # Tarjeta Módulos
        card_mods = QWidget()
        card_mods.setStyleSheet(
            'background:white;border:1px solid #E0E0E0;'
            'border-radius:10px;border-top:4px solid #1B5E20;')
        cm_vl = QVBoxLayout(card_mods)
        cm_vl.setContentsMargins(18, 16, 18, 16)
        cm_vl.setSpacing(6)

        lbl_sec_mod = QLabel('MÓDULOS DE ANÁLISIS')
        lbl_sec_mod.setStyleSheet(
            'font-size:9px;font-weight:bold;color:#1B5E20;'
            'letter-spacing:1.5px;background:transparent;border:none;')
        cm_vl.addWidget(lbl_sec_mod)

        modulos_lista = [
            ('01', 'Topografía',          'DEM · Pendiente · TWI'),
            ('02', 'Vegetación',          'NDVI · EVI · SAVI · NDWI · NBR'),
            ('03', 'Cobertura del suelo', 'Dynamic World (9 clases)'),
            ('04', 'Precipitación',       'CHIRPS v2.0 — serie mensual'),
            ('05', 'Temperatura',         'ERA5-Land — serie mensual'),
            ('06', 'Suelos',              'pH · Carbono · Textura USDA'),
            ('07', 'Erosión RUSLE',       'Índice y nivel de riesgo'),
            ('08', 'Evapotranspiración',  'MOD16 — ET real 8 días'),
        ]
        grid_mods = QGridLayout()
        grid_mods.setSpacing(4)
        grid_mods.setVerticalSpacing(3)
        for i, (num, nom, det) in enumerate(modulos_lista):
            row = i // 2; col = (i % 2) * 2
            lbl_num = QLabel(num)
            lbl_num.setFixedSize(22, 22)
            lbl_num.setAlignment(Qt.AlignCenter)
            lbl_num.setStyleSheet(
                'font-size:9px;font-weight:bold;color:white;'
                'background:#2E7D32;border-radius:11px;border:none;')
            lbl_mod = QLabel(f'<b style="font-size:10px;color:#212121;">{nom}</b>'
                             f'<br><span style="font-size:9px;color:#757575;">{det}</span>')
            lbl_mod.setTextFormat(Qt.RichText)
            lbl_mod.setStyleSheet('background:transparent;border:none;')
            grid_mods.addWidget(lbl_num, row, col)
            grid_mods.addWidget(lbl_mod, row, col + 1)
        cm_vl.addLayout(grid_mods)
        cm_vl.addStretch()
        fila1.addWidget(card_mods, 3)
        inner_vl.addLayout(fila1)

        # ── FILA: Descripción ──────────────────────────────────────────────────
        card_desc = QWidget()
        card_desc.setStyleSheet(
            'background:white;border:1px solid #E0E0E0;border-radius:10px;')
        cd_vl = QVBoxLayout(card_desc)
        cd_vl.setContentsMargins(18, 14, 18, 14)
        lbl_about = QLabel(
            'GeoDiagnostic conecta QGIS con <b>Google Earth Engine</b> para generar '
            'diagnósticos ambientales de línea base de forma automatizada. Define el '
            'área de interés dibujando un polígono o cargando un shapefile, selecciona '
            'los módulos a analizar y el plugin calcula topografía, vegetación, cobertura, '
            'clima, suelos y riesgo de erosión sobre la nube, descargando los rasters '
            'resultantes y generando un reporte PDF profesional listo para usar en '
            'expedientes técnicos, tesis y proyectos de reforestación.')
        lbl_about.setWordWrap(True)
        lbl_about.setTextFormat(Qt.RichText)
        lbl_about.setStyleSheet(
            'font-size:11px;color:#37474F;line-height:1.7;'
            'background:transparent;border:none;')
        cd_vl.addWidget(lbl_about)
        inner_vl.addWidget(card_desc)

        # ── FILA: Donación ────────────────────────────────────────────────────
        card_don = QWidget()
        card_don.setStyleSheet(
            'background:qlineargradient(x1:0,y1:0,x2:1,y2:0,'
            'stop:0 #E8F5E9, stop:1 #F1F8E9);'
            'border:1px solid #A5D6A7;border-radius:10px;'
            'border-left:5px solid #2E7D32;')
        don_hl = QHBoxLayout(card_don)
        don_hl.setContentsMargins(20, 16, 20, 16)
        don_hl.setSpacing(20)

        don_vl = QVBoxLayout()
        don_vl.setSpacing(5)
        lbl_don_titulo = QLabel('¿Te fue útil GeoDiagnostic?')
        lbl_don_titulo.setStyleSheet(
            'font-size:14px;font-weight:bold;color:#1B5E20;'
            'background:transparent;border:none;')
        don_vl.addWidget(lbl_don_titulo)
        lbl_don_texto = QLabel(
            'Es una herramienta gratuita y de código abierto. Si la usaste en tu '
            'proyecto, tesis o trabajo profesional, considera apoyar su desarrollo.')
        lbl_don_texto.setWordWrap(True)
        lbl_don_texto.setStyleSheet(
            'font-size:10px;color:#37474F;background:transparent;border:none;')
        don_vl.addWidget(lbl_don_texto)
        don_hl.addLayout(don_vl, 3)

        # Caja Yape destacada
        yape_box = QWidget()
        yape_box.setFixedWidth(220)
        yape_box.setStyleSheet(
            'background:white;border:2px solid #66BB6A;'
            'border-radius:10px;')
        yape_vl2 = QVBoxLayout(yape_box)
        yape_vl2.setContentsMargins(14, 12, 14, 12)
        yape_vl2.setSpacing(4)
        lbl_yape_ic = QLabel('Yape  /  Plin')
        lbl_yape_ic.setAlignment(Qt.AlignCenter)
        lbl_yape_ic.setStyleSheet(
            'font-size:10px;font-weight:bold;color:#2E7D32;'
            'background:#E8F5E9;border-radius:5px;padding:3px;border:none;')
        yape_vl2.addWidget(lbl_yape_ic)
        lbl_yape_num2 = QLabel('+51 976 742 241')
        lbl_yape_num2.setAlignment(Qt.AlignCenter)
        lbl_yape_num2.setStyleSheet(
            'font-size:16px;font-weight:bold;color:#1B5E20;'
            'letter-spacing:1px;background:transparent;border:none;')
        lbl_yape_num2.setTextInteractionFlags(Qt.TextSelectableByMouse)
        lbl_yape_num2.setCursor(Qt.IBeamCursor)
        yape_vl2.addWidget(lbl_yape_num2)
        lbl_yape_nom = QLabel('Lenin E. Julca')
        lbl_yape_nom.setAlignment(Qt.AlignCenter)
        lbl_yape_nom.setStyleSheet(
            'font-size:10px;color:#546E7A;background:transparent;border:none;')
        yape_vl2.addWidget(lbl_yape_nom)
        lbl_yape_nota2 = QLabel('Cualquier monto — gracias.')
        lbl_yape_nota2.setAlignment(Qt.AlignCenter)
        lbl_yape_nota2.setStyleSheet(
            'font-size:9px;color:#9E9E9E;font-style:italic;'
            'background:transparent;border:none;')
        yape_vl2.addWidget(lbl_yape_nota2)
        don_hl.addWidget(yape_box, 0)
        inner_vl.addWidget(card_don)

        # ── FILA: Fuentes + Botones ───────────────────────────────────────────
        fila3 = QHBoxLayout()
        fila3.setSpacing(14)

        # Tarjeta fuentes
        card_fuentes = QWidget()
        card_fuentes.setStyleSheet(
            'background:white;border:1px solid #E0E0E0;border-radius:10px;')
        cf_vl = QVBoxLayout(card_fuentes)
        cf_vl.setContentsMargins(18, 14, 18, 14)
        cf_vl.setSpacing(4)
        lbl_sec_f = QLabel('FUENTES DE DATOS')
        lbl_sec_f.setStyleSheet(
            'font-size:9px;font-weight:bold;color:#37474F;'
            'letter-spacing:1.5px;background:transparent;border:none;')
        cf_vl.addWidget(lbl_sec_f)
        fuentes_lista = [
            ('SRTM v3',           'NASA / USGS',          'Dominio público'),
            ('Sentinel-2 SR',     'ESA / Copernicus',     'Libre uso'),
            ('CHIRPS v2.0',       'UCSB / CHG',           'Libre uso'),
            ('ERA5-Land',         'ECMWF / Copernicus',   'Libre uso'),
            ('SoilGrids 250m',    'ISRIC',                'CC-BY 4.0'),
            ('Dynamic World',     'Google / WRI',         'CC-BY 4.0'),
            ('MOD16',             'NASA / MODIS',         'Libre uso'),
            ('FAO GAUL',          'FAO',                  'No comercial'),
        ]
        grid_f = QGridLayout()
        grid_f.setSpacing(2)
        grid_f.setContentsMargins(0, 4, 0, 0)
        for i, (dataset, org, lic) in enumerate(fuentes_lista):
            lbl_ds = QLabel(f'<b>{dataset}</b>')
            lbl_ds.setTextFormat(Qt.RichText)
            lbl_ds.setStyleSheet(
                'font-size:9.5px;color:#212121;background:transparent;border:none;')
            lbl_org = QLabel(org)
            lbl_org.setStyleSheet(
                'font-size:9px;color:#546E7A;background:transparent;border:none;')
            lbl_lic = QLabel(lic)
            lbl_lic.setStyleSheet(
                'font-size:9px;color:#1B5E20;background:#E8F5E9;'
                'border-radius:4px;padding:1px 5px;border:none;')
            grid_f.addWidget(lbl_ds,  i, 0)
            grid_f.addWidget(lbl_org, i, 1)
            grid_f.addWidget(lbl_lic, i, 2)
        cf_vl.addLayout(grid_f)
        fila3.addWidget(card_fuentes, 3)

        # Tarjeta acciones
        card_acc = QWidget()
        card_acc.setStyleSheet(
            'background:white;border:1px solid #E0E0E0;border-radius:10px;')
        cacc_vl = QVBoxLayout(card_acc)
        cacc_vl.setContentsMargins(18, 14, 18, 14)
        cacc_vl.setSpacing(10)
        lbl_sec_acc = QLabel('ACCIONES')
        lbl_sec_acc.setStyleSheet(
            'font-size:9px;font-weight:bold;color:#37474F;'
            'letter-spacing:1.5px;background:transparent;border:none;')
        cacc_vl.addWidget(lbl_sec_acc)

        btn_correo = QPushButton('  Contactar por correo')
        btn_correo.setStyleSheet(estilo_boton_primario())
        btn_correo.setMinimumHeight(36)
        btn_correo.clicked.connect(
            lambda: QDesktopServices.openUrl(
                QUrl('mailto:ljulcao_epg19@unc.edu.pe'
                     '?subject=GeoDiagnostic%20v1.0.0')))
        cacc_vl.addWidget(btn_correo)

        btn_manual = QPushButton('  Abrir Manual PDF')
        btn_manual.setStyleSheet(estilo_boton_secundario())
        btn_manual.setMinimumHeight(36)
        btn_manual.clicked.connect(self._abrir_manual)
        cacc_vl.addWidget(btn_manual)

        btn_github = QPushButton('  Ver en GitHub')
        btn_github.setStyleSheet(estilo_boton_secundario())
        btn_github.setMinimumHeight(36)
        btn_github.clicked.connect(
            lambda: QDesktopServices.openUrl(
                QUrl('https://github.com/ljulcaoepg19-gif/geodiagnostic')))
        cacc_vl.addWidget(btn_github)

        cacc_vl.addStretch()

        # Tecnologías usadas
        lbl_tec = QLabel(
            '<span style="color:#9E9E9E;font-size:9px;">'
            'QGIS 3.16+ &nbsp;·&nbsp; Python 3 &nbsp;·&nbsp; PyQt5 &nbsp;·&nbsp; '
            'Google Earth Engine API &nbsp;·&nbsp; reportlab &nbsp;·&nbsp; GDAL'
            '</span>')
        lbl_tec.setTextFormat(Qt.RichText)
        lbl_tec.setWordWrap(True)
        lbl_tec.setStyleSheet('background:transparent;border:none;')
        cacc_vl.addWidget(lbl_tec)
        fila3.addWidget(card_acc, 2)
        inner_vl.addLayout(fila3)

        # ── PIE ───────────────────────────────────────────────────────────────
        lbl_pie = QLabel(
            '<center><span style="color:#BDBDBD;font-size:9px;">'
            'GeoDiagnostic v1.0.0 &nbsp;—&nbsp; GPL-2.0 &nbsp;—&nbsp; '
            '2024-2026 Lenin E. Julca &nbsp;—&nbsp; '
            'ljulcao_epg19@unc.edu.pe'
            '</span></center>')
        lbl_pie.setTextFormat(Qt.RichText)
        lbl_pie.setAlignment(Qt.AlignCenter)
        lbl_pie.setStyleSheet('background:transparent;border:none;')
        inner_vl.addWidget(lbl_pie)
        inner_vl.addStretch()

        vl.addWidget(inner)
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

        # Recopilar TODAS las geometrias y disolver en una sola
        geoms = [feat.geometry() for feat in capa.getFeatures()
                 if feat.geometry() and not feat.geometry().isEmpty()]
        if not geoms:
            QMessageBox.warning(self, 'Sin geometria', 'La capa no tiene geometrias validas.')
            return

        # Disolver: combinar todas las features en una geometria unificada
        geom = geoms[0]
        for g in geoms[1:]:
            geom = geom.combine(g)

        # Asegurar que el resultado sea Polygon o MultiPolygon
        # combine() puede devolver GeometryCollection — convertir si es necesario
        from qgis.core import QgsWkbTypes as _WKB
        if not _WKB.geometryType(geom.wkbType()) == _WKB.PolygonGeometry:
            # Intentar convertir a multipoligono extrayendo solo polígonos
            partes = []
            for i in range(geom.constGet().numGeometries() if hasattr(geom.constGet(), 'numGeometries') else 0):
                parte = QgsGeometry(geom.constGet().geometryN(i).clone())
                if _WKB.geometryType(parte.wkbType()) == _WKB.PolygonGeometry:
                    partes.append(parte)
            if partes:
                geom = partes[0]
                for p in partes[1:]:
                    geom = geom.combine(p)

        # Informar si habia multiples features
        n = len(geoms)
        if n > 1:
            from qgis.PyQt.QtWidgets import QMessageBox as QMB
            QMB.information(self, 'Multiples geometrias',
                f'La capa tiene {n} geometrias. '
                f'Se analizaran como una sola area unificada.')

        self._aoi_geom     = geom.asWkt()
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
            # Contar vértices de forma segura para Polygon y MultiPolygon
            try:
                from qgis.core import QgsWkbTypes as _WKB
                _wt = _WKB.geometryType(geom.wkbType())
                if _wt == _WKB.PolygonGeometry:
                    if _WKB.isMultiType(geom.wkbType()):
                        _partes = geom.asMultiPolygon()
                        n_verts = len(_partes[0][0]) if _partes else 0
                    else:
                        _anillo = geom.asPolygon()
                        n_verts = len(_anillo[0]) if _anillo else 0
                else:
                    n_verts = 0
            except Exception:
                n_verts = 0

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

            # ── Extraer coordenadas de vértices en WGS84 y UTM ───────────────
            self._vertices_lista = []
            self._vertices_zona_utm = zona_utm
            self._vertices_epsg_utm = epsg_utm
            try:
                from qgis.core import QgsWkbTypes as _WKB2
                _geom_wgs = QgsGeometry(geom_ll)  # ya en WGS84
                _geom_utm_v = QgsGeometry(_geom_wgs)
                _xf_v = QgsCoordinateTransform(
                    crs_wgs84, crs_utm, QgsProject.instance())
                _geom_utm_v.transform(_xf_v)

                _wt2 = _WKB2.geometryType(geom.wkbType())
                if _wt2 == _WKB2.PolygonGeometry:
                    if _WKB2.isMultiType(geom.wkbType()):
                        _rings_wgs = _geom_wgs.asMultiPolygon()
                        _rings_utm = _geom_utm_v.asMultiPolygon()
                        pts_wgs = _rings_wgs[0][0] if _rings_wgs else []
                        pts_utm = _rings_utm[0][0] if _rings_utm else []
                    else:
                        _rings_wgs = _geom_wgs.asPolygon()
                        _rings_utm = _geom_utm_v.asPolygon()
                        pts_wgs = _rings_wgs[0] if _rings_wgs else []
                        pts_utm = _rings_utm[0] if _rings_utm else []

                    # Omitir el punto de cierre (igual al primero)
                    if (len(pts_wgs) > 1 and
                            abs(pts_wgs[0].x() - pts_wgs[-1].x()) < 1e-9 and
                            abs(pts_wgs[0].y() - pts_wgs[-1].y()) < 1e-9):
                        pts_wgs = pts_wgs[:-1]
                        pts_utm = pts_utm[:-1] if pts_utm else pts_utm

                    for i, (pw, pu) in enumerate(zip(pts_wgs, pts_utm), 1):
                        self._vertices_lista.append({
                            'n':    i,
                            'lat':  round(pw.y(), 6),
                            'lon':  round(pw.x(), 6),
                            'este': round(pu.x(), 1),
                            'norte': round(pu.y(), 1),
                            'zona': zona_utm,
                        })
            except Exception:
                self._vertices_lista = []
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
            self._btn_exportar_vertices.setEnabled(False)
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
        self._btn_exportar_vertices.setEnabled(
            bool(getattr(self, '_vertices_lista', [])))

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
        self._nombre_proy_actual    = nombre_proy
        self._btn_ejecutar.setEnabled(False)
        self._btn_cancelar.setEnabled(True)
        self._progreso_global.setValue(0)
        self._limpiar_tabla()

        # Guardar AOI como GPKG en WGS84 (EPSG:4326) para recorte GDAL posterior.
        # IMPORTANTE: siempre WGS84 porque GEE descarga los rasters en 4326.
        # Usar el mismo CRS en máscara y raster evita desalineación de bordes.
        self._aoi_gpkg_path = None
        try:
            import os as _os
            from qgis.core import (QgsVectorFileWriter, QgsFields,
                                   QgsField as QgsFieldAoi, QgsFeature as QgsFeatureAoi,
                                   QgsWkbTypes as QgsWkbTypesAoi,
                                   QgsCoordinateReferenceSystem as _CRS,
                                   QgsCoordinateTransform as _XF)
            from qgis.PyQt.QtCore import QVariant as QVariantAoi
            _carpeta_proy = _os.path.join(carpeta, nombre_proy)
            _os.makedirs(_carpeta_proy, exist_ok=True)
            _ruta_gpkg  = _os.path.join(_carpeta_proy, f'{nombre_proy}_AOI.gpkg')
            _geom_aoi   = QgsGeometry.fromWkt(self._aoi_geom)
            _crs_orig   = _CRS(f'EPSG:{self._aoi_crs_epsg}')
            _crs_wgs84  = _CRS('EPSG:4326')
            # Reproyectar a WGS84 si el SHP está en otro CRS
            if _crs_orig != _crs_wgs84:
                _geom_aoi.transform(_XF(_crs_orig, _crs_wgs84,
                                        QgsProject.instance()))
            _campos = QgsFields()
            _campos.append(QgsFieldAoi('id', QVariantAoi.Int))
            _opts            = QgsVectorFileWriter.SaveVectorOptions()
            _opts.driverName    = 'GPKG'
            _opts.fileEncoding  = 'UTF-8'
            _writer = QgsVectorFileWriter.create(
                _ruta_gpkg, _campos,
                QgsWkbTypesAoi.Polygon, _crs_wgs84,
                QgsCoordinateTransform(), _opts)
            _feat = QgsFeatureAoi()
            _feat.setGeometry(_geom_aoi)
            _feat.setAttributes([1])
            _writer.addFeature(_feat)
            del _writer
            if _os.path.exists(_ruta_gpkg):
                self._aoi_gpkg_path = _ruta_gpkg
        except Exception:
            pass

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
    # DESCARGA Y CARGA DE RASTERS — todas las capas
    # ══════════════════════════════════════════════════════════════════════════
    def _descargar_rasters(self, modulo, urls_str):
        try:
            import os
            NP           = self._nombre_proy_actual
            carpeta_proy = os.path.join(self._carpeta_salida_actual, NP)
            os.makedirs(carpeta_proy, exist_ok=True)

            # ── Nombres en orden EXACTO igual a las URLs de gee_worker.py ──
            nombres = {
                'topografia':        [f'{NP}_DEM.tif',
                                      f'{NP}_Pendiente.tif',
                                      f'{NP}_TWI.tif'],
                'vegetacion':        [f'{NP}_NDVI.tif',
                                      f'{NP}_EVI.tif',
                                      f'{NP}_SAVI.tif',
                                      f'{NP}_NDWI.tif',
                                      f'{NP}_NDMI.tif',
                                      f'{NP}_NBR.tif',
                                      f'{NP}_BSI.tif'],
                'cobertura':         [f'{NP}_Cobertura.tif'],
                'clima':             [f'{NP}_Precipitacion.tif'],
                'temperatura':       [f'{NP}_Temperatura.tif'],
                'suelos':            [f'{NP}_pH.tif',
                                      f'{NP}_Arcilla.tif',
                                      f'{NP}_Carbono.tif'],
                'erosion':           [f'{NP}_Erosion_RUSLE.tif'],
                'evapotranspiracion':[f'{NP}_ET.tif'],
            }

            # ── Subgrupos por módulo para organizar el panel de capas ──────
            SUBGRUPOS = {
                'topografia':        'Topografia (SRTM)',
                'vegetacion':        'Vegetacion (Sentinel-2)',
                'cobertura':         'Cobertura del Suelo (DW)',
                'clima':             'Precipitacion (CHIRPS)',
                'temperatura':       'Temperatura (ERA5-Land)',
                'suelos':            'Suelos (SoilGrids)',
                'erosion':           'Erosion RUSLE',
                'evapotranspiracion':'Evapotranspiracion (MOD16)',
            }

            urls = [u for u in urls_str.split('|||') if u.strip()]
            noms = nombres.get(modulo, [f'{NP}_{modulo}.tif'])

            # ── Obtener/crear grupo raíz y subgrupo del módulo ────────────
            root         = QgsProject.instance().layerTreeRoot()
            grp_nombre   = f'GeoDiagnostic — {NP}'
            grp_root     = root.findGroup(grp_nombre)
            if not grp_root:
                grp_root = root.insertGroup(0, grp_nombre)

            sub_nombre   = SUBGRUPOS.get(modulo, modulo.capitalize())
            grp_sub      = grp_root.findGroup(sub_nombre)
            if not grp_sub:
                grp_sub  = grp_root.insertGroup(0, sub_nombre)

            # ── Ruta del AOI recortado (gpkg guardado al ejecutar) ─────────
            ruta_aoi_gpkg = getattr(self, '_aoi_gpkg_path', None)

            for url, nom in zip(urls, noms):
                if not url.strip():
                    continue
                ruta_raw  = os.path.join(carpeta_proy, nom)
                ruta_clip = os.path.join(carpeta_proy,
                                         nom.replace('.tif', '_clip.tif'))
                nombre_capa = nom.replace('.tif', '')

                # 1. Descargar el .tif desde GEE
                try:
                    urllib.request.urlretrieve(url, ruta_raw)
                except Exception:
                    continue  # si falla la descarga, siguiente capa

                # 2. Recortar al polígono exacto del AOI con GDAL
                # El GPKG de máscara siempre está en WGS84 (igual que los rasters GEE).
                # ALL_TOUCHED=True incluye píxeles de borde → recorte exacto al perímetro.
                ruta_final = ruta_raw
                _clip_ok   = False
                if ruta_aoi_gpkg and os.path.exists(ruta_aoi_gpkg):
                    try:
                        import processing
                        resultado = processing.run(
                            'gdal:cliprasterbymasklayer',
                            {
                                'INPUT':           ruta_raw,
                                'MASK':            ruta_aoi_gpkg,
                                'SOURCE_CRS':      'EPSG:4326',
                                'TARGET_CRS':      'EPSG:4326',
                                'NODATA':          -9999,
                                'ALPHA_BAND':      False,
                                'CROP_TO_CUTLINE': True,
                                'ALL_TOUCHED':     True,
                                'KEEP_RESOLUTION': True,
                                'OPTIONS':         '',
                                'DATA_TYPE':       0,
                                'OUTPUT':          ruta_clip,
                            }
                        )
                        if os.path.exists(ruta_clip):
                            ruta_final = ruta_clip
                            _clip_ok   = True
                            try:
                                os.remove(ruta_raw)
                            except Exception:
                                pass
                    except Exception as _e_clip:
                        ruta_final = ruta_raw  # fallback sin recorte
                        # Advertencia visible en la tabla de resultados
                        self._agregar_fila_tabla(
                            modulo.upper(),
                            f'⚠ {nombre_capa}: recorte falló — capa cargada sin recortar',
                            str(_e_clip)[:120]
                        )

                # 3. Cargar capa raster en QGIS
                capa = QgsRasterLayer(ruta_final, nombre_capa)
                if not capa.isValid():
                    continue
                QgsProject.instance().addMapLayer(capa, False)
                grp_sub.insertLayer(0, capa)

                # 4. Paleta automática de colores por tipo de capa
                self._aplicar_paleta(capa, nom)

            # 5. Cobertura: además del raster, generar SHP con nombres de clase
            if modulo == 'cobertura':
                self._vectorizar_cobertura(carpeta_proy, NP, grp_sub)

        except Exception:
            import traceback
            traceback.print_exc()

    def _aplicar_paleta(self, capa, nombre_archivo):
        """Aplica rampa de color automática según el tipo de capa."""
        try:
            from qgis.core import (QgsColorRampShader, QgsRasterShader,
                                   QgsSingleBandPseudoColorRenderer,
                                   QgsRasterBandStats)

            # Definir rampa según nombre de archivo
            RAMPAS = {
                '_DEM':          ('RdYlGn',   False),
                '_Pendiente':    ('YlOrRd',   False),
                '_TWI':          ('Blues',    False),
                '_NDVI':         ('RdYlGn',   False),
                '_EVI':          ('RdYlGn',   False),
                '_SAVI':         ('RdYlGn',   False),
                '_NDWI':         ('RdYlBu',   False),
                '_NDMI':         ('RdYlBu',   False),
                '_NBR':          ('RdYlGn',   False),
                '_BSI':          ('YlOrRd',   True),
                '_Precipitacion':('Blues',    False),
                '_Temperatura':  ('RdYlBu',   True),
                '_pH':           ('BrBG',     False),
                '_Arcilla':      ('YlOrBr',   False),
                '_Carbono':      ('YlGn',     False),
                '_Erosion_RUSLE':('RdYlGn',   True),
                '_ET':           ('Blues',    False),
            }

            # Cobertura DW — paleta categórica especial
            if '_Cobertura' in nombre_archivo:
                self._aplicar_paleta_cobertura_dw(capa)
                return

            rampa_nombre = None
            invertir     = False
            for key, (rmp, inv) in RAMPAS.items():
                if key in nombre_archivo:
                    rampa_nombre = rmp
                    invertir     = inv
                    break
            if not rampa_nombre:
                return

            from qgis.core import QgsStyle
            style  = QgsStyle.defaultStyle()
            ramp   = style.colorRamp(rampa_nombre)
            if not ramp:
                return
            if invertir:
                ramp.invert()

            stats = capa.dataProvider().bandStatistics(
                1, QgsRasterBandStats.All, capa.extent(), 0)
            mn, mx = stats.minimumValue, stats.maximumValue
            if mn == mx:
                return

            shader_func = QgsColorRampShader()
            shader_func.setColorRampType(QgsColorRampShader.Interpolated)
            n_steps = 10
            items   = []
            for i in range(n_steps + 1):
                t     = i / n_steps
                val   = mn + t * (mx - mn)
                color = ramp.color(t)
                items.append(QgsColorRampShader.ColorRampItem(val, color))
            shader_func.setColorRampItemList(items)

            shader = QgsRasterShader()
            shader.setRasterShaderFunction(shader_func)

            renderer = QgsSingleBandPseudoColorRenderer(
                capa.dataProvider(), 1, shader)
            capa.setRenderer(renderer)
            capa.triggerRepaint()
        except Exception:
            pass

    def _aplicar_paleta_cobertura_dw(self, capa):
        """Paleta categórica oficial Dynamic World — colores por clase."""
        try:
            from qgis.core import (QgsPalettedRasterRenderer,
                                   QgsColorRampShader)
            CLASES_DW = [
                (0, '#419BDF', 'Agua'),
                (1, '#397D49', 'Árboles'),
                (2, '#88B053', 'Césped / Pasto'),
                (3, '#7A87C6', 'Veg. inundada'),
                (4, '#E49635', 'Cultivos'),
                (5, '#DFC35A', 'Arbustos'),
                (6, '#C4281B', 'Construido'),
                (7, '#A59B8F', 'Suelo desnudo'),
                (8, '#B39FE1', 'Nieve / Hielo'),
            ]
            clases = [
                QgsPalettedRasterRenderer.Class(
                    val, QColor(hex_c), nombre)
                for val, hex_c, nombre in CLASES_DW
            ]
            renderer = QgsPalettedRasterRenderer(
                capa.dataProvider(), 1, clases)
            capa.setRenderer(renderer)
            capa.triggerRepaint()
        except Exception:
            pass

    def _vectorizar_cobertura(self, carpeta_proy, NP, grupo_qgis):
        """Vectoriza el raster de cobertura a SHP con nombres de clase DW."""
        try:
            import os, processing
            from qgis.core import QgsVectorLayer, QgsProject, QgsField
            from qgis.PyQt.QtCore import QVariant

            ruta_raster = os.path.join(carpeta_proy, f'{NP}_Cobertura_clip.tif')
            if not os.path.exists(ruta_raster):
                ruta_raster = os.path.join(carpeta_proy, f'{NP}_Cobertura.tif')
            if not os.path.exists(ruta_raster):
                return

            ruta_shp = os.path.join(carpeta_proy, f'{NP}_Cobertura_LULC.gpkg')

            # Polygonize — convierte raster de clases a polígonos
            processing.run('gdal:polygonize', {
                'INPUT':   ruta_raster,
                'BAND':    1,
                'FIELD':   'clase_id',
                'EIGHT_CONNECTEDNESS': False,
                'OUTPUT':  ruta_shp,
            })

            if not os.path.exists(ruta_shp):
                return

            # Cargar la capa vectorial
            capa_v = QgsVectorLayer(ruta_shp, f'{NP}_Cobertura_LULC', 'ogr')
            if not capa_v.isValid():
                return

            # Agregar campo "Cobertura" con el nombre textual de la clase
            NOMBRES_DW = {
                0: 'Agua',         1: 'Árboles',
                2: 'Césped/Pasto', 3: 'Veg. inundada',
                4: 'Cultivos',     5: 'Arbustos',
                6: 'Construido',   7: 'Suelo desnudo',
                8: 'Nieve/Hielo',
            }
            COLORES_DW = {
                0: '#419BDF', 1: '#397D49', 2: '#88B053',
                3: '#7A87C6', 4: '#E49635', 5: '#DFC35A',
                6: '#C4281B', 7: '#A59B8F', 8: '#B39FE1',
            }

            capa_v.startEditing()
            capa_v.addAttribute(QgsField('Cobertura', QVariant.String))
            capa_v.updateFields()

            idx_id  = capa_v.fields().indexOf('clase_id')
            idx_nom = capa_v.fields().indexOf('Cobertura')
            for feat in capa_v.getFeatures():
                cid  = int(feat[idx_id]) if feat[idx_id] is not None else -1
                nom  = NOMBRES_DW.get(cid, f'Clase_{cid}')
                capa_v.changeAttributeValue(feat.id(), idx_nom, nom)
            capa_v.commitChanges()

            # Simbología categórica por clase
            from qgis.core import (QgsCategorizedSymbolRenderer,
                                   QgsRendererCategory, QgsFillSymbol)
            categorias = []
            for cid, nombre in NOMBRES_DW.items():
                simbolo = QgsFillSymbol.createSimple({
                    'color':         COLORES_DW.get(cid, '#9E9E9E'),
                    'outline_color': '#FFFFFF',
                    'outline_width': '0.1',
                })
                categorias.append(
                    QgsRendererCategory(cid, simbolo, nombre))
            renderer_v = QgsCategorizedSymbolRenderer('clase_id', categorias)
            capa_v.setRenderer(renderer_v)

            QgsProject.instance().addMapLayer(capa_v, False)
            grupo_qgis.insertLayer(0, capa_v)

        except Exception:
            import traceback
            traceback.print_exc()

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
            f'  GeoDiagnostic v1.0.0',
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

    def _exportar_vertices_csv(self):
        """Exporta las coordenadas de todos los vértices del AOI a un archivo CSV."""
        verts = getattr(self, '_vertices_lista', [])
        if not verts:
            QMessageBox.warning(self, 'Sin vértices',
                'No hay vértices disponibles. Define primero el área de interés.')
            return
        nombre_proy = self._inp_nombre_proy.text().strip() or 'AOI'
        ruta, _ = QFileDialog.getSaveFileName(
            self, 'Exportar vértices',
            f'{nombre_proy}_vertices.csv', 'CSV (*.csv)')
        if not ruta:
            return
        zona = getattr(self, '_vertices_zona_utm', 'UTM')
        try:
            with open(ruta, 'w', encoding='utf-8') as f:
                f.write(f'# GeoDiagnostic v1.0.0 — Coordenadas de vertices del AOI\n')
                f.write(f'# Proyecto: {nombre_proy}\n')
                f.write(f'# Fecha: {datetime.now().strftime("%d/%m/%Y %H:%M")}\n')
                f.write(f'# Sistema geografico: WGS84 (EPSG:4326)\n')
                f.write(f'# Sistema plano: UTM Zona {zona} (WGS84)\n')
                f.write('#\n')
                f.write('N,Latitud_WGS84,Longitud_WGS84,'
                        f'Este_UTM_{zona}_m,Norte_UTM_{zona}_m\n')
                for v in verts:
                    f.write(f"{v['n']},{v['lat']:.6f},{v['lon']:.6f},"
                            f"{v['este']:.1f},{v['norte']:.1f}\n")
            QMessageBox.information(self, 'Exportado',
                f'Vértices exportados ({len(verts)} puntos):\n{ruta}')
        except Exception as e:
            QMessageBox.critical(self, 'Error', f'No se pudo guardar el CSV:\n{str(e)}')

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
            'plugin': 'GeoDiagnostic v1.0.0',
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
                'Ejecuta el diagnóstico primero para generar el reporte PDF.')
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
            area_ha    = getattr(self, '_area_ha_actual', 0)
            modo_drive = area_ha > 8000
            ficha      = getattr(self, '_datos_ficha', {})

            # Capturar imagen del canvas QGIS con el polígono del AOI
            imagen_aoi = None
            try:
                import os as _os
                ruta_img = _os.join(_os.path.dirname(ruta), f'{nombre_proy}_AOI_preview.png')
                self.canvas.saveAsImage(ruta_img)
                if _os.path.exists(ruta_img):
                    imagen_aoi = ruta_img
            except Exception:
                pass

            generar_reporte(ruta, nombre_proy, self._resultados,
                            ficha, area_ha, modo_drive, imagen_aoi,
                            vertices=getattr(self, '_vertices_lista', []),
                            zona_utm=getattr(self, '_vertices_zona_utm', ''))
            QMessageBox.information(self, 'Reporte generado',
                f'El reporte PDF fue guardado correctamente en:\n{ruta}')
            QDesktopServices.openUrl(QUrl.fromLocalFile(ruta))
        except Exception as e:
            import traceback
            QMessageBox.critical(self, 'Error al generar PDF',
                f'No se pudo generar el reporte:\n\n{str(e)}\n\n'
                'Verifica que reportlab esté instalado:\n'
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
