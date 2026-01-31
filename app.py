import os
import requests
from flask import Flask, request, Response, render_template
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# ---------------- CONFIGURATION ---------------- #
# We get these from Render's "Environment Variables" later
XI_API_KEY = os.environ.get("XI_API_KEY")
VOICE_ID = os.environ.get("VOICE_ID")
# ----------------------------------------------- #

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/process_audio', methods=['POST'])
def process_audio():
    if not XI_API_KEY or not VOICE_ID:
        return {"error": "Missing API Key or Voice ID on Server"}, 500

    # 1. Get the audio file from the frontend
    if 'audio' not in request.files:
        return {"error": "No audio uploaded"}, 400
    
    audio_file = request.files['audio']
    
    # 2. Prepare headers for ElevenLabs
    CHUNK_SIZE = 1024
    url = f"https://api.elevenlabs.io/v1/speech-to-speech/{VOICE_ID}"
    
    headers = {
        "xi-api-key": XI_API_KEY,
    }

    # 3. Setup the data (Multipart upload)
    files = {
        'audio': (audio_file.filename, audio_file.read(), 'audio/webm')
    }
    
    # Model settings for Indian accent
    data = {
        "model_id": "eleven_multilingual_v2", 
        "voice_settings": '{"stability": 0.5, "similarity_boost": 0.8}'
    }

    # 4. Stream the response back to the user
    # (This reduces lag significantly)
    try:
        response = requests.post(url, headers=headers, data=data, files=files, stream=True)
        
        if response.status_code != 200:
            return Response(response.text, status=response.status_code)

        def generate():
            for chunk in response.iter_content(chunk_size=CHUNK_SIZE):
                if chunk:
                    yield chunk

        return Response(generate(), mimetype="audio/mpeg")

    except Exception as e:
        return {"error": str(e)}, 500

if __name__ == '__main__':
    app.run(debug=True)
