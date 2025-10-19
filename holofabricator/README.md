# 🔧 HoloFabricator - Tony Stark Holographic Workshop

**Your AI-powered mixed reality assistant for scanning, understanding, and repairing any real-world object.**

## 🚀 Quick Start

### 1. Start the Python Backend

```bash
# Activate Python 3.11 environment
cd C:\Users\Xenn\Downloads\LUCIDIC
.\venv_py311\Scripts\activate

# Set your Gemini API key (get one at https://makersuite.google.com/app/apikey)
$env:GEMINI_API_KEY="your-api-key-here"

# Start the server
cd holofabricator\backend
python main.py
```

**Backend will run at:** http://localhost:8000

### 2. Open the WebXR App

**Option A: Simple HTTP Server**
```bash
cd holofabricator\webxr-app
python -m http.server 3000
```

**Option B: VS Code Live Server**
- Install "Live Server" extension in VS Code
- Right-click `index.html` → "Open with Live Server"

**App will open at:** http://localhost:3000 (or Live Server port)

### 3. Test in Browser

1. **Open Chrome** with Meta Immersive Web Emulator installed
2. **Navigate to** http://localhost:3000
3. **Press F12** → Go to "WebXR" tab
4. **Select** "Meta Quest 3" device
5. **Click** "Enter Mixed Reality" button

## ✨ Features

### Current Demo
- ✅ WebXR scene with holographic UI
- ✅ Floating 3D object preview
- ✅ AI backend integration ready
- ✅ Meta Quest 3 emulator support

### Next Steps to Add
- [ ] Real camera capture from Quest 3
- [ ] Gemini Vision object analysis
- [ ] 3D mesh scanning with depth data
- [ ] RATK integration (planes, anchors)
- [ ] Fetch.ai procurement agents
- [ ] OpenYOLO3D object recognition

## 📁 Project Structure

```
holofabricator/
├── backend/
│   └── main.py              # FastAPI + Gemini + Open3D
├── webxr-app/
│   └── index.html           # Three.js + WebXR app
└── README.md                # This file
```

## 🎮 Controls

**Desktop (Emulator):**
- Use WebXR DevTools to control headset position
- Simulate controller input for interactions

**Quest 3 (When you get it):**
- Look at objects to scan
- Trigger button to analyze
- Ask questions with voice

## 🔧 Configuration

### Gemini API Key
Get your free API key: https://makersuite.google.com/app/apikey

Set it before running backend:
```bash
# Windows PowerShell
$env:GEMINI_API_KEY="your-key"

# Windows CMD
set GEMINI_API_KEY=your-key

# Linux/Mac
export GEMINI_API_KEY="your-key"
```

## 🧪 Testing

**Test backend is running:**
```bash
curl http://localhost:8000
```

**Test in browser:**
- Click "Test AI Vision (Desktop)" button
- Check browser console for logs

## 📚 API Endpoints

- `GET /` - Status and info
- `POST /analyze` - Analyze object from image
- `POST /3d/process` - Process 3D scan
- `GET /parts/search` - Search for parts (uAgents)

## 🎯 Next Development Steps

1. **Add Camera Capture** - Grab frames from Quest passthrough
2. **Integrate RATK** - Add plane detection and anchors
3. **Connect Gemini** - Send images for analysis
4. **3D Reconstruction** - Use Open3D for mesh processing
5. **Smart Agents** - Implement Fetch.ai procurement

## 🐛 Troubleshooting

**Backend not starting?**
- Check Python 3.11 venv is activated
- Install missing packages: `pip install fastapi uvicorn google-generativeai`

**WebXR not working?**
- Install Meta Immersive Web Emulator extension
- Check browser console for errors
- Try Firefox with WebXR extension

**CORS errors?**
- Backend CORS is configured for `*` (all origins)
- Check backend is running on port 8000

## 📖 Documentation

- **RATK:** https://meta-quest.github.io/reality-accelerator-toolkit
- **Three.js:** https://threejs.org/docs/
- **Gemini API:** https://ai.google.dev/docs
- **WebXR:** https://developer.mozilla.org/en-US/docs/Web/API/WebXR_Device_API

---

**Built with:**
- Python 3.11 + FastAPI
- Three.js + WebXR
- Gemini AI
- Open3D + PyTorch
- Fetch.ai uAgents
