import sys
import sqlite3
import json
from mcp.server import Server
from mcp.server.stdio import stdio_server

app = Server("sqlite-server")

@app.list_tools()
async def list_tools():
    return [
        {
            "name": "query",
            "description": "Ejecuta una consulta SQL de solo lectura en la base SQLite. Devuelve los resultados como una cadena JSON (lista de objetos).",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "sql": {"type": "string", "description": "Consulta SQL SELECT"}
                },
                "required": ["sql"],
            },
        }
    ]

@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list:
    if name != "query":
        raise ValueError(f"Herramienta desconocida: {name}")
    sql = arguments["sql"]
    db_path = sys.argv[1]  # pasado como argumento al script
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    try:
        cur = conn.execute(sql)
        rows = [dict(row) for row in cur.fetchall()]
        conn.close()
        # Devuelve el resultado como texto JSON
        return [type("Content", (), {"type": "text", "text": json.dumps(rows, ensure_ascii=False, default=str)})()]
    except Exception as e:
        conn.close()
        return [type("Content", (), {"type": "text", "text": json.dumps({"error": str(e)}, ensure_ascii=False)})()]

async def main():
    async with stdio_server() as (read_stream, write_stream):
        await app.run(read_stream, write_stream, app.create_initialization_options())

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())