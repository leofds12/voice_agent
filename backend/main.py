import os
import uuid
import tempfile
from contextlib import asynccontextmanager
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
import uvicorn

from config import HOST, PORT, SQLITE_DB_PATH
from database import create_db_from_csv
from transcriber import transcribe_audio
from agent import Agent

agent = Agent()

class TextoInput(BaseModel):
    texto: str

@asynccontextmanager
async def lifespan(app: FastAPI):
    if not os.path.exists(SQLITE_DB_PATH):
        create_db_from_csv()
    yield

app = FastAPI(title="SQL Agent Backend", lifespan=lifespan)
app.mount("/app", StaticFiles(directory="../mobile"), name="mobile")

@app.get("/")
async def root():
    return FileResponse("../mobile/index.html")

@app.post("/ask")
async def ask(audio: UploadFile = File(...)):
    with tempfile.NamedTemporaryFile(delete=False, suffix=".ogg") as tmp:
        contents = await audio.read()
        tmp.write(contents)
        tmp_path = tmp.name
    try:
        texto = transcribe_audio(tmp_path, language="es")
        result = await agent.process_message(texto)
        print(f"\n🎤 {texto}\n📊 {result['sql']}\n💬 {result['answer']}\n")
        return {
            "transcripcion": texto,
            "respuesta": result["answer"],
            "sql": result["sql"],
            "datos": result["data"]
        }
    finally:
        os.unlink(tmp_path)

@app.post("/preguntar")
async def preguntar(body: TextoInput):
    result = await agent.process_message(body.texto)
    print(f"\n💬 {body.texto}\n📊 {result['sql']}\n🤖 {result['answer']}\n")
    return {"respuesta": result["answer"], "sql": result["sql"]}

if __name__ == "__main__":
    uvicorn.run(app, host=HOST, port=PORT)