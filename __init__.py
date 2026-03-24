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
