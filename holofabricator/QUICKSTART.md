# 🚀 HoloFabricator - Quick Start Guide

## 📋 Prerequisites

✅ Python 3.11 environment installed (`venv_py311`)
✅ All packages installed (done)
✅ Gemini API key (get from https://makersuite.google.com/app/apikey)

---

## 🔧 Setup (One-Time)

### Step 1: Add Your Gemini API Key

Open `holofabricator\.env` and add your API key:

```env
GEMINI_API_KEY=your-actual-api-key-here
```

### Step 2: Install python-dotenv

```bash
.\venv_py311\Scripts\activate
pip install python-dotenv pillow
```

---

## 🚀 Running the App

### Terminal 1: Start Backend

```bash
cd C:\Users\Xenn\Downloads\LUCIDIC
.\venv_py311\Scripts\activate
cd holofabricator\backend
python main_v2.py
```

**You should see:**
```
✅ Gemini 2.0 Flash configured
📡 Starting server on http://localhost:8000
```

### Terminal 2: Start Frontend

```bash
cd C:\Users\Xenn\Downloads\LUCIDIC\holofabricator\webxr-app
python -m http.server 3000
```

### Step 3: Open in Browser

Go to: **http://localhost:3000/scanner-app.html**

---

## 🎯 How to Use

### 1. Upload an Image
- Click the upload zone or drag & drop an image
- Any object photo works (tools, electronics, engines, etc.)

### 2. Gemini Analyzes
- Identifies the object
- Lists all parts and functions
- Generates 3D reconstruction
- Takes ~5-10 seconds

### 3. Explore in 3D
- Rotate: Mouse drag
- Zoom: Scroll wheel
- Click parts to highlight them
- Use control buttons (Explode, Rotate, etc.)

### 4. Ask Questions
- Bottom right chat box
- Ask anything about the object
- Gemini will highlight relevant parts
- Examples:
  - "How does this work?"
  - "What's this part called?"
  - "How do I fix it?"

---

## 🎨 Features

### Left Panel
- 📸 Upload images
- 📊 Scan metrics
- 🔍 Object details

### Center Panel
- 🎨 Interactive 3D viewer
- 💥 Exploded view controls
- 🔄 Auto-rotate
- 🖱️ Mouse controls

### Right Panel
- 📝 Part analysis
- 💬 AI chat interface
- ✨ Part highlighting

---

## 🧪 Test It!

**Try uploading:**
- A watch ⌚
- A car engine 🚗
- A laptop 💻
- Any tool 🔧
- Electronic device 📱

Gemini will identify parts and you can ask questions about it!

---

## 🐛 Troubleshooting

**Backend won't start:**
```bash
# Make sure venv is activated
.\venv_py311\Scripts\activate

# Install missing package
pip install python-dotenv pillow
```

**"GEMINI_API_KEY not set":**
- Check `.env` file exists in `holofabricator/`
- Make sure API key is on one line, no spaces
- Restart backend after adding key

**CORS errors:**
- Backend must be running on port 8000
- Frontend must be on port 3000
- Open http://localhost:3000/scanner-app.html (not file://)

**3D mesh not loading:**
- First scan might take longer
- Check browser console (F12) for errors
- Mesh generation works best with clear, well-lit photos

---

## 🎯 What's Actually Working

✅ **Image Upload** - Real file upload
✅ **Gemini 2.0 Flash** - Real AI analysis
✅ **Part Identification** - Actual part detection
✅ **3D Mesh Generation** - Real Open3D reconstruction
✅ **Interactive Chat** - Real conversation with Gemini
✅ **Part Highlighting** - Highlight relevant parts
✅ **3D Viewer** - Real Three.js scene

This is a **REAL working pipeline**, not a demo!

---

## 📚 Next Steps

Want to add:
- [ ] Multiple image scanning (better 3D)
- [ ] Fetch.ai procurement agents
- [ ] Export to Quest 3 WebXR
- [ ] OpenYOLO3D advanced segmentation
- [ ] Voice commands
- [ ] AR overlay mode

Let me know what to build next!
