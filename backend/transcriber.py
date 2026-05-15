import whisper
from config import WHISPER_MODEL

# Carga única del modelo (singleton)
_model = None

def get_model():
    global _model
    if _model is None:
        print(f"Cargando modelo Whisper '{WHISPER_MODEL}'...")
        _model = whisper.load_model(WHISPER_MODEL)
    return _model

def transcribe_audio(audio_path: str, language: str = "es") -> str:
    model = get_model()
    result = model.transcribe(
        audio_path,
        language=language,
        temperature=0.4,
        beam_size=5,
        best_of=5,
        condition_on_previous_text=False,
        fp16=False
    )
    return result["text"].strip()