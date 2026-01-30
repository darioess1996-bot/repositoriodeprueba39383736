import pandas as pd
import sqlite3
import os

def importar_todo_el_tambo():
    print("🚀 VIALAC: Iniciando proceso de ingesta masiva...")
    conn = sqlite3.connect('vialactea_datos.db')

    try:
        # 1. CARGAR HATO PRINCIPAL (VACAS_LF)
        if os.path.exists('VACAS_LF.csv'):
            df_vacas = pd.read_csv('VACAS_LF.csv')
            # Renombramos para nuestra DB
            df_vacas = df_vacas.rename(columns={'ID': 'id_vaca', 'RPRO': 'estado', 'LECHE': 'ult_leche'})
            df_vacas.to_sql('hato', conn, if_exists='replace', index=False)
            print(f"✅ {len(df_vacas)} vacas cargadas desde VACAS_LF.")

        # 2. CARGAR HISTORIAL REPRODUCCIÓN
        if os.path.exists('HISTORIAL_REPRODUCCION.csv'):
            df_repro = pd.read_csv('HISTORIAL_REPRODUCCION.csv')
            df_repro.to_sql('eventos', conn, if_exists='replace', index=False)
            print(f"✅ Historial reproductivo sincronizado.")

        # 3. CARGAR GENEALOGÍA
        if os.path.exists('GENEALOGIA Y SALUD.csv'):
            df_gen = pd.read_csv('GENEALOGIA Y SALUD.csv')
            df_gen.to_sql('genealogia', conn, if_exists='replace', index=False)
            print(f"✅ Datos genealógicos vinculados.")

        print("\n🔥 VIALAC: Sistema alimentado con éxito.")
    except Exception as e:
        print(f"❌ Error en la ingesta: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    importar_todo_el_tambo()
