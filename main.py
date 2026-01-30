import os
import sys
import json
import sqlite3
import pandas as pd
from PySide6.QtCore import Qt, QCoreApplication
from PySide6.QtWidgets import QApplication
import webview
import database
from intro import IntroViaLactea

# --- CONFIGURACIÓN DE ENTORNO VIALAC ---
os.environ['QT_QPA_PLATFORM'] = 'xcb'
os.environ['PYWEBVIEW_GUI'] = 'qt'
os.environ["QTWEBENGINE_DISABLE_SANDBOX"] = "1"
QCoreApplication.setAttribute(Qt.AA_ShareOpenGLContexts)

class PuenteVIALAC:
    """Orquestador Central VIALAC - Lógica de Mapeo Inteligente y Servidor PS"""

    def _get_db_connection(self):
        return database.conectar()

    def get_dashboard_data(self):
        """Analítica de precisión basada en SQLite (vialactea_datos.db)"""
        try:
            conn = self._get_db_connection()
            # Obtenemos el hato con el último evento si existe
            query = """
                SELECT h.id_vaca, h.ult_leche,
                COALESCE(e.resultado, h.estado) as estado_actual
                FROM hato h
                LEFT JOIN (
                    SELECT id_vaca, resultado
                    FROM eventos
                    WHERE id IN (SELECT MAX(id) FROM eventos GROUP BY id_vaca)
                ) e ON h.id_vaca = e.id_vaca
            """
            df = pd.read_sql_query(query, conn)
            conn.close()

            total = len(df)
            leche_num = pd.to_numeric(df['ult_leche'], errors='coerce').fillna(0)

            serie_repro = df['estado_actual'].str.upper().fillna('')
            pre = int(serie_repro.str.contains('PRE').sum())
            ins = int(((serie_repro.str.contains('INS') | (serie_repro == 'IA')) & ~serie_repro.str.contains('VAC')).sum())
            rech = int(serie_repro.str.contains('RECH').sum())
            vacias = int(total - (pre + ins + rech))

            return {
                "total_animales": int(total),
                "promedio_litros": round(float(leche_num.mean()), 1) if not leche_num.empty else 0,
                "alertas_salud": "Ok",
                "repro": {
                    "PREÑADAS": pre,
                    "INSEMINADAS": ins,
                    "RECHAZO": rech,
                    "VACÍAS": vacias
                }
            }
        except Exception as e:
            print(f"Error Dashboard: {e}")
            return {"error": str(e)}

    def get_lista_completa(self):
        """Devuelve todo el hato desde SQLite para la tabla de la Manga"""
        try:
            conn = self._get_db_connection()
            query = """
                SELECT CAST(h.id_vaca AS TEXT) as id,
                COALESCE(e.resultado, h.estado) as rpro,
                CAST(h.ult_leche AS REAL) as leche
                FROM hato h
                LEFT JOIN (
                    SELECT id_vaca, resultado
                    FROM eventos
                    WHERE id IN (SELECT MAX(id) FROM eventos GROUP BY id_vaca)
                ) e ON h.id_vaca = e.id_vaca
            """
            df = pd.read_sql_query(query, conn)
            conn.close()
            # Convertimos tipos de pandas/numpy a nativos de Python para JSON
            return df.astype(object).to_dict(orient='records')
        except Exception as e:
            print(f"Error lista completa: {e}")
            return []

    def get_datos_grafico(self):
        """Extrae la tendencia de producción para el gráfico visual"""
        try:
            archivo = 'produccion_leche_6_meses.csv'
            if os.path.exists(archivo):
                df = pd.read_csv(archivo)
                ultimos_datos = df.tail(30)
                return {
                    "labels": ultimos_datos['FECHA'].tolist(),
                    "valores": ultimos_datos['LITROS'].tolist()
                }
            return {"error": "Archivo histórico no encontrado"}
        except Exception as e:
            return {"error": str(e)}

    def procesar_comando(self, comando, params_json):
        """Búsqueda en Manga utilizando SQLite"""
        params = json.loads(params_json) if isinstance(params_json, str) else params_json
        caravana = str(params.get('caravana'))

        try:
            conn = self._get_db_connection()
            query = """
                SELECT h.*, g.PAD, COALESCE(e.resultado, h.estado) as estado_actual
                FROM hato h
                LEFT JOIN genealogia g ON h.id_vaca = g.ID
                LEFT JOIN (
                    SELECT id_vaca, resultado
                    FROM eventos
                    WHERE id IN (SELECT MAX(id) FROM eventos GROUP BY id_vaca)
                ) e ON h.id_vaca = e.id_vaca
                WHERE h.id_vaca = ?
            """
            # Uso de parámetros para evitar SQL Injection
            vaca = pd.read_sql_query(query, conn, params=(caravana,))
            conn.close()

            if not vaca.empty:
                v = vaca.iloc[0]
                alertas = []

                # Lógica de alerta migrada/mejorada
                if 'INS' in str(v['estado_actual']).upper() and int(v.get('DDP', 0)) > 30:
                    alertas.append({"tipo": "repro", "msj": "⚠️ TACTO PENDIENTE", "color": "#f1e05a"})

                return {
                    "animal": {
                        "caravana": str(v['id_vaca']),
                        "estado": str(v['estado_actual']),
                        "leche": float(v['ult_leche']) if pd.notnull(v['ult_leche']) else 0.0,
                        "del": str(v.get('DEL', '-')),
                        "lact": str(v.get('LACT', '-')),
                        "padre": str(v.get('PAD', '-'))
                    },
                    "alertas": alertas
                }
            return {"status": "empty"}
        except Exception as e:
            print(f"Error en Manga: {e}")
            return {"status": "empty"}

    def analizar_calidad_leche(self, registros):
        """Migrado de analytics.jl: Analiza promedios de calidad"""
        if not registros: return {}
        df = pd.DataFrame(registros)
        return {
            "litros_total": round(float(df['litros'].sum()), 2),
            "grasa_avg": round(float(df['grasa'].mean()), 2),
            "proteina_avg": round(float(df['proteina'].mean()), 2)
        }

    def analizar_calidad_mixer(self, cargas):
        """Migrado de alimentacion.jl: Valida orden y desvíos en alimentación"""
        alertas = []
        for c in cargas:
            if c['ingrediente'] == "Heno de Alfalfa" and c['orden_mezcla'] != 1:
                alertas.append(f"CRÍTICO: Alfalfa fuera de orden en carga {c.get('id', '')}")

            desvio = abs(c['kg_real'] - c['kg_teorico'])
            if desvio > (c['kg_teorico'] * 0.05):
                alertas.append(f"ADVERTENCIA: Carga {c['ingrediente']} con error > 5%")
        return alertas

    def registrar_ordene(self, id_vaca, litros):
        """Registro de producción individual en SQLite"""
        conn = self._get_db_connection()
        cursor = conn.cursor()
        try:
            cursor.execute('INSERT INTO produccion (id_vaca, litros) VALUES (?, ?)', (id_vaca, litros))
            # También actualizamos la última leche en la tabla hato
            cursor.execute('UPDATE hato SET ult_leche = ? WHERE id_vaca = ?', (litros, id_vaca))
            conn.commit()
            return {"status": "success", "msj": f"Ordeñe de {litros}L registrado para {id_vaca}"}
        except Exception as e:
            return {"status": "error", "msj": str(e)}
        finally:
            conn.close()

    def registrar_evento_repro(self, caravana, tipo, resultado):
        """Persistencia de cambios manuales en el Servidor PS"""
        conn = self._get_db_connection()
        cursor = conn.cursor()
        try:
            # Sincronizado con esquema de database.py
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS eventos (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    id_vaca TEXT,
                    tipo_evento TEXT,
                    resultado TEXT,
                    fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            cursor.execute('INSERT INTO eventos (id_vaca, tipo_evento, resultado) VALUES (?, ?, ?)', (caravana, tipo, resultado))
            conn.commit()
            return {"status": "success", "msj": f"Vaca {caravana} registrada como {resultado}"}
        except Exception as e:
            return {"status": "error", "msj": str(e)}
        finally:
            conn.close()

    def cerrar_app(self):
        os._exit(0)

def ejecutar_todo():
    # Inicialización de la base de datos
    database.crear_tablas()

    app = QApplication.instance() or QApplication(sys.argv)
    api = PuenteVIALAC()

    ruta_html = os.path.abspath('web/index.html')

    window = webview.create_window(
        'VIALAC - Gestión de Precisión',
        url=ruta_html,
        js_api=api,
        width=1200,
        height=800,
        background_color='#0d111b'
    )

    def al_terminar_intro():
        splash.close()

    # Lanzamiento con Splash Screen
    splash = IntroViaLactea(al_terminar=al_terminar_intro)
    splash.show()

    # Debug activado para inspeccionar desde la interfaz (F12 o Clic Derecho)
    webview.start(gui='qt', debug=True)

if __name__ == "__main__":
    ejecutar_todo()
