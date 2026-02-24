# AI Local Transcription Automation

Developed by Panagiotis Zois  
MSc in Information & Communication Technology  
Focus: AI Integration • Business Process Automation • Systems Architecture

AI-powered local transcription system built with Python and OpenAI Whisper.

This project demonstrates how AI models can be integrated into real-world business workflows through automation, process orchestration, and desktop application development.

---

## 🎯 Project Purpose

This application was designed as a practical example of:

- AI model integration in business processes
- Process automation & orchestration
- Long-running task monitoring (progress & ETA)
- Desktop system interface development
- Production packaging & distribution

Rather than being a simple script wrapper, this project implements a full transcription pipeline with chunking, subprocess handling, cancellation logic, and real-time progress tracking.

---

## 🚀 Features

- Local AI speech-to-text (OpenAI Whisper)
- Automatic audio chunking for large files
- Real-time progress monitoring
- ETA estimation logic
- Cancellation support
- Desktop GUI (PySide6)
- macOS standalone build (via Releases)

---

## 🧠 Architecture Overview

The system is structured into clear layers:

**GUI Layer**
- PySide6 desktop interface
- User interaction & process control

**Processing Layer**
- Whisper model invocation via subprocess
- FFmpeg-based audio segmentation
- Time-based ETA calculation
- Progress estimation logic

**Automation Layer**
- Chunk orchestration
- Process lifecycle management
- Error handling & cancellation control

This mirrors real-world enterprise system patterns:
- Orchestration engines
- Batch processing
- Workflow automation
- Long-running job monitoring

---

## 🛠 Tech Stack

- Python 3.9+
- PySide6 (Qt GUI framework)
- OpenAI Whisper
- FFmpeg
- PyInstaller (macOS packaging)

---

## 📦 Installation (Run from Source – macOS)

```bash
git clone <repo-url>
cd ai-local-transcription-automation

python3 -m venv .venv
source .venv/bin/activate

pip install -r requirements.txt
brew install ffmpeg

python app/gui_app.py

```

## 💻 macOS Standalone App

A compiled macOS build is available under the Releases section.

Download the .zip, extract it, and open:

Panos Whisper.app

If macOS blocks the application:
Right-click → Open → Confirm.

---

## 📈 Why This Project Matters

This project demonstrates capabilities aligned with:
- Business Process Automation
- AI integration in operational workflows
- Systems thinking & architecture
- Enterprise-style job orchestration
- Tooling development for productivity improvement

It reflects the intersection of:
AI + Automation + Systems + Business Workflow Design

---

## 🔮 Future Improvements

- Multi-file batch processing
- Structured output formats (JSON / CSV)
- ERP/CRM integration hooks
- API version
- Performance benchmarking layer
- Windows & Linux builds

---

## 📄 License

MIT License
