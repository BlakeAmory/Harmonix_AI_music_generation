#define libraries
from fastapi import FastAPI, Form, Request
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from transformers import AutoProcessor, MusicgenForConditionalGeneration
import torch
import scipy.io.wavfile
import os
from dotenv import load_dotenv

app = FastAPI()

# Load environment variables
load_dotenv()

# Mount static files directory
app.mount("/static", StaticFiles(directory="static"), name="static")

# Load HTML templates
templates = Jinja2Templates(directory="templates")

# Initialize the MusicGen model and processor
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
processor = AutoProcessor.from_pretrained("facebook/musicgen-large")
model = MusicgenForConditionalGeneration.from_pretrained("facebook/musicgen-large").to(device)

@app.get("/")
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/generate-music")
async def generate_music(prompt: str = Form(...), duration: int = Form(...)):
    # Process the input
    inputs = processor(
        text=[prompt],
        padding=True,
        return_tensors="pt",
    ).to(device)

    # Generate audio
    audio_values = model.generate(**inputs, max_new_tokens=duration * 50)  # Approximate tokens for duration

    # Convert to numpy and save as wav
    audio_data = audio_values[0, 0].cpu().numpy()
    output_path = "static/generated_music.wav"
    scipy.io.wavfile.write(output_path, rate=model.config.audio_encoder.sampling_rate, data=audio_data)

    # Return the URL of the generated audio file
    return JSONResponse(content={"url": "/static/generated_music.wav"})

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
