#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

pkill -f "Panos AI Transcriber" || true

# Hard clean with attribute removal
if [ -d "dist" ]; then
  chmod -R u+w dist || true
  xattr -rc dist 2>/dev/null || true
  rm -rf dist 2>/dev/null || true
fi

if [ -d "build" ]; then
  chmod -R u+w build || true
  xattr -rc build 2>/dev/null || true
  rm -rf build 2>/dev/null || true
fi

rm -f ./*.spec 2>/dev/null || true

FFMPEG="$(python3 -c 'import shutil, pathlib, sys; p=shutil.which("ffmpeg"); print(pathlib.Path(p).resolve()) if p else sys.exit(1)')"
FFPROBE="$(python3 -c 'import shutil, pathlib, sys; p=shutil.which("ffprobe"); print(pathlib.Path(p).resolve()) if p else sys.exit(1)')"

python3 -m PyInstaller --noconfirm --clean --windowed \
  --name "Panos AI Transcriber" \
  --icon "./assets/panos_whisper_logo_last.icns" \
  --add-data "./assets:assets" \
  --add-binary "$FFMPEG:." \
  --add-binary "$FFPROBE:." \
  --collect-data whisper \
  --hidden-import whisper \
  ./app/gui_app.py

APP="dist/Panos AI Transcriber.app"

# Verify critical assets
test -f "$APP/Contents/Resources/whisper/assets/mel_filters.npz"
test -f "$APP/Contents/Frameworks/ffmpeg" -o -f "$APP/Contents/Resources/ffmpeg"
test -f "$APP/Contents/Frameworks/ffprobe" -o -f "$APP/Contents/Resources/ffprobe"

# Create release zip
rm -f "dist/Panos-AI-Transcriber-macOS.zip" 2>/dev/null || true
ditto -c -k --sequesterRsrc --keepParent "$APP" "dist/Panos-AI-Transcriber-macOS.zip"

echo "--------------------------------------------"
echo "BUILD SUCCESS"
echo "$APP"
echo "dist/Panos-AI-Transcriber-macOS.zip"
echo "--------------------------------------------"