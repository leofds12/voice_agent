# SQL Agent – Consulta tus datos con la voz

Aplicación que permite hablar desde tu celular, transcribir la pregunta en español, y que un agente inteligente responda consultando una base de datos SQLite generada a partir de tu archivo CSV.

## Requisitos

- Python 3.10+
- Una API key de OpenAI (GPT-4o o compatible)
- PC donde ejecutar el backend (Windows/Linux/macOS)
- Celular con navegador moderno (misma red WiFi)

## Configuración inicial

1. Clona/descarga este proyecto.
2. Coloca tu CSV (`datos.csv`) en la carpeta `data/`. Debe tener al menos las columnas `fecha, monto, modelo` (pueden existir otras).
3. Copia `.env.example` a `.env` y completa `OPENAI_API_KEY`.
4. Instala dependencias del backend:
   ```bash
   cd backend
   pip install -r requirements.txt