# Panos AI Transcriber

AI-powered local transcription system with cross-platform production builds.

**Developed by Panagiotis Zois**  
*MSc in Information & Communication Technology*  
**Focus Areas:** AI Integration • Business Process Automation • Systems Architecture • ERP-Oriented Thinking

---

## Overview

Panos AI Transcriber is a fully local AI transcription desktop application designed to demonstrate how artificial intelligence can be integrated into structured, production-oriented workflows.

The project goes beyond a simple Whisper wrapper.  
It implements:

- Deterministic build pipelines  
- Cross-platform distribution  
- Chunk-based processing orchestration  
- Long-running job monitoring  
- Enterprise-style execution control  

**Latest Production Release:** `v1.1.0` (Cross-Platform)  
Available for **macOS** and **Windows (x64)**.

---

## 🎯 Project Purpose

This project was designed as a portfolio-grade demonstration of:

- AI model integration into operational workflows  
- Process orchestration & job lifecycle management  
- Desktop system engineering  
- Reproducible build pipelines  
- Cross-platform packaging discipline  

It reflects how AI tools can be embedded inside real business environments rather than used as standalone scripts.

---

## 🚀 Core Capabilities

- Fully local speech-to-text processing (no cloud dependency)  
- Automatic audio chunking for large files  
- Real-time progress monitoring  
- Estimated time calculation (ETA logic)  
- Cancellation & lifecycle control  
- Cross-platform standalone builds (macOS / Windows x64)  

---

## 🧠 Architecture Overview

The system follows a layered architecture:

### 1️⃣ GUI Layer
- PySide6 desktop interface  
- User interaction control  
- Job state visibility  

### 2️⃣ Processing Layer
- Whisper Python API integration  
- FFmpeg-based segmentation  
- Time-based performance estimation  
- Controlled execution environment  

### 3️⃣ Orchestration Layer
- Chunk scheduling  
- Job lifecycle management  
- Error handling & safe termination  
- Deterministic execution flow  

This structure mirrors real-world enterprise patterns such as:

- Batch processing systems  
- Orchestration engines  
- Workflow automation pipelines  
- Long-running background task monitoring  

---

## ⚙️ Technical Design Decisions

- Whisper invoked via Python API (not CLI subprocess)  
- CPU-first execution model  
- Fully local execution (no external API calls)  
- Bundled `ffmpeg` / `ffprobe` binaries  
- Deterministic macOS build script  
- Windows CI-based reproducible build pipeline  
- Semantic versioning for releases  

---

## 📦 Production Builds

Versioned cross-platform builds are available under **Releases**.

Current stable release:

**Panos AI Transcriber – v1.1.0**

Included assets:

- macOS standalone application  
- Windows standalone application (x64)  

No Python installation is required for end users.

---

## 🛠 Tech Stack

- Python 3.11  
- PySide6 (Qt GUI framework)  
- OpenAI Whisper  
- FFmpeg  
- PyInstaller  
- GitHub Actions (Windows CI pipeline)  

---

## 📊 Performance Notes

Performance scales with hardware capability.

Tested successfully on:

- Apple Silicon macOS  
- Legacy Intel i5 (4th Gen) systems (CPU-only execution)  

This demonstrates portability across hardware tiers and predictable scaling behavior.

---

## 💼 Business & Systems Perspective

This project demonstrates competencies aligned with:

- Business Process Automation  
- AI-enabled workflow integration  
- System lifecycle management  
- Enterprise-style orchestration design  
- Operational tooling development  
- Cross-platform deployment discipline  

It reflects the intersection of:

**AI + Systems Engineering + Automation + Business Workflow Design**

---

## 🔮 Roadmap / Future Enhancements

- Multi-file batch processing  
- Structured output formats (JSON / CSV)  
- ERP / CRM integration hooks  
- API-based version  
- Performance benchmarking module  
- Model selection options  
- Linux build pipeline  

---

## 📄 License

MIT License
