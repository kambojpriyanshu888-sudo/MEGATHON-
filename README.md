
SahAI — Accessible Language Companion
Technical Setup & Deployment Guide
Prerequisites
Before commencing setup, verify that your environment satisfies the following baseline requirements:

Python Engine: Python 3.9 or higher
OCR Subsystem: Tesseract OCR (with installed language packs for English, Hindi, and Punjabi)


1. Installation & Environment Setup
Initialize your local project directory via terminal or VS Code terminal and set up an isolated Python environment:# Create virtual environment

py -m venv .venv

# Activate virtual environment (Windows PowerShell)

.venv\Scripts\Activate.ps1

# Upgrade pip package manager and install dependencies

python -m pip install --upgrade pip

pip install -r requirements.txt


2. Configure Tesseract OCR
Download and install the Tesseract OCR executable for Windows.
Ensure language data files for English (eng), Hindi (hin), and Punjabi (pan) are included in your installation.
Generate your environment configuration file from the template:Copy-Item .env.example .env
Define the TESSERACT_CMD environment variable in .env to point to your executable path (e.g., C:\Program Files\Tesseract-OCR\tesseract.exe).


3. Configure API Credentials
Obtain valid keys and configure your BHASHINI User ID and ULCA API authentication keys within the .env file:BHASHINI_USER_ID=your_user_id

BHASHINI_API_KEY=your_api_key


4. Run the Application
Launch the Streamlit web application instance:streamlit run app.py

Access the user interface locally at http://localhost:8501.


Model Weights & External Datasets
Component / Engine
Integration Type
Source & Documentation
BHASHINI API Models
Ecosystem Integration
BHASHINI Ecosystem
AnuvaadHub Services
Managed Endpoint
Connected via API endpoints
Tesseract Language Models
Local Training Data
Tesseract OCR Repository










# SahAI — Accessible Language Companion

A Streamlit + Python prototype for English, Hindi and Punjabi. It has three modes:

- **Blind / low vision:** take or upload a menu photo, extract the text with OCR, edit mistakes, translate it with AnuvaadHub, and listen to it.
- **Deaf / hard of hearing:** record nearby speech, turn it into text, and translate it for reading.
- **Non-speaking / speech difficulty:** type a message, optionally translate it, then play it aloud.

The interface also has an optional voice-based mode selector. Browser speech synthesis reads prompts without API keys; AnuvaadHub handles speech recognition and text translation, and configured English, Hindi, and Punjabi TTS models generate playback audio. Languages without a configured model use available browser voices.

## 1. Run on Windows with VS Code

Open this folder in VS Code. In the terminal, run:

```powershell
py -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
```

If PowerShell blocks environment activation, you can use the VS Code terminal's `cmd` profile and run `.venv\Scripts\activate.bat`, or run `.venv\Scripts\python.exe -m pip install -r requirements.txt`.

## 2. Set up OCR (menu reader)

The camera captures the photo, but a separate OCR engine is needed to read text from it. Install **Tesseract OCR for Windows** and ensure its language data contains:

- `eng` — English
- `hin` — Hindi
- `pan` — Punjabi

If Windows cannot find Tesseract, copy `.env.example` to `.env` and set `TESSERACT_CMD` to the full path of `tesseract.exe`, commonly `C:\\Program Files\\Tesseract-OCR\\tesseract.exe`. The selected language's trained data must also be installed. OCR quality depends on lighting, image angle, font size and menu layout.

## 3. Configure AnuvaadHub speech

Speech recognition and text translation use the AnuvaadHub settings already present in `.env`. English, Hindi, and Punjabi text-to-speech use these settings:

```dotenv
ANUVAADHUB_TTS_EN_URL=https://canvas.iiit.ac.in/sandboxbeprod/generate_tts/67bca8b3e0b95a6a1ea34a93
ANUVAADHUB_TTS_EN_TOKEN=your_private_model_token
ANUVAADHUB_TTS_HI_URL=https://canvas.iiit.ac.in/sandboxbeprod/generate_tts/67bca89ae0b95a6a1ea34a92
ANUVAADHUB_TTS_HI_TOKEN=your_private_model_token
ANUVAADHUB_TTS_PA_URL=https://canvas.iiit.ac.in/sandboxbeprod/generate_tts/67bca99de0b95a6a1ea34a9b
ANUVAADHUB_TTS_PA_TOKEN=your_private_model_token
```

Keep each token in `.env`; do not paste it into chat or commit it.

## 4. Start the app

```powershell
streamlit run app.py
```

Streamlit will show a local URL, usually `http://localhost:8501`, and open it in your browser. Allow microphone and camera permissions when prompted. Streamlit's audio and camera inputs work best in a modern browser. On a deployed website, camera/microphone access generally requires HTTPS.

## 5. Test the flow

1. Open the home screen and tap **Listen to this instruction**.
2. Select each of the three modes.
3. In the blind/low-vision mode, upload a clear menu photo, extract text, correct it if needed, then try translation and speech.
4. In the deaf/hard-of-hearing mode, record a short sentence in the selected language, transcribe it, and translate it.
5. In the non-speaking mode, type a sentence, translate it (or use the original), and play it aloud.

## Notes / current prototype limits

- This is a working starter, not a certified assistive device. Keep a human-readable result on screen and verify OCR/translation before relying on it for prices, allergens, medicines, directions or emergencies.
- The app does not automatically play audio on page load because browsers commonly block unsolicited autoplay. Press **Generate and play [language] audio** to use a configured AnuvaadHub TTS model; generated audio appears in an audio player. Other languages use available browser voices until their TTS models are configured.
- Voice-based mode selection uses simple keyword matching after transcription. It can miss phrases or confuse language variants, so the three manual mode buttons remain available.
- The OCR implementation uses local Tesseract; speech API credentials do not install the OCR engine.
