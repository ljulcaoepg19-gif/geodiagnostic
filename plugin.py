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
