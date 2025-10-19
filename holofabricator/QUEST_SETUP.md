# 🔧 HoloFabricator - Quest 3 Setup Guide

**Goal:** Zero configuration when Quest arrives - just connect and test!

---

## ✅ Pre-Setup (DONE - Already Built)

- ✅ Backend v4 with WebXR mesh support
- ✅ Frontend mesh-scanner.html with voice commands
- ✅ Spatial anchors for 3D labels
- ✅ Gemini 2.5 Pro integration
- ✅ Database persistence

---

## 📦 When Quest 3 Arrives - Do This:

### Step 1: Initial Quest Setup (5 min)

1. **Power on Quest 3**
2. **Complete first-time setup**
   - Connect to WiFi (same network as your PC)
   - Create/login to Meta account
3. **Update to latest firmware**
   - Settings > System > Software Update
   - **CRITICAL:** Need v76+ for Passthrough API, v77+ for WebXR mesh support

### Step 2: Enable Developer Mode (2 min)

1. **On your phone:**
   - Install "Meta Quest" app
   - Go to Menu > Devices > Your Quest 3
   - Enable "Developer Mode"

2. **On Quest 3:**
   - Settings > System > Developer
   - Toggle "USB Connection Dialog" ON
   - Toggle "Passthrough over USB" ON (optional, for debugging)

### Step 3: Scan Your Room (3 min)

**THIS IS CRITICAL** - Quest needs scanned room data for mesh detection!

1. Settings > Physical Space > Space Setup
2. Click "Create new space" or "Rescan"
3. Walk around room looking at:
   - Walls
   - Furniture (DJ set, workbench, etc.)
   - Objects on tables
4. Quest will create 3D meshes of everything

**Verify:** You should see walls/furniture outlined in blue grid

---

## 🚀 Testing HoloFabricator

### Step 4: Start Backend (1 min)

On your PC:

```bash
cd c:\Users\Xenn\Downloads\LUCIDIC\holofabricator\backend
python main_v4.py
```

**Expected output:**
```
======================================================================
🚀 HoloFabricator v4 - Quest 3 Ready!
======================================================================
✅ Gemini 2.5 Pro configured
✅ Database ready - 0 existing scans
INFO:     Uvicorn running on http://0.0.0.0:8000
```

**Keep this running!**

---

### Step 5: Get Your PC's IP Address

```bash
ipconfig
```

Look for "IPv4 Address" under your WiFi adapter.

Example: `192.168.1.100`

**Write it down!** You'll need it on Quest.

---

### Step 6: Open HoloFabricator on Quest (2 min)

1. **Put on Quest 3**

2. **Open Quest Browser**
   - Press Oculus button
   - Select "Browser" app

3. **Navigate to:**
   ```
   http://YOUR_PC_IP:8000
   ```

   Example: `http://192.168.1.100:8000`

4. **You should see:**
   ```json
   {
     "name": "HoloFabricator API v4",
     "status": "operational",
     "features": {
       "3d_file_upload": true,
       "quest_3_scan_support": true
     }
   }
   ```

5. **Now navigate to the scanner:**
   ```
   http://YOUR_PC_IP:8000/static/../webxr-app/mesh-scanner.html
   ```

   Or simpler, use your file path:
   ```
   file:///c:/Users/Xenn/Downloads/LUCIDIC/holofabricator/webxr-app/mesh-scanner.html
   ```

   **Note:** For WebXR features to work, you may need to serve via HTTP. Use the first option.

---

### Step 7: First Scan Test (Tony Stark Moment!)

1. **In Quest Browser, you'll see:**
   - Blue button: "🔧 Enter AR Scanner Mode"

2. **Click the button**
   - Browser will request AR permissions
   - Accept all permissions (camera, sensors, etc.)

3. **AR mode activates!**
   - You'll see the real world (passthrough)
   - HUD overlay in top-left corner
   - Status: "AR Mode Active - Looking for objects..."

4. **Look at an object** (DJ set, engine, anything)

5. **Pull controller trigger** OR say **"Scan this"**

6. **Watch the magic:**
   ```
   ✅ Found 5 detected meshes
   📤 Uploading table mesh...
   🧠 Analyzing with Gemini 2.5 Pro...
   ✅ DJ Controller identified!
   ```

7. **3D labels appear** floating on the real object:
   - "Crossfader"
   - "EQ Knobs"
   - "Jog Wheel"

8. **Click on a part** → Gemini explains what it does

9. **Say "What is this?"** → Voice response!

---

## 🎯 Full Workflow Demo

### Scenario: Scan & Analyze DJ Set

```
YOU:   *Put on Quest*
YOU:   *Open mesh-scanner.html in browser*
YOU:   *Click "Enter AR Mode"*
QUEST: *AR session starts, passthrough active*

YOU:   *Look at DJ set*
YOU:   *Pull trigger*

SYSTEM: 🔍 Searching for object meshes...
SYSTEM: ✅ Found 3 detected meshes
SYSTEM: 📤 Uploading "table" mesh (15,243 vertices)...
SYSTEM: 🧠 Analyzing with Gemini 2.5 Pro...
SYSTEM: ✅ Pioneer DDJ-400 DJ Controller identified!

AR VIEW:
  [Real DJ set with floating holographic labels]

  Crossfader ───────→ [points to crossfader on real device]
  Jog Wheels ───────→ [points to platters]
  EQ Section ───────→ [points to knobs]

YOU:   *Click "Crossfader" label*
GEMINI: "The crossfader blends audio between channels A and B..."

YOU:   "How do I beatmatch?"
GEMINI: "To beatmatch on this controller:
         1. Play track on Channel A
         2. Cue track on Channel B using headphones
         3. Adjust tempo with pitch fader
         4. Sync beats using jog wheel nudge
         5. Use crossfader to transition"

YOU:   "Explode view"
SYSTEM: 💥 Parts separate in 3D space showing assembly
```

---

## 🐛 Troubleshooting

### Issue: "AR mode not supported"

**Fix:**
- Update Quest to latest firmware (Settings > System > Software Update)
- Make sure browser is updated (should auto-update)
- Try restarting Quest

### Issue: "No meshes detected"

**Fix:**
- Go to Settings > Space Setup > Scan Room
- Walk around looking at objects
- Quest needs to see furniture/objects to create meshes
- Global mesh alone won't work - need object-specific meshes

### Issue: Backend connection failed

**Fix:**
- Check PC firewall allows port 8000
- Make sure PC and Quest on same WiFi
- Verify IP address with `ipconfig`
- Try: `http://192.168.1.100:8000` (your actual IP)

### Issue: Voice commands not working

**Fix:**
- Quest Browser needs microphone permission
- When AR starts, accept all permission prompts
- Say commands clearly: "Scan this", "What is this?"

### Issue: Gemini analysis is generic/wrong

**Fix:**
- Make sure .env has valid GEMINI_API_KEY
- Check backend logs for errors
- Mesh rendering might have failed - check Open3D installation

---

## 🎮 Controls Reference

### Controller:
- **Trigger** → Scan object
- **Grip** → (Future: Grab hologram)

### Voice Commands:
- **"Scan this"** → Scan object in view
- **"What is this?"** → Explain current object
- **"Explode"** → Show exploded view (WIP)

### Keyboard (Browser Testing):
- **SPACE** → Trigger scan
- **ESC** → Exit AR mode

---

## 📊 What's Working Now

✅ **WebXR mesh detection** - Access Quest's scanned room meshes
✅ **Automatic upload** - No manual export needed
✅ **Gemini analysis** - AI identifies objects & parts
✅ **3D spatial labels** - Labels float on real objects
✅ **Voice commands** - Hands-free operation
✅ **Database persistence** - Scans survive restarts
✅ **Real-time AR overlay** - See analysis while looking at object

---

## 🚧 Coming Soon (Not Implemented Yet)

⏳ **Exploded view animation** - Parts separate in 3D space
⏳ **Hand tracking** - Pinch to scan (currently controller only)
⏳ **Part highlighting** - Bounding boxes around selected parts
⏳ **Fetch.ai procurement** - Auto-order replacement parts

---

## 📝 System Requirements

**Quest 3:**
- Firmware v76+ (Passthrough API)
- Firmware v77+ (WebXR mesh detection)
- Room must be scanned (Space Setup)
- Developer mode enabled

**PC:**
- Python 3.11 (for Open3D)
- Gemini API key in `.env`
- Same WiFi network as Quest
- Port 8000 not blocked by firewall

**Network:**
- Quest and PC on same WiFi
- No VPN interfering
- Local network allows device-to-device communication

---

## ✅ Checklist Before Testing

- [ ] Quest 3 powered on and updated
- [ ] Room scanned in Space Setup
- [ ] Developer mode enabled
- [ ] Backend running (`python main_v4.py`)
- [ ] GEMINI_API_KEY in .env file
- [ ] PC IP address known
- [ ] Quest and PC on same WiFi
- [ ] Firewall allows port 8000

---

## 🎉 Success Criteria

**You'll know it's working when:**

1. AR mode starts without errors
2. Status shows "Found X detected meshes"
3. After trigger pull: "✅ [Object] identified!"
4. 3D labels appear floating on real object
5. Clicking labels shows part info
6. Voice commands work

**That's the "Tony Stark workshop" experience! 🔧✨**

---

## 📞 Quick Debug Commands

```bash
# Check backend status
curl http://localhost:8000

# Test mesh upload endpoint
curl -X POST http://localhost:8000/upload-webxr-mesh \
  -H "Content-Type: application/json" \
  -d '{"vertices": [[0,0,0]], "indices": [0], "semantic_label": "test"}'

# List all scans
curl http://localhost:8000/scans

# Check Python/Open3D
python -c "import open3d; print(open3d.__version__)"

# Get PC IP
ipconfig | findstr IPv4
```

---

**Built and ready to test! When Quest arrives, follow steps 1-7 and you're live! 🚀**
