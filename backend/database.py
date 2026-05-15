import os
import sqlite3
import pandas as pd
from config import CSV_PATH, SQLITE_DB_PATH

def create_db_from_csv():
    """Crea/sobreescribe una BD SQLite con los datos del CSV."""
    if not os.path.exists(CSV_PATH):
        raise FileNotFoundError(f"No se encuentra el archivo CSV: {CSV_PATH}")

    df = pd.read_csv(CSV_PATH)
    # Asegurarse de que exista la carpeta data
    os.makedirs(os.path.dirname(SQLITE_DB_PATH), exist_ok=True)

    conn = sqlite3.connect(SQLITE_DB_PATH)
    df.to_sql("datos", conn, if_exists="replace", index=False)
    conn.close()
    print(f"Base de datos creada en {SQLITE_DB_PATH} con {len(df)} registros.")
    return SQLITE_DB_PATH