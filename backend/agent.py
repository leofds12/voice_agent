import json
import sqlite3
import requests
from config import OLLAMA_BASE_URL, OLLAMA_MODEL, SQLITE_DB_PATH

OLLAMA_URL = f"{OLLAMA_BASE_URL.rstrip('/')}/api/chat"

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "run_sql_query",
            "description": "Ejecuta una consulta SQL contra la base de datos SQLite. Devuelve los resultados en formato JSON. Solo se debe usar para consultas de datos de tipo SELECT. No se permiten operaciones de escritura, actualización ni borrado.",
            "parameters": {
                "type": "object",
                "properties": {
                    "sql": {
                        "type": "string",
                        "description": "Consulta SQL a ejecutar",
                    }
                },
                "required": ["sql"],
            },
        },
    }
]

def ejecutar_sql(sql):
    """Ejecuta SQL directo y devuelve JSON."""
    conn = sqlite3.connect(SQLITE_DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        cursor = conn.execute(sql)
        rows = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return json.dumps(rows, ensure_ascii=False, default=str)
    except Exception as e:
        conn.close()
        return json.dumps({"error": str(e)})

class Agent:
    def __init__(self):
        self._schema_cache = None

    def _get_schema(self):
        if self._schema_cache:
            return self._schema_cache

        conn = sqlite3.connect(SQLITE_DB_PATH)
        cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        if not tables:
            conn.close()
            return "No hay tablas en la base de datos."

        table_name = tables[0][0]
        cursor = conn.execute(f"PRAGMA table_info('{table_name}')")
        columns = cursor.fetchall()
        schema = f"Columnas de la tabla '{table_name}':\n"
        for col in columns:
            schema += f"  - {col[1]} ({col[2]})\n"

        sample = conn.execute(f"SELECT * FROM '{table_name}' LIMIT 3")
        rows = sample.fetchall()
        if rows:
            schema += "\nFilas de ejemplo:\n"
            for row in rows:
                schema += f"  {tuple(row)}\n"

        conn.close()
        self._schema_cache = schema
        return schema

    def _build_system_prompt(self):
        return f"""Eres un asistente de análisis de datos. Tienes acceso a una base de datos SQLite con información de ventas de vestimenta.

    {self._get_schema()}

    **IMPORTANTE SOBRE LAS COLUMNAS:**
    - La columna 'Mes' es solo el número del mes (1 a 12)
    - La columna 'Año' es el año (2023, 2024, 2025, 2026)
    - Para análisis por mes, SIEMPRE agrupá por Año y Mes juntos: GROUP BY Año, Mes
    - Para comparar meses entre años, usá ambos campos
    - La columna 'Precio' es el monto de cada venta individual
    - Para totales usá SUM(Precio)

    Cuando el usuario haga preguntas que requieran consultar los datos, DEBES usar la herramienta 'run_sql_query' con una consulta SQL válida.
    Después de obtener el resultado, proporciona una respuesta clara en español, interpretando los datos.
    Si el usuario pregunta algo que no tenga relación con los datos, responde amablemente sin usar la herramienta.
    No inventes datos; si la consulta falla, comunícalo educadamente."""

    def _call_ollama(self, messages, tools=None, temperature=0.2):
        payload = {
            "model": OLLAMA_MODEL,
            "messages": messages,
            "stream": False,
            "options": {"temperature": temperature},
        }
        if tools:
            payload["tools"] = tools

        response = requests.post(OLLAMA_URL, json=payload, timeout=300)
        response.raise_for_status()

        text = response.text.strip()
        if '\n' in text:
            for line in text.split('\n'):
                obj = json.loads(line)
                if "message" in obj:
                    return obj["message"]
        return json.loads(text)["message"]

    def _format_data(self, data):
        try:
            rows = json.loads(data)
            if isinstance(rows, dict) and "error" in rows:
                return f"Error: {rows['error']}"
            if isinstance(rows, list) and len(rows) > 0:
                headers = list(rows[0].keys())
                tabla = " | ".join(headers) + "\n"
                tabla += "-" * len(tabla) + "\n"
                for row in rows:
                    tabla += " | ".join(str(row[h]) for h in headers) + "\n"
                return tabla
            return str(rows)
        except:
            return str(data)

    async def process_message(self, user_text: str) -> dict:
        system_prompt = self._build_system_prompt()
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_text},
        ]
        sql = None
        data = None

        message = self._call_ollama(messages, tools=TOOLS)

        if message.get("tool_calls"):
            tool_call = message["tool_calls"][0]
            if tool_call["function"]["name"] == "run_sql_query":
                args = tool_call["function"]["arguments"]
                if isinstance(args, str):
                    args = json.loads(args)
                sql = args["sql"]

                # Ejecutar SQL directo (sin MCP)
                data = ejecutar_sql(sql)

                datos_tabla = self._format_data(data)

                messages = [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f'El usuario preguntó: "{user_text}"\n\nSQL ejecutada: {sql}\n\nResultado:\n{datos_tabla}\n\nRespondé al usuario en español analizando estos datos.'}
                ]

                try:
                    message2 = self._call_ollama(messages, tools=None, temperature=0.4)
                    answer = message2.get("content", "Sin respuesta.")
                except Exception as e:
                    answer = f"Error: {str(e)}"
            else:
                answer = "Lo siento, no puedo realizar esa acción."
        else:
            answer = message.get("content", "Sin respuesta.")

        return {"answer": answer, "sql": sql, "data": data}