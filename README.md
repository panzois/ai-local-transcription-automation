# AI Local Transcription Automation

Local AI-powered transcription tool using OpenAI Whisper.
Includes chunking, progress tracking, ETA calculation and GUI.

## Features
- Local speech-to-text (Whisper)
- Chunking for long files
- Clean progress tracking
- Cancellation support
- macOS GUI (PySide6)

## Requirements
- Python 3.9+
- ffmpeg (brew install ffmpeg)

## Install

```bash
git clone <repo-url>
cd ai-local-transcription-automation
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python app/gui_app.py