import os
import requests
from flask import Flask, request, Response, render_template
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# GET KEYS FROM RENDER ENV
XI_API_KEY = os.environ.get("XI_API_KEY")
# Use a STANDARD voice ID to avoid 402 Payment Error
VOICE_ID = os.environ.get("VOICE_ID") 

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/process_audio', methods=['POST'])
def process_audio():
    if not XI_API_KEY or not VOICE_ID:
        return {"error": "Missing Keys"}, 500

    if 'audio' not in request.files:
        return {"error": "No audio"}, 400
    
    audio_file = request.files['audio']
    
    # ⚡ OPTIMIZATION: Use 'eleven_turbo_v2' for lowest latency (It is faster than multilingual)
    # If you need Hindi accent, switch back to 'eleven_multilingual_v2'
    model_id = "eleven_multilingual_v2" 

    url = f"https://api.elevenlabs.io/v1/speech-to-speech/{VOICE_ID}/stream"
    
    headers = {
        "xi-api-key": XI_API_KEY,
        "accept": "audio/mpeg"
    }

    # ⚡ DATA: Lower stability = More accent variation
    data = {
        "model_id": model_id,
        "voice_settings": '{"stability": 0.4, "similarity_boost": 0.6}'
    }

    files = {
        'audio': (audio_file.filename, audio_file.read(), 'audio/webm')
    }

    # ⚡ STREAMING REQUEST
    try:
        response = requests.post(url, headers=headers, data=data, files=files, stream=True)
        
        if response.status_code != 200:
            error_msg = response.text
            print(f"Error: {error_msg}")
            # Check specifically for 402 to warn user
            if response.status_code == 402:
                return {"error": "PAYMENT ERROR: You are using a Paid Voice on a Free Plan. Change VOICE_ID."}, 402
            return Response(error_msg, status=response.status_code)

        # Generator function to stream bytes instantly to frontend
        def generate():
            for chunk in response.iter_content(chunk_size=1024):
                if chunk:
                    yield chunk

        return Response(generate(), mimetype="audio/mpeg")

    except Exception as e:
        return {"error": str(e)}, 500

if __name__ == '__main__':
    app.run(debug=True)
