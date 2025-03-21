# Setup Guide

## 1. Install Required Software

### Python Installation
1. Download Python 3.13 from the official website:
   - Go to [Python Downloads](https://www.python.org/downloads/)
   - Click on "Download Python 3.13.0"
   - Or use direct link: https://www.python.org/downloads/release/python-3130/
2. Run the installer
   - ✅ Important: Check "Add Python to PATH" during installation
   - Choose "Customize Installation"
   - Select all optional features
   - Install for all users

### Node.js Installation
1. Download Node.js from the official website:
   - Go to [Node.js Downloads](https://nodejs.org/)
   - Download the LTS (Long Term Support) version
2. Run the installer with default settings

### FFmpeg Installation (Required for audio processing)
1. Download FFmpeg:
   - Go to [FFmpeg Downloads](https://ffmpeg.org/download.html)
   - For Windows, use gyan.dev: https://www.gyan.dev/ffmpeg/builds/
   - Download "ffmpeg-release-full.7z"
2. Extract the archive
3. Add FFmpeg to System PATH:
   - Copy the path to the `bin` folder (e.g., `C:\ffmpeg\bin`)
   - Open System Properties → Advanced → Environment Variables
   - Edit Path variable
   - Add the FFmpeg bin path

## 2. Clone and Setup Project

1. Clone the repository:
bash
git clone [your-repository-url]
cd [repository-name]

bash
pip install -r requirements.txt
3. Install Node.js dependencies:
npm install


## 3. Configuration

1. Update paths in scripts if necessary:
   - Check Python path in `package.json`
   - Current path is: `C:/Users/Lingwing/AppData/Local/Programs/Python/Python313/python.exe`
   - Update this to match your Python installation path

2. Verify installation:
python --version # Should show Python 3.13.0
node --version # Should show your Node.js version
ffmpeg -version # Should show FFmpeg version

## 4. Usage

...

## Troubleshooting

Common issues and solutions:

1. **"Python is not recognized as an internal or external command"**
   - Make sure Python is added to PATH
   - Try restarting your computer

2. **FFmpeg related errors**
   - Verify FFmpeg is in system PATH
   - Try running `ffmpeg` in command prompt to check installation

3. **Module not found errors**
   - Try reinstalling dependencies:
   ```bash
   pip install -r requirements.txt --force-reinstall
   ```

## Vosk Model Setup

After installing dependencies, you need to download the Vosk model:

1. Download the model from https://alphacephei.com/vosk/models
2. Choose either:
   - `vosk-model-small-en-us-0.15` (smaller, faster, less accurate)
   - `vosk-model-en-us-0.22` (larger, slower, more accurate)
3. Extract the downloaded model
4. Place the extracted folder in your project directory
5. Rename it to `model` or update the path in your code to match the model folder name

## System Requirements

- Windows 10 or later
- Python 3.13
- Node.js (LTS version)
- At least 2GB of free disk space
- Internet connection for TTS services