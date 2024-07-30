import os
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from dotenv import load_dotenv
import firebase_admin
from firebase_admin import credentials, firestore
from elevenlabs.client import ElevenLabs

load_dotenv()

# Initialize Firebase
cred = credentials.Certificate(os.getenv("FIREBASE_CREDENTIALS"))
firebase_admin.initialize_app(cred)
db = firestore.client()

app = FastAPI()

elevenlabs = ElevenLabs(api_key=os.getenv("ELEVENLABS_API_KEY"))

class SoundRequest(BaseModel):
    phrases: list[str]
    duration_seconds: int = 10
    prompt_influence: float = 0.3

@app.post("/generate_sound_effects")
async def generate_sound_effects(request: SoundRequest):
    try:
        audio_paths = []
        for index, text in enumerate(request.phrases):
            result = elevenlabs.text_to_sound_effects.convert(
                text=text,
                duration_seconds=request.duration_seconds,
                prompt_influence=request.prompt_influence,
            )

            output_path = f"output_{index}.mp3"
            with open(output_path, "wb") as f:
                for chunk in result:
                    f.write(chunk)

            audio_paths.append(output_path)

        # Save the audio paths to Firestore
        write_result = db.collection("audio_files").add({"paths": audio_paths})
        doc_ref = write_result[1]  # Ensure you get the DocumentReference object
        
        

        return {"message": "Audio files saved successfully", "paths": audio_paths, "firestore_doc_id": doc_ref.id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
