# HoloFabricator - Real Integration Roadmap

## Current State: DEMO PHASE
**What works:** Basic WebXR scene with mock objects
**What's needed:** Connect all the pieces for real scanning

---

## 🔗 Complete Integration Pipeline

### Phase 1: Camera & Depth Capture (Quest 3 → WebXR)
**Status:** NOT STARTED

**What needs to happen:**
1. Use WebXR Camera Access API to get Quest 3 passthrough frames
2. Access depth data via WebXR Depth Sensing API
3. Capture multiple angles as user moves around object

**Code location:** `webxr-app/scanner.js` (needs to be created)

**APIs to use:**
```javascript
// Quest 3 camera access
navigator.xr.requestSession('immersive-ar', {
    requiredFeatures: ['camera-access', 'depth-sensing']
});

// Capture frames
const cameraTexture = session.getCameraTexture();
const depthInfo = frame.getDepthInformation(view);
```

---

### Phase 2: Send Data to Backend (WebXR → Python)
**Status:** SKELETON EXISTS

**What needs to happen:**
1. Capture RGB frames + depth data from Quest
2. Package as base64 images or binary data
3. POST to Python backend `/scan` endpoint
4. Backend receives and stores scan data

**Flow:**
```
Quest 3 → WebXR captures → JSON/Binary → FastAPI receives → Save to disk
```

**Files:**
- Frontend: `webxr-app/index.html` (add fetch calls)
- Backend: `backend/main.py` (add `/scan` endpoint)

---

### Phase 3: 3D Reconstruction (Python Backend)
**Status:** OPEN3D INSTALLED, NOT INTEGRATED

**What needs to happen:**
1. Take RGB images + depth → Create point cloud (Open3D)
2. Clean noise, filter outliers
3. Generate mesh from point cloud
4. Save as `.ply` or `.obj` file

**Code to write:**
```python
# backend/reconstruction.py
import open3d as o3d
import numpy as np

def create_point_cloud(rgb_images, depth_maps):
    # Convert depth maps to point cloud
    pcd = o3d.geometry.PointCloud()
    # ... Open3D processing
    return pcd

def create_mesh(point_cloud):
    # Ball pivoting or Poisson reconstruction
    mesh = o3d.geometry.TriangleMesh.create_from_point_cloud_ball_pivoting(pcd)
    return mesh
```

**Dependencies:**
- ✅ Open3D (installed)
- ✅ NumPy (installed)

---

### Phase 4: Object Recognition (Python Backend)
**Status:** OPENYOLO3D CLONED, NOT INTEGRATED

**What needs to happen:**
1. Load 3D mesh from Phase 3
2. Run OpenYOLO3D to identify object
3. Segment mesh into individual parts
4. Label each part with Gemini

**Code to write:**
```python
# backend/recognition.py
from OpenYOLO3D import model  # needs setup
import google.generativeai as genai

def identify_object(mesh_path):
    # Run OpenYOLO3D inference
    segments = model.segment(mesh_path)

    # Ask Gemini what each part is
    for segment in segments:
        label = genai.identify_part(segment.image)
        segment.name = label

    return segments
```

**Dependencies:**
- ✅ PyTorch (installed)
- ❌ OpenYOLO3D setup (needs installation from ./OpenYOLO3D)
- ✅ Gemini API (installed)

---

### Phase 5: Send Back to WebXR (Python → Quest 3)
**Status:** NOT STARTED

**What needs to happen:**
1. Backend processes scan → Returns JSON with:
   - 3D mesh URL or data
   - Part labels and positions
   - Exploded view coordinates
2. WebXR receives data
3. Load mesh into Three.js scene
4. Position parts at coordinates
5. Add interactive labels

**Response format:**
```json
{
    "object_name": "V6 Engine",
    "mesh_url": "/static/scans/engine_mesh.glb",
    "parts": [
        {
            "id": 1,
            "name": "Cylinder Block",
            "position": [0, 0, 0],
            "exploded_position": [0, 3, 0],
            "color": "#808080"
        }
    ]
}
```

---

### Phase 6: Interactive Controls (WebXR Controllers)
**Status:** NOT STARTED

**What needs to happen:**
1. Add controller input handlers
2. Trigger button → Explode/assemble
3. Point at part → Show label
4. Grip button → Grab and move part
5. Voice commands via Web Speech API

**Code to add:**
```javascript
// Get controllers
const controller1 = renderer.xr.getController(0);
controller1.addEventListener('selectstart', onSelectStart);
controller1.addEventListener('selectend', onSelectEnd);

function onSelectStart(event) {
    // Raycast to find part
    // Trigger action (explode/grab/analyze)
}
```

---

## 📊 What Works NOW vs What's NEEDED

| Feature | Demo (Now) | Real (Needed) |
|---------|-----------|---------------|
| **3D Scene** | ✅ Works | ✅ Done |
| **WebXR Support** | ✅ Works | ✅ Done |
| **Camera Access** | ❌ Mock cube | ❌ Need Quest 3 camera API |
| **Depth Sensing** | ❌ None | ❌ Need WebXR depth API |
| **3D Reconstruction** | ❌ Hardcoded shapes | ❌ Need Open3D pipeline |
| **Object Recognition** | ❌ None | ❌ Need OpenYOLO3D integration |
| **Part Segmentation** | ✅ Manual split | ❌ Need ML segmentation |
| **Gemini Analysis** | ✅ API ready | ⚠️ Need to call with images |
| **Exploded View** | ✅ Works in demo | ✅ Same logic applies |
| **Controller Input** | ❌ Mouse only | ❌ Need XR controller handlers |

---

## 🚀 Next Steps (Priority Order)

### Step 1: Set up OpenYOLO3D (High Priority)
**Why:** This is the core ML model for object recognition

**Tasks:**
1. Read OpenYOLO3D installation docs
2. Install dependencies in venv_py311
3. Download pretrained models
4. Test with sample 3D mesh
5. Create `backend/recognition.py`

**Time estimate:** 2-4 hours

---

### Step 2: Build 3D Reconstruction Pipeline (High Priority)
**Why:** Need to convert Quest scans to usable meshes

**Tasks:**
1. Create `backend/reconstruction.py`
2. Write point cloud generation
3. Write mesh creation
4. Test with sample depth maps
5. Add `/reconstruct` API endpoint

**Time estimate:** 2-3 hours

---

### Step 3: Add Camera Capture (Medium Priority)
**Why:** Need real data from Quest 3

**Tasks:**
1. Research WebXR Camera Access API docs
2. Add camera permission request
3. Capture frames in WebXR
4. Send to backend via POST
5. Test with Quest 3 emulator (limited)

**Time estimate:** 3-4 hours
**Note:** Full testing requires real Quest 3

---

### Step 4: Controller Interactions (Medium Priority)
**Why:** Makes it usable in VR

**Tasks:**
1. Add controller raycasting
2. Implement select/trigger handlers
3. Add grab-and-move for parts
4. Test in emulator

**Time estimate:** 1-2 hours

---

### Step 5: Gemini Integration (Low Priority - Easy)
**Why:** API is ready, just need to wire it up

**Tasks:**
1. Add image upload to `/analyze`
2. Call Gemini with mesh screenshots
3. Parse and display results
4. Add voice command support (optional)

**Time estimate:** 1 hour

---

## 🎯 Minimal Viable Product (MVP)

To get a **working demo** that actually scans and recognizes objects:

**Must Have:**
1. ✅ WebXR scene (DONE)
2. ❌ Open3D reconstruction (NEED)
3. ❌ OpenYOLO3D recognition (NEED)
4. ⚠️ Gemini analysis (50% done)
5. ✅ Exploded view (DONE in demo)

**Can Skip for MVP:**
- Real Quest 3 camera (use uploaded images instead)
- Controller interactions (use mouse/keyboard)
- Voice commands (use buttons)

---

## 🧪 Testing Without Quest 3

**Option 1: Desktop Upload**
- Skip camera capture
- Let user upload photos of object
- Process with Open3D + OpenYOLO3D
- Display results in 3D viewer

**Option 2: Sample Data**
- Use pre-captured scans
- Download sample 3D meshes
- Test full pipeline offline

**Option 3: Emulator Only**
- Use emulator to test UI/UX
- Mock the ML processing
- Validate user flow

---

## 💡 What Should We Build Next?

**Choose one:**

### A) **Full ML Pipeline First** (No Quest needed)
- Set up OpenYOLO3D
- Build reconstruction
- Test with uploaded images
- **Result:** Working AI, no VR yet

### B) **Full WebXR First** (Needs Quest 3)
- Camera capture
- Controller input
- Real MR experience
- **Result:** Working VR, mock AI

### C) **Hybrid Approach** (Recommended)
- Desktop web app for upload
- Process with real ML
- View in WebXR emulator
- **Result:** End-to-end demo

---

**Which path should we take?**
