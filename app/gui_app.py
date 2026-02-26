import sys, math, subprocess, time, shutil, glob, os
from pathlib import Path

from PySide6.QtCore import QThread, Signal, Qt, QSettings, QTimer, QUrl
from PySide6.QtWidgets import (
    QApplication, QWidget, QPushButton, QFileDialog, QVBoxLayout, QHBoxLayout,
    QLabel, QProgressBar, QTextEdit, QComboBox, QSpinBox, QCheckBox
)
from PySide6.QtGui import QDesktopServices


# ---------------------------
# Packaged-path helpers
# ---------------------------
def app_base_dir() -> Path:
    """
    When frozen (PyInstaller), sys.executable points to the .exe.
    Otherwise, use current working directory.
    """
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path.cwd()


def get_tool(name: str) -> str:
    """
    Find external binaries like ffmpeg/ffprobe.
    Priority:
      1) PATH
      2) next to the packaged exe (dist folder)
      3) common local locations (macOS / linux user bin)
    """
    # 1) PATH
    p = shutil.which(name)
    if p:
        return p

    base = app_base_dir()

    # 2) Next to exe (Windows release bundling)
    # On Windows we expect name.exe
    candidates = []
    if os.name == "nt":
        candidates.append(str(base / f"{name}.exe"))
    candidates.append(str(base / name))

    # 3) Common macOS locations
    candidates += [
        f"/opt/homebrew/bin/{name}",
        f"/usr/local/bin/{name}",
    ]

    # 4) user local bin (linux/mac)
    home = str(Path.home())
    candidates.append(f"{home}/.local/bin/{name}")

    for c in candidates:
        if Path(c).exists():
            return c

    # Friendly error
    if name in ("ffmpeg", "ffprobe"):
        raise FileNotFoundError(
            f"{name} not found.\n\n"
            f"This app requires FFmpeg.\n"
            f"- On Windows: make sure ffmpeg.exe & ffprobe.exe are next to the app .exe (in the same folder)\n"
            f"- On macOS: brew install ffmpeg\n"
        )

    raise FileNotFoundError(f"{name} not found.")


def ensure_ffmpeg_on_path():
    """
    If we bundled ffmpeg/ffprobe next to the exe, add that folder to PATH
    so subprocess calls work even when using just 'ffprobe' or 'ffmpeg'.
    """
    base = app_base_dir()
    if os.name == "nt":
        ffmpeg_exe = base / "ffmpeg.exe"
        ffprobe_exe = base / "ffprobe.exe"
        if ffmpeg_exe.exists() and ffprobe_exe.exists():
            os.environ["PATH"] = str(base) + os.pathsep + os.environ.get("PATH", "")
            return True
    return False


def run_capture(cmd):
    p = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    return p.returncode, p.stdout


def run_stream(cmd, on_line=None, cancel_check=None):
    """
    Run command with Popen, stream stdout line-by-line.
    Returns (rc, full_output, process, last_lines)
    """
    p = subprocess.Popen(
        cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1
    )
    full = []
    last_lines = []
    try:
        for line in p.stdout:
            raw = line.rstrip()
            full.append(line)

            if raw.strip():
                last_lines.append(raw)
                last_lines = last_lines[-25:]

            if raw.strip() and on_line:
                on_line(raw)

            if cancel_check and cancel_check():
                try:
                    p.terminate()
                    time.sleep(0.2)
                    if p.poll() is None:
                        p.kill()
                except:
                    pass
                break
    finally:
        try:
            p.stdout.close()
        except:
            pass

    rc = p.wait()
    return rc, "".join(full), p, last_lines


# ---------------------------
# Whisper helper (Python API)
# ---------------------------
def whisper_transcribe_to_text(audio_path: str, model_name: str, language: str = "el") -> str:
    """
    Uses whisper python package directly (no CLI).
    """
    import whisper  # lazy import (keeps startup faster)

    model = whisper.load_model(model_name)
    result = model.transcribe(audio_path, language=language, fp16=False, verbose=False)
    return (result.get("text") or "").strip()


# ---------------------------
# Worker
# ---------------------------
class TranscribeWorker(QThread):
    log = Signal(str)
    status = Signal(str)
    overall = Signal(int)        # 0..100
    eta = Signal(str)
    done = Signal(str)           # out_dir
    error = Signal(str)
    cancelled = Signal()

    def __init__(self, input_file: str, model: str, out_dir: str, use_chunking: bool, chunk_min: int):
        super().__init__()
        self.input_file = input_file
        self.model = model
        self.out_dir = Path(out_dir)
        self.use_chunking = use_chunking
        self.chunk_seconds = int(chunk_min) * 60
        self._cancel = False
        self._proc = None

    def request_cancel(self):
        self._cancel = True
        p = self._proc
        if p and p.poll() is None:
            try:
                p.terminate()
                time.sleep(0.2)
                if p.poll() is None:
                    p.kill()
            except:
                pass

    def is_cancelled(self):
        return self._cancel

    def get_duration_seconds(self) -> float:
        ffprobe = get_tool("ffprobe")
        rc, out = run_capture([
            ffprobe, "-v", "error",
            "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1",
            self.input_file
        ])
        if rc != 0:
            raise RuntimeError(out)
        return float(out.strip())

    def split_to_chunks(self, chunks_dir: Path):
        ffmpeg = get_tool("ffmpeg")
        chunks_dir.mkdir(parents=True, exist_ok=True)
        out_pattern = str(chunks_dir / "chunk_%03d.mp3")

        cmd = [
            ffmpeg,
            "-hide_banner", "-nostats", "-loglevel", "error",
            "-y", "-i", self.input_file,
            "-vn", "-ac", "1", "-ar", "16000",
            "-f", "segment", "-segment_time", str(self.chunk_seconds),
            out_pattern
        ]

        self.status.emit("Splitting audio into chunks…")

        def cancel_check():
            return self.is_cancelled()

        rc, out, p, last = run_stream(cmd, on_line=None, cancel_check=cancel_check)
        self._proc = p

        if self.is_cancelled():
            raise KeyboardInterrupt("Cancelled")

        if rc != 0:
            msg = "\n".join(last[-10:]) if last else out
            raise RuntimeError(f"ffmpeg failed.\n{msg}")

    def fmt_eta(self, seconds: float) -> str:
        seconds = int(max(0, seconds))
        h = seconds // 3600
        m = (seconds % 3600) // 60
        s = seconds % 60
        if h > 0:
            return f"ETA: {h:02d}:{m:02d}:{s:02d}"
        return f"ETA: {m:02d}:{s:02d}"

    def run(self):
        try:
            # Ensure ffmpeg/ffprobe bundled next to exe are usable
            ensure_ffmpeg_on_path()

            self.out_dir.mkdir(parents=True, exist_ok=True)

            # Output file (single final txt)
            in_stem = Path(self.input_file).stem
            out_txt = self.out_dir / f"{in_stem}.txt"
            if out_txt.exists():
                # avoid accidentally appending to old runs
                out_txt.unlink()

            self.status.emit("Reading duration…")
            total_sec = self.get_duration_seconds()

            # No chunking
            if not self.use_chunking:
                self.overall.emit(0)
                self.eta.emit("ETA: estimating…")
                self.status.emit("Transcribing…")

                if self.is_cancelled():
                    raise KeyboardInterrupt("Cancelled")

                text = whisper_transcribe_to_text(self.input_file, self.model, language="el")
                out_txt.write_text(text + "\n", encoding="utf-8")

                self.overall.emit(100)
                self.eta.emit("ETA: 00:00")
                self.done.emit(str(self.out_dir))
                return

            # Chunking path
            chunk_sec = self.chunk_seconds
            planned = max(1, math.ceil(total_sec / chunk_sec))
            self.log.emit(f"Splitting into ~{chunk_sec//60} min chunks (~{planned} chunks)…")

            chunks_dir = self.out_dir / "_chunks"
            self.split_to_chunks(chunks_dir)

            chunks = sorted(chunks_dir.glob("chunk_*.mp3"))
            total_chunks = max(1, len(chunks))

            start_all = time.time()

            for i, chunk in enumerate(chunks, start=1):
                if self.is_cancelled():
                    raise KeyboardInterrupt("Cancelled")

                chunk_start = time.time()
                audio_done_before = (i - 1) * chunk_sec
                audio_this_chunk = min(chunk_sec, max(0.0, total_sec - audio_done_before))

                self.status.emit(f"Processing chunk {i}/{total_chunks}")
                self.log.emit(f"Processing chunk {i}/{total_chunks} • {chunk.name}")

                overall_at_start = int((audio_done_before / max(1e-6, total_sec)) * 100)
                self.overall.emit(overall_at_start)
                self.eta.emit("ETA: estimating…")

                # Transcribe via python API
                text = whisper_transcribe_to_text(str(chunk), self.model, language="el")
                with out_txt.open("a", encoding="utf-8") as f:
                    if text:
                        f.write(text.strip() + "\n")

                # after chunk progress
                processed_audio = min(total_sec, i * chunk_sec)
                overall_frac = processed_audio / max(1e-6, total_sec)
                self.overall.emit(int(overall_frac * 100))

                elapsed = max(1e-6, time.time() - start_all)
                speed = processed_audio / elapsed
                remaining = max(0.0, total_sec - processed_audio)
                eta_sec = remaining / max(1e-6, speed)
                self.eta.emit(self.fmt_eta(eta_sec))

            self.overall.emit(100)
            self.eta.emit("ETA: 00:00")
            self.done.emit(str(self.out_dir))

        except KeyboardInterrupt:
            self.cancelled.emit()
        except Exception as e:
            self.error.emit(str(e))


# ---------------------------
# UI
# ---------------------------
class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Panos Whisper (Local)")
        self.resize(900, 520)

        self.settings = QSettings("Panos", "Panos Whisper")

        self.selected_file = None
        self.out_dir_path = str(Path.home() / "Desktop" / "WhisperOutputs")

        # Top label
        self.lbl_selected = QLabel("No file selected.")

        # Buttons
        self.btn_choose = QPushButton("Choose Video/Audio…")
        self.btn_start = QPushButton("Start")
        self.btn_cancel = QPushButton("Cancel")
        self.btn_open_output = QPushButton("Open Output Folder")
        self.btn_outdir = QPushButton("Output Folder…")

        self.btn_start.setEnabled(False)
        self.btn_cancel.setEnabled(False)

        # Model
        self.model_combo = QComboBox()
        self.model_combo.addItems(["tiny", "base", "small", "medium", "large", "turbo"])

        # Chunking
        self.chk_chunking = QCheckBox("Use chunking (recommended)")
        self.chk_chunking.setChecked(True)

        self.spin_chunk = QSpinBox()
        self.spin_chunk.setRange(1, 60)
        self.spin_chunk.setValue(10)

        self.lbl_chunk = QLabel("Chunk:")
        self.lbl_chunk_val = QLabel("min")

        # Output folder label
        self.lbl_outdir = QLabel(self.out_dir_path)

        # Status + ETA
        self.status_label = QLabel("Status: Idle")
        self.eta_label = QLabel("ETA: --:--")
        self.overall_label = QLabel("Overall: 0%")

        # Overall progress
        self.progress_overall = QProgressBar()
        self.progress_overall.setRange(0, 100)
        self.progress_overall.setValue(0)

        # Animated dots
        self._dots_timer = QTimer(self)
        self._dots_timer.timeout.connect(self._animate_status_dots)
        self._dots_state = 0
        self._base_status = "Idle"

        # Log box
        self.log_box = QTextEdit()
        self.log_box.setReadOnly(True)

        # Layout
        root = QVBoxLayout()
        root.addWidget(self.lbl_selected)

        row1 = QHBoxLayout()
        row1.addWidget(self.btn_choose)
        row1.addWidget(self.btn_start)
        root.addLayout(row1)

        row2 = QHBoxLayout()
        row2.addWidget(QLabel("Model:"))
        row2.addWidget(self.model_combo)
        row2.addSpacing(20)
        row2.addWidget(self.chk_chunking)
        row2.addWidget(self.lbl_chunk)
        row2.addWidget(self.spin_chunk)
        row2.addWidget(self.lbl_chunk_val)
        root.addLayout(row2)

        row3 = QHBoxLayout()
        row3.addWidget(self.btn_outdir)
        row3.addWidget(self.lbl_outdir, 1)
        root.addLayout(row3)

        root.addWidget(self.status_label)
        root.addWidget(self.eta_label)
        root.addWidget(self.overall_label)
        root.addWidget(self.progress_overall)
        root.addWidget(self.log_box, 1)

        row4 = QHBoxLayout()
        row4.addWidget(self.btn_cancel)
        row4.addWidget(self.btn_open_output)
        root.addLayout(row4)

        self.setLayout(root)

        # Signals
        self.btn_choose.clicked.connect(self.choose_file)
        self.btn_outdir.clicked.connect(self.choose_outdir)
        self.btn_start.clicked.connect(self.start_job)
        self.btn_cancel.clicked.connect(self.cancel_job)
        self.btn_open_output.clicked.connect(self.open_output_folder)

        # Chunk toggle behavior
        self.chk_chunking.toggled.connect(self.on_chunking_toggled)

        # Load settings
        self.load_settings()
        self.on_chunking_toggled(self.chk_chunking.isChecked())

    def on_chunking_toggled(self, checked: bool):
        self.spin_chunk.setEnabled(checked)

    def _animate_status_dots(self):
        self._dots_state = (self._dots_state + 1) % 4
        dots = "." * self._dots_state
        self.status_label.setText(f"Status: {self._base_status}{dots}")

    def set_running_ui(self, running: bool):
        if running:
            self._dots_state = 0
            self._dots_timer.start(350)
            QApplication.setOverrideCursor(Qt.WaitCursor)
        else:
            self._dots_timer.stop()
            try:
                QApplication.restoreOverrideCursor()
            except:
                pass

    def append_log(self, text: str):
        self.log_box.append(text)

    def set_controls_enabled(self, enabled: bool):
        self.btn_choose.setEnabled(enabled)
        self.btn_start.setEnabled(enabled and self.selected_file is not None)
        self.model_combo.setEnabled(enabled)
        self.chk_chunking.setEnabled(enabled)
        self.spin_chunk.setEnabled(enabled and self.chk_chunking.isChecked())
        self.btn_outdir.setEnabled(enabled)
        self.btn_cancel.setEnabled(not enabled)

    def choose_file(self):
        f, _ = QFileDialog.getOpenFileName(
            self,
            "Choose audio/video",
            str(Path.home() / "Downloads"),
            "Media files (*.mp4 *.m4a *.mp3 *.wav *.mov *.mkv);;All files (*.*)"
        )
        if not f:
            return

        self.selected_file = f
        self.lbl_selected.setText(f"Selected: {f}")
        self.btn_start.setEnabled(True)

    def choose_outdir(self):
        d = QFileDialog.getExistingDirectory(self, "Choose output folder", self.out_dir_path)
        if not d:
            return
        self.out_dir_path = d
        self.lbl_outdir.setText(d)
        self.save_settings()

    def open_output_folder(self):
        out_dir = Path(self.out_dir_path)
        out_dir.mkdir(parents=True, exist_ok=True)
        QDesktopServices.openUrl(QUrl.fromLocalFile(str(out_dir)))

    def cancel_job(self):
        if getattr(self, "worker", None):
            self.append_log("Cancelling…")
            self.worker.request_cancel()

    def start_job(self):
        if not self.selected_file:
            return

        self.log_box.clear()
        self.progress_overall.setValue(0)
        self.eta_label.setText("ETA: estimating…")

        self.set_controls_enabled(False)
        self.set_status_text("Transcribing…")
        self.set_running_ui(True)

        model = self.model_combo.currentText()
        use_chunking = self.chk_chunking.isChecked()
        chunk_min = int(self.spin_chunk.value())

        self.save_settings()

        self.worker = TranscribeWorker(
            input_file=self.selected_file,
            model=model,
            out_dir=self.out_dir_path,
            use_chunking=use_chunking,
            chunk_min=chunk_min
        )

        self.worker.log.connect(self.append_log)
        self.worker.status.connect(self.set_status_text)
        self.worker.overall.connect(self.on_overall_update)
        self.worker.eta.connect(self.eta_label.setText)

        self.worker.done.connect(self.on_done)
        self.worker.error.connect(self.on_error)
        self.worker.cancelled.connect(self.on_cancelled)

        self.worker.start()

    def set_status_text(self, s: str):
        self._base_status = s.replace("…", "").replace("...", "").strip()
        self.status_label.setText(f"Status: {self._base_status}")

    def on_overall_update(self, v: int):
        self.progress_overall.setValue(v)
        self.overall_label.setText(f"Overall: {v}%")

    def on_done(self, out_dir: str):
        self.append_log("Done ✅")
        self._base_status = "Done ✅"
        self.status_label.setText("Status: Done ✅")
        self.progress_overall.setValue(100)
        self.eta_label.setText("ETA: 00:00")

        self.set_running_ui(False)
        self.set_controls_enabled(True)

    def on_error(self, msg: str):
        self.append_log(f"ERROR: {msg}")
        self._base_status = "Error ❌"
        self.status_label.setText("Status: Error ❌")

        self.set_running_ui(False)
        self.set_controls_enabled(True)

    def on_cancelled(self):
        self.append_log("Cancelled.")
        self._base_status = "Cancelled"
        self.status_label.setText("Status: Cancelled")

        self.set_running_ui(False)
        self.set_controls_enabled(True)

    def load_settings(self):
        model = self.settings.value("model", "small")
        chunking = self.settings.value("chunking", True, type=bool)
        chunk_min = self.settings.value("chunk_min", 10, type=int)
        out_dir = self.settings.value("out_dir", self.out_dir_path)

        i = self.model_combo.findText(model)
        if i >= 0:
            self.model_combo.setCurrentIndex(i)

        self.chk_chunking.setChecked(chunking)
        self.spin_chunk.setValue(int(chunk_min))
        self.out_dir_path = str(out_dir)
        self.lbl_outdir.setText(self.out_dir_path)

    def save_settings(self):
        self.settings.setValue("model", self.model_combo.currentText())
        self.settings.setValue("chunking", self.chk_chunking.isChecked())
        self.settings.setValue("chunk_min", int(self.spin_chunk.value()))
        self.settings.setValue("out_dir", self.out_dir_path)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    w = MainWindow()
    w.show()
    sys.exit(app.exec())
