import os
from dotenv import load_dotenv

load_dotenv()

# Directorio base del proyecto (backend/../)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
WHISPER_MODEL = os.getenv("WHISPER_MODEL", "small")
SQLITE_DB_PATH = os.getenv("SQLITE_DB_PATH", os.path.join(BASE_DIR, "data", "ventas.db"))
CSV_PATH = os.getenv("CSV_PATH", os.path.join(BASE_DIR, "data", "luleaventas3.csv"))
HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", 8000))
MCP_SERVER_PATH = os.getenv("MCP_SERVER_PATH", "../mcp_sql_server/server.py")
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434").rstrip("/")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "qwen2.5:3b")