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

    def _ejecutar_mapeo(self, df):
        """Tu lógica de cargado inteligente: busca columnas por alias"""
        df.columns = [c.upper().strip() for c in df.columns]
        
        # Diccionario de búsqueda flexible para adaptarse a cualquier CSV
        mapeo = {
            'id': ['ID', 'RP', 'ID_VACA', 'IDENTIFICACION'],
            'lact': ['LACT', 'LACTANCIA'],
            'del': ['DEL', 'D.E.L.'],
            'leche': ['LECHE', 'PROD', 'LTS', 'LITROS'],
            'rpro': ['RPRO', 'ESTADO', 'PRE', 'REPRO'],
            'dduc': ['DDUC', 'D.D.U.C', 'DIAS_ULT_CELO', 'DDP']
        }

        df_final = pd.DataFrame()
        for destino, opciones in mapeo.items():
            encontrada = next((o for o in opciones if o in df.columns), None)
            if encontrada:
                df_final[destino] = df[encontrada]
            else:
                # Valores por defecto para evitar errores en cálculos
                df_final[destino] = "0" if destino in ['leche', 'dduc', 'del', 'lact'] else "-"
        return df_final

    def get_dashboard_data(self):
        """Analítica de precisión basada en el mapeo de VACAS_LF.csv"""
        try:
            archivo = 'VACAS_LF.csv'
            if not os.path.exists(archivo):
                return {"error": "Archivo VACAS_LF.csv no detectado"}

            # Carga inteligente
            df_raw = pd.read_csv(archivo, dtype=str)
            df = self._ejecutar_mapeo(df_raw)

            total = len(df)
            # Conversión segura a números para promedio
            leche_num = pd.to_numeric(df['leche'], errors='coerce').fillna(0)
            
            # Análisis de estados reproductivos (Usa tu lógica de strings contains)
            serie_repro = df['rpro'].str.upper().fillna('')
            pre = serie_repro.str.contains('PRE').sum()
            ins = serie_repro.str.contains('INS').sum()
            rech = serie_repro.str.contains('RECH').sum()
            vacias = total - (pre + ins + rech)

            return {
                "total_animales": int(total),
                "promedio_litros": round(float(leche_num.mean()), 1) if not leche_num.empty else 0,
                "alertas_salud": "Ok", # Módulo de salud pendiente de mapear
                "repro": {
                    "PREÑADAS": int(pre),
                    "INSEMINADAS": int(ins),
                    "RECHAZO": int(rech),
                    "VACÍAS": int(vacias)
                }
            }
        except Exception as e:
            print(f"Error Dashboard: {e}")
            return {"error": str(e)}

    def get_lista_completa(self):
        """Devuelve todo el hato mapeado para la tabla de la Manga"""
        try:
            archivo = 'VACAS_LF.csv'
            if not os.path.exists(archivo):
                return []
            
            df_raw = pd.read_csv(archivo, dtype=str)
            df = self._ejecutar_mapeo(df_raw)
            
            # Convertimos el DataFrame a una lista de diccionarios
            return df.to_dict(orient='records')
        except Exception as e:
            print(f"Error lista completa: {e}")
            return []

    def get_datos_grafico(self):
        """Extrae la tendencia de producción para el gráfico visual"""
        try:
            archivo = 'produccion_leche_6_meses.csv'
            if os.path.exists(archivo):
                df = pd.read_csv(archivo)
                # Tomamos los últimos 30 días para el gráfico
                ultimos_datos = df.tail(30) 
                return {
                    "labels": ultimos_datos['FECHA'].tolist(),
                    "valores": ultimos_datos['LITROS'].tolist()
                }
            return {"error": "Archivo histórico no encontrado"}
        except Exception as e:
            return {"error": str(e)}

    def procesar_comando(self, comando, params_json):
        """Búsqueda en Manga utilizando el mapeo inteligente"""
        params = json.loads(params_json) if isinstance(params_json, str) else params_json
        caravana = str(params.get('caravana'))
        
        try:
            df = self._ejecutar_mapeo(pd.read_csv('VACAS_LF.csv', dtype=str))
            vaca = df[df['id'] == caravana]

            if not vaca.empty:
                v = vaca.iloc[0]
                alertas = []
                
                # Ejemplo de alerta inteligente basada en dduc
                if v['rpro'] == 'INSEMIN' and int(v['dduc']) > 30:
                    alertas.append({"tipo": "repro", "msj": "⚠️ TACTO PENDIENTE", "color": "#f1e05a"})

                return {
                    "animal": {
                        "caravana": v['id'],
                        "estado": v['rpro'],
                        "leche": v['leche'],
                        "del": v['del'],
                        "lact": v['lact']
                    },
                    "alertas": alertas
                }
            return {"status": "empty"}
        except Exception as e:
            print(f"Error en Manga: {e}")
            return {"status": "empty"}

    def registrar_evento_repro(self, caravana, tipo, resultado):
        """Persistencia de cambios manuales en el Servidor PS"""
        conn = database.conectar()
        cursor = conn.cursor()
        try:
            cursor.execute('CREATE TABLE IF NOT EXISTS eventos (id_vaca TEXT, tipo TEXT, resultado TEXT, fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP)')
            cursor.execute('INSERT INTO eventos (id_vaca, tipo, resultado) VALUES (?, ?, ?)', (caravana, tipo, resultado))
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
