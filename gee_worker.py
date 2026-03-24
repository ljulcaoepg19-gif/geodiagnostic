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
        # Aplicar máscara exacta del AOI para que GEE envíe solo píxeles
        # dentro del polígono (NoData fuera). Evita descargar el bbox completo.
        img = img.updateMask(ee.Image.constant(1).clip(aoi).mask())
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

    def _periodo(self, col):
        """Obtiene fecha inicio y fin reales de una coleccion."""
        import ee
        try:
            fechas = col.aggregate_array('system:time_start').getInfo()
            if fechas:
                from datetime import datetime
                f_ini = datetime.utcfromtimestamp(min(fechas)/1000).strftime('%d/%m/%Y')
                f_fin = datetime.utcfromtimestamp(max(fechas)/1000).strftime('%d/%m/%Y')
                n     = len(fechas)
                return f'{f_ini} — {f_fin}  ({n} imágenes)'
        except Exception:
            pass
        return f'{self.fecha_ini} — {self.fecha_fin}'

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

            # Detectar tipo con wkbType — seguro para Polygon Y MultiPolygon
            from qgis.core import QgsWkbTypes
            _wt = QgsWkbTypes.geometryType(gq.wkbType())

            if _wt == QgsWkbTypes.PolygonGeometry:
                if QgsWkbTypes.isMultiType(gq.wkbType()):
                    _partes = gq.asMultiPolygon()
                    if not _partes:
                        raise ValueError('MultiPolygon sin partes.')
                    _coords = [
                        [[[p.x(), p.y()] for p in r] for r in pol]
                        for pol in _partes
                    ]
                    aoi = ee.Geometry.MultiPolygon(_coords)
                else:
                    _rings = gq.asPolygon()
                    if not _rings:
                        raise ValueError('Polygon sin anillos.')
                    aoi = ee.Geometry.Polygon(
                        [[p.x(), p.y()] for p in _rings[0]])
            else:
                raise ValueError(
                    'Solo se admiten geometrias Polygon o MultiPolygon. '
                    f'Tipo detectado: {QgsWkbTypes.displayString(gq.wkbType())}')

            RG   = {}
            tot  = len(self.modulos)
            paso = 0
            NM   = self.nombre_proyecto

            # ── TOPOGRAFIA ────────────────────────────────────────────────────
            if 'topografia' in self.modulos and not self._cancelar:
                try:
                    self.progreso.emit('Calculando topografía (SRTM + TWI)...', int(paso/tot*85))
                    sc  = self._escala(30)
                    dem = ee.Image('USGS/SRTMGL1_003').clip(aoi)
                    pen = ee.Terrain.slope(dem)
                    prad = pen.multiply(math.pi / 180)
                    try:
                        fa   = ee.Image('WWF/HydroSHEDS/15ACC').clip(aoi)
                        twi  = fa.add(1).log().subtract(prad.tan().max(ee.Image(0.001)).log()).rename('TWI')
                        st_twi = twi.reduceRegion(
                            ee.Reducer.mean().combine(ee.Reducer.stdDev(), sharedInputs=True)
                            .combine(ee.Reducer.count(), sharedInputs=True),
                            geometry=aoi, scale=sc, maxPixels=1e13, bestEffort=True).getInfo()
                        twi_v   = round(st_twi.get('TWI_mean', 0) or 0, 3)
                        url_twi = self._url(twi, aoi, sc, f'{NM}_TWI')
                    except Exception:
                        twi_v, url_twi = 0, ''
                    KW = dict(geometry=aoi, scale=sc, maxPixels=1e13, bestEffort=True)
                    sd = dem.rename('e').reduceRegion(
                        ee.Reducer.mean()
                        .combine(ee.Reducer.minMax(), sharedInputs=True)
                        .combine(ee.Reducer.stdDev(), sharedInputs=True)
                        .combine(ee.Reducer.count(), sharedInputs=True)
                        .combine(ee.Reducer.percentile([25, 75]), sharedInputs=True), **KW).getInfo()
                    sp2 = pen.rename('p').reduceRegion(
                        ee.Reducer.mean()
                        .combine(ee.Reducer.minMax(), sharedInputs=True)
                        .combine(ee.Reducer.stdDev(), sharedInputs=True), **KW).getInfo()
                    res = {
                        'Elevación media (msnm)':    round(sd.get('e_mean',   0) or 0, 1),
                        'Elevación mínima (msnm)':   round(sd.get('e_min',    0) or 0, 1),
                        'Elevación máxima (msnm)':   round(sd.get('e_max',    0) or 0, 1),
                        'Desv. estándar elev. (m)':  round(sd.get('e_stdDev', 0) or 0, 2),
                        'N° píxeles analizados':     int(sd.get('e_count',   0) or 0),
                        'P25 elevación (msnm)':      round(sd.get('e_p25',    0) or 0, 1),
                        'P75 elevación (msnm)':      round(sd.get('e_p75',    0) or 0, 1),
                        'Pendiente media (°)':        round(sp2.get('p_mean',  0) or 0, 2),
                        'Pendiente máxima (°)':       round(sp2.get('p_max',   0) or 0, 2),
                        'Pendiente stdDev (°)':       round(sp2.get('p_stdDev',0) or 0, 2),
                        'TWI medio':                  twi_v,
                        '_periodo': 'Estático — SRTM misión 2000',
                        '_resolucion': '30 m',
                        '_fuente': 'USGS/SRTMGL1_003',
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

            # ── VEGETACIÓN ────────────────────────────────────────────────────
            if 'vegetacion' in self.modulos and not self._cancelar:
                try:
                    self.progreso.emit('Calculando índices espectrales (Sentinel-2)...', int(paso/tot*85))
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
                    col_s2 = (ee.ImageCollection('COPERNICUS/S2_SR_HARMONIZED')
                              .filterBounds(aoi).filterDate(self.fecha_ini, self.fecha_fin)
                              .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', 20)))
                    periodo_s2 = self._periodo(col_s2)
                    s2 = col_s2.map(add_indices).median().clip(aoi)
                    indices = ['NDVI','EVI','SAVI','NDWI','NDMI','NBR','BSI']
                    st = s2.select(indices).reduceRegion(
                        ee.Reducer.mean()
                        .combine(ee.Reducer.minMax(), sharedInputs=True)
                        .combine(ee.Reducer.stdDev(), sharedInputs=True)
                        .combine(ee.Reducer.percentile([10, 25, 75, 90]), sharedInputs=True)
                        .combine(ee.Reducer.count(), sharedInputs=True),
                        geometry=aoi, scale=sc, maxPixels=1e13, bestEffort=True).getInfo()
                    res = {'_periodo': periodo_s2, '_resolucion': '10 m',
                           '_fuente': 'COPERNICUS/S2_SR_HARMONIZED'}
                    for idx in indices:
                        res[f'{idx} medio']  = round(st.get(f'{idx}_mean',   0) or 0, 4)
                        res[f'{idx} min']    = round(st.get(f'{idx}_min',    0) or 0, 4)
                        res[f'{idx} max']    = round(st.get(f'{idx}_max',    0) or 0, 4)
                        res[f'{idx} stdDev'] = round(st.get(f'{idx}_stdDev', 0) or 0, 4)
                        res[f'{idx} p10']    = round(st.get(f'{idx}_p10',    0) or 0, 4)
                        res[f'{idx} p25']    = round(st.get(f'{idx}_p25',    0) or 0, 4)
                        res[f'{idx} p75']    = round(st.get(f'{idx}_p75',    0) or 0, 4)
                        res[f'{idx} p90']    = round(st.get(f'{idx}_p90',    0) or 0, 4)
                        res[f'{idx} count']  = int(st.get(f'{idx}_count',    0) or 0)
                    urls = '|||'.join([
                        self._url(s2.select('NDVI'), aoi, sc, f'{NM}_NDVI'),
                        self._url(s2.select('EVI'),  aoi, sc, f'{NM}_EVI'),
                        self._url(s2.select('SAVI'), aoi, sc, f'{NM}_SAVI'),
                        self._url(s2.select('NDWI'), aoi, sc, f'{NM}_NDWI'),
                        self._url(s2.select('NDMI'), aoi, sc, f'{NM}_NDMI'),
                        self._url(s2.select('NBR'),  aoi, sc, f'{NM}_NBR'),
                        self._url(s2.select('BSI'),  aoi, sc, f'{NM}_BSI'),
                    ])
                    self.modulo_ok.emit('vegetacion', res, urls)
                    RG['vegetacion'] = res
                except Exception as e:
                    self.error_modulo.emit('vegetacion', str(e))
                paso += 1

            # ── COBERTURA ─────────────────────────────────────────────────────
            if 'cobertura' in self.modulos and not self._cancelar:
                try:
                    self.progreso.emit('Calculando cobertura del suelo (Dynamic World)...', int(paso/tot*85))
                    sc = self._escala(10)
                    col_dw = (ee.ImageCollection('GOOGLE/DYNAMICWORLD/V1')
                              .filterBounds(aoi).filterDate(self.fecha_ini, self.fecha_fin))
                    periodo_dw = self._periodo(col_dw)
                    dw = col_dw.select('label').mode().clip(aoi)
                    CLASES = {
                        0:('Agua',          '#419BDF','Cuerpos hídricos permanentes'),
                        1:('Árboles',       '#397D49','Bosque nativo y plantaciones'),
                        2:('Césped/Pasto',  '#88B053','Pastizales y praderas'),
                        3:('Veg. inundada', '#7A87C6','Bofedales y humedales'),
                        4:('Cultivos',      '#E49635','Tierras agrícolas activas'),
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
                    res = {'_periodo': periodo_dw, '_resolucion': '10 m',
                           '_fuente': 'GOOGLE/DYNAMICWORLD/V1',
                           '_total_pixeles': int(total_px)}
                    for k, v in hist.items():
                        ki  = int(float(k))
                        nom = CLASES.get(ki, (f'Clase_{ki}','#9E9E9E',''))[0]
                        res[f'{nom} (%)']     = round(v / total_px * 100, 2)
                        res[f'{nom} pixeles'] = int(v)
                    res['_clases_info'] = {
                        str(k): {'nombre':v[0],'color':v[1],'descripcion':v[2]}
                        for k,v in CLASES.items()}
                    self.modulo_ok.emit('cobertura', res, self._url(dw, aoi, sc, f'{NM}_Cobertura'))
                    RG['cobertura'] = res
                except Exception as e:
                    self.error_modulo.emit('cobertura', str(e))
                paso += 1

            # ── CLIMA ─────────────────────────────────────────────────────────
            if 'clima' in self.modulos and not self._cancelar:
                try:
                    self.progreso.emit('Calculando precipitación (CHIRPS)...', int(paso/tot*85))
                    col_ch = (ee.ImageCollection('UCSB-CHG/CHIRPS/DAILY')
                              .filterBounds(aoi).filterDate(self.fecha_ini, self.fecha_fin)
                              .select('precipitation'))
                    periodo_ch = self._periodo(col_ch)
                    pp_tot = col_ch.sum().clip(aoi)
                    st = pp_tot.reduceRegion(
                        ee.Reducer.mean()
                        .combine(ee.Reducer.minMax(), sharedInputs=True)
                        .combine(ee.Reducer.stdDev(), sharedInputs=True)
                        .combine(ee.Reducer.count(), sharedInputs=True),
                        geometry=aoi, scale=5566, maxPixels=1e13, bestEffort=True).getInfo()
                    meses = {}
                    for m in range(1, 13):
                        v = (col_ch.filter(ee.Filter.calendarRange(m, m, 'month'))
                             .sum().reduceRegion(ee.Reducer.mean(),
                             geometry=aoi, scale=5566, maxPixels=1e13, bestEffort=True).getInfo())
                        meses[f'PP_Mes_{m:02d} (mm)'] = round(v.get('precipitation', 0) or 0, 1)
                    res = {
                        'Precipitación total (mm)':   round(st.get('precipitation_mean', 0) or 0, 1),
                        'Precipitación mínima (mm)':  round(st.get('precipitation_min',  0) or 0, 1),
                        'Precipitación máxima (mm)':  round(st.get('precipitation_max',  0) or 0, 1),
                        'Desv. estándar PP (mm)':     round(st.get('precipitation_stdDev',0) or 0, 2),
                        'N° píxeles analizados':      int(st.get('precipitation_count',  0) or 0),
                        '_periodo':    periodo_ch,
                        '_resolucion': '5566 m (~5 km)',
                        '_fuente':     'UCSB-CHG/CHIRPS/DAILY',
                        **meses
                    }
                    self.modulo_ok.emit('clima', res, self._url(pp_tot, aoi, 5566, f'{NM}_Precipitacion'))
                    RG['clima'] = res
                except Exception as e:
                    self.error_modulo.emit('clima', str(e))
                paso += 1

            # ── TEMPERATURA ───────────────────────────────────────────────────
            if 'temperatura' in self.modulos and not self._cancelar:
                try:
                    self.progreso.emit('Calculando temperatura (ERA5-Land)...', int(paso/tot*85))
                    col_era = (ee.ImageCollection('ECMWF/ERA5_LAND/MONTHLY_AGGR')
                               .filterBounds(aoi).filterDate(self.fecha_ini, self.fecha_fin)
                               .select('temperature_2m'))
                    periodo_era = self._periodo(col_era)
                    t_med = col_era.mean().subtract(273.15).clip(aoi)
                    t_min = col_era.min().subtract(273.15).clip(aoi)
                    t_max = col_era.max().subtract(273.15).clip(aoi)
                    def tm(img):
                        return img.reduceRegion(
                            ee.Reducer.mean().combine(ee.Reducer.stdDev(), sharedInputs=True)
                            .combine(ee.Reducer.count(), sharedInputs=True),
                            geometry=aoi, scale=11132, maxPixels=1e13, bestEffort=True).getInfo()
                    st_med = tm(t_med)
                    meses = {}
                    for m in range(1, 13):
                        v = (col_era.filter(ee.Filter.calendarRange(m, m, 'month'))
                             .mean().subtract(273.15)
                             .reduceRegion(ee.Reducer.mean(),
                             geometry=aoi, scale=11132, maxPixels=1e13, bestEffort=True).getInfo())
                        meses[f'Temp_Mes_{m:02d} (°C)'] = round(v.get('temperature_2m', 0) or 0, 1)
                    t_med_v = round(st_med.get('temperature_2m_mean',   0) or 0, 1)
                    t_min_v = round(tm(t_min).get('temperature_2m_mean',0) or 0, 1)
                    t_max_v = round(tm(t_max).get('temperature_2m_mean',0) or 0, 1)
                    res = {
                        'Temperatura media anual (°C)': t_med_v,
                        'Temperatura mínima (°C)':       t_min_v,
                        'Temperatura máxima (°C)':       t_max_v,
                        'Amplitud térmica (°C)':         round(t_max_v - t_min_v, 1),
                        'Desv. estándar T (°C)':         round(st_med.get('temperature_2m_stdDev', 0) or 0, 2),
                        'N° píxeles analizados':         int(st_med.get('temperature_2m_count',   0) or 0),
                        '_periodo':    periodo_era,
                        '_resolucion': '11132 m (~11 km)',
                        '_fuente':     'ECMWF/ERA5_LAND/MONTHLY_AGGR',
                        **meses
                    }
                    self.modulo_ok.emit('temperatura', res, self._url(t_med, aoi, 11132, f'{NM}_Temperatura'))
                    RG['temperatura'] = res
                except Exception as e:
                    self.error_modulo.emit('temperatura', str(e))
                paso += 1

            # ── SUELOS ────────────────────────────────────────────────────────
            if 'suelos' in self.modulos and not self._cancelar:
                try:
                    self.progreso.emit('Calculando propiedades del suelo (SoilGrids)...', int(paso/tot*85))
                    sc = self._escala(250)
                    def gm(img, band):
                        st = img.clip(aoi).reduceRegion(
                            ee.Reducer.mean().combine(ee.Reducer.stdDev(), sharedInputs=True)
                            .combine(ee.Reducer.count(), sharedInputs=True),
                            geometry=aoi, scale=sc, maxPixels=1e13, bestEffort=True).getInfo()
                        return (st.get(f'{band}_mean', 0) or 0,
                                st.get(f'{band}_stdDev', 0) or 0,
                                int(st.get(f'{band}_count', 0) or 0))
                    ph   = ee.Image('OpenLandMap/SOL/SOL_PH-H2O_USDA-4C1A2A_M/v02').select('b0')
                    carb = ee.Image('OpenLandMap/SOL/SOL_ORGANIC-CARBON_USDA-6A1C_M/v02').select('b0')
                    clay = ee.Image('OpenLandMap/SOL/SOL_CLAY-WFRACTION_USDA-3A1A1A_M/v02').select('b0')
                    sand = ee.Image('OpenLandMap/SOL/SOL_SAND-WFRACTION_USDA-3A1A1A_M/v02').select('b0')
                    bulk = ee.Image('OpenLandMap/SOL/SOL_BULKDENS-FINEEARTH_USDA-4A1H_M/v02').select('b0')
                    v_ph,   std_ph,  cnt_ph  = gm(ph,   'b0'); v_ph   /= 10.0; std_ph /= 10.0
                    v_carb, std_c,   cnt_c   = gm(carb, 'b0')
                    v_clay, std_cl,  cnt_cl  = gm(clay, 'b0')
                    v_sand, std_sa,  cnt_sa  = gm(sand, 'b0')
                    v_silt = max(0, 100 - v_clay - v_sand)
                    v_bulk, std_bu,  cnt_bu  = gm(bulk, 'b0'); v_bulk /= 100.0
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
                        'pH del suelo (0-5 cm)':       round(v_ph,   2),
                        'pH stdDev':                    round(std_ph, 3),
                        'Carbono orgánico (g/kg)':      round(v_carb, 1),
                        'Carbono stdDev (g/kg)':        round(std_c,  2),
                        'Arcilla (%)':                  round(v_clay, 1),
                        'Limo (%)':                     round(v_silt, 1),
                        'Arena (%)':                    round(v_sand, 1),
                        'Clase textural USDA':          ctusda(v_clay, v_sand, v_silt),
                        'Densidad aparente (g/cm³)':    round(v_bulk, 2),
                        'N° píxeles analizados':        cnt_ph,
                        '_periodo':    'Estático — modelo ML SoilGrids 2.0',
                        '_resolucion': '250 m',
                        '_fuente':     'OpenLandMap/SOL (ISRIC SoilGrids)',
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

            # ── EROSIÓN RUSLE ─────────────────────────────────────────────────
            if 'erosion' in self.modulos and not self._cancelar:
                try:
                    self.progreso.emit('Calculando riesgo de erosión RUSLE...', int(paso/tot*85))
                    sc   = self._escala(30)
                    dem  = ee.Image('USGS/SRTMGL1_003').clip(aoi)
                    pend = ee.Terrain.slope(dem)
                    prad = pend.multiply(math.pi/180)
                    ls   = prad.sin().divide(0.0896).pow(0.6).multiply(
                           prad.tan().divide(0.0896).pow(1.3)).rename('LS')
                    chirps_r = (ee.ImageCollection('UCSB-CHG/CHIRPS/DAILY')
                                .filterBounds(aoi).filterDate(self.fecha_ini, self.fecha_fin)
                                .select('precipitation').mean().clip(aoi))
                    dw_e = (ee.ImageCollection('GOOGLE/DYNAMICWORLD/V1')
                            .filterBounds(aoi).filterDate(self.fecha_ini, self.fecha_fin)
                            .select('label').mode().clip(aoi))
                    c_factor = dw_e.remap(
                        list(range(9)),
                        [0.001, 0.003, 0.01, 0.005, 0.2, 0.02, 0.6, 0.4, 0.0]
                    ).rename('C').toFloat()
                    rusle = chirps_r.multiply(0.04).multiply(ls).multiply(c_factor).rename('RUSLE')
                    st = rusle.reduceRegion(
                        ee.Reducer.mean()
                        .combine(ee.Reducer.minMax(), sharedInputs=True)
                        .combine(ee.Reducer.stdDev(), sharedInputs=True)
                        .combine(ee.Reducer.count(),  sharedInputs=True),
                        geometry=aoi, scale=sc, maxPixels=1e13, bestEffort=True).getInfo()
                    media = st.get('RUSLE_mean') or 0
                    res = {
                        'Índice RUSLE medio':     round(media, 4),
                        'Índice RUSLE máximo':    round(st.get('RUSLE_max',    0) or 0, 4),
                        'Índice RUSLE stdDev':    round(st.get('RUSLE_stdDev', 0) or 0, 4),
                        'N° píxeles analizados':  int(st.get('RUSLE_count',   0) or 0),
                        'Riesgo erosivo':         'Bajo' if media<0.02 else 'Medio' if media<0.1 else 'Alto',
                        '_periodo':    f'{self.fecha_ini} — {self.fecha_fin}',
                        '_resolucion': '30 m',
                        '_fuente':     'SRTM + CHIRPS + Dynamic World (RUSLE simplificado)',
                    }
                    self.modulo_ok.emit('erosion', res, self._url(rusle, aoi, sc, f'{NM}_RUSLE'))
                    RG['erosion'] = res
                except Exception as e:
                    self.error_modulo.emit('erosion', str(e))
                paso += 1

            # ── EVAPOTRANSPIRACIÓN ────────────────────────────────────────────
            if 'evapotranspiracion' in self.modulos and not self._cancelar:
                try:
                    self.progreso.emit('Calculando evapotranspiración (MOD16)...', int(paso/tot*85))
                    sc = self._escala(500)
                    col_et = (ee.ImageCollection('MODIS/061/MOD16A2GF')
                              .filterBounds(aoi).filterDate(self.fecha_ini, self.fecha_fin)
                              .select('ET'))
                    periodo_et = self._periodo(col_et)
                    et = col_et.mean().multiply(0.1).clip(aoi)
                    st = et.reduceRegion(
                        ee.Reducer.mean()
                        .combine(ee.Reducer.minMax(), sharedInputs=True)
                        .combine(ee.Reducer.stdDev(), sharedInputs=True)
                        .combine(ee.Reducer.count(),  sharedInputs=True),
                        geometry=aoi, scale=sc, maxPixels=1e13, bestEffort=True).getInfo()
                    res = {
                        'ET media (mm/8 días)':   round(st.get('ET_mean',   0) or 0, 2),
                        'ET mínima (mm/8 días)':  round(st.get('ET_min',    0) or 0, 2),
                        'ET máxima (mm/8 días)':  round(st.get('ET_max',    0) or 0, 2),
                        'ET stdDev (mm/8 días)':  round(st.get('ET_stdDev', 0) or 0, 2),
                        'N° píxeles analizados':  int(st.get('ET_count',   0) or 0),
                        '_periodo':    periodo_et,
                        '_resolucion': '500 m',
                        '_fuente':     'MODIS/061/MOD16A2GF',
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
                        'País':         info.get('ADM0_NAME', 'N/D'),
                        'Departamento': info.get('ADM1_NAME', 'N/D'),
                        'Distrito':     info.get('ADM2_NAME', 'N/D'),
                    }
                    if 'topografia' in RG:
                        RG['_admin']['Altitud media (msnm)'] = RG['topografia'].get('Elevación media (msnm)', 'N/D')
                except Exception:
                    RG['_admin'] = {}

            self.progreso.emit('Diagnóstico completado.', 100)
            self.terminado.emit(RG)

        except Exception as e:
            self.error_fatal.emit(f'{str(e)}\n\n{traceback.format_exc()}')
