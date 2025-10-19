# 🧪 Testing main_v3.py - Complete Guide

## ✅ What's NEW in v3:

1. **SQLite Database** - Scans persist across restarts
2. **Async Mesh Generation** - Non-blocking, faster response
3. **Status Polling** - Frontend automatically checks mesh status
4. **Chat History** - All conversations saved
5. **Health Checks** - `/health` endpoint

---

## 🚀 Step 1: Start Backend v3

```powershell
cd C:\Users\Xenn\Downloads\LUCIDIC
.\venv_py311\Scripts\activate
cd holofabricator\backend

# IMPORTANT: Make sure .env has your API key
python main_v3.py
```

**Expected output:**
```
✅ Gemini 2.5 Pro configured
============================================================
🚀 HoloFabricator Backend v3 - Production Ready
============================================================
✅ Gemini 2.5 Pro configured
✅ Database ready - 0 existing scans loaded

📡 Server: http://localhost:8000
📚 API Docs: http://localhost:8000/docs
💾 Database: backend/holofabricator.db
🔄 Features: Async mesh, persistent storage, polling support
============================================================

INFO:     Started server process
INFO:     Waiting for application startup.
✅ Database initialized: holofabricator.db
✅ Database ready - 0 existing scans loaded
📦 Scans will persist across restarts
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000
```

---

## 🧪 Step 2: Test Database Creation

**Check that database file was created:**
```powershell
ls backend/holofabricator.db
```

**Should see:** `holofabricator.db` file exists

---

## 🌐 Step 3: Start Frontend

**New terminal:**
```powershell
cd C:\Users\Xenn\Downloads\LUCIDIC\holofabricator\webxr-app
python -m http.server 3000
```

**Open browser:** http://localhost:3000/scanner-app.html

---

## 📸 Step 4: Test Upload & Async Mesh

1. **Upload any image** (car, tool, phone, etc.)

2. **Watch the status messages:**
   ```
   ✅ "Uploading and analyzing..."
   ✅ "Analysis complete: [Object Name]"
   ✅ "Generating 3D mesh... (2s)"
   ✅ "Generating 3D mesh... (4s)"
   ✅ "Generating 3D mesh... (6s)"
   ...
   ✅ "3D mesh ready!"
   ```

3. **Backend console should show:**
   ```
   📸 New upload: 20251019_123456_789012
   🧠 Analyzing with Gemini 2.5 Pro...
   ✅ Analysis complete: [Object Name]
   💾 Saved to database: 20251019_123456_789012
   🎨 Starting 3D mesh generation (async)...
   🔄 Generating mesh for 20251019_123456_789012...
   ✅ Mesh ready: 20251019_123456_789012 → 20251019_123456_789012_mesh.ply
   ```

---

## 🔄 Step 5: Test Persistence (CRITICAL)

1. **Upload an image** (note the object name)

2. **Stop the server** (Ctrl+C in backend terminal)

3. **Restart the server:**
   ```powershell
   python main_v3.py
   ```

4. **Check startup message:**
   ```
   ✅ Database ready - 1 existing scans loaded
   📦 Scans will persist across restarts
   ```

5. **Test API:**
   Open: http://localhost:8000/scans

   **Should see your previous scan!**

---

## 💬 Step 6: Test Chat

1. Upload an object
2. Wait for mesh to be ready
3. In chat box, ask: "How does this work?"
4. **Watch backend console:**
   ```
   🧠 Chat query for scan_id
   ✅ Chat response generated
   💾 Chat saved to database
   ```

---

## 🩺 Step 7: Health Checks

**Visit:** http://localhost:8000/health

**Should return:**
```json
{
  "status": "healthy",
  "gemini": "configured",
  "database": "connected"
}
```

**Visit:** http://localhost:8000/

**Should show all features enabled**

---

## ✅ Success Criteria

| Test | Expected Result | Pass/Fail |
|------|----------------|-----------|
| Server starts without errors | ✅ See startup banner | ⬜ |
| Database file created | ✅ holofabricator.db exists | ⬜ |
| Image upload succeeds | ✅ Immediate response | ⬜ |
| Analysis completes | ✅ Object identified | ⬜ |
| Mesh generates async | ✅ Status updates appear | ⬜ |
| Mesh loads in 3D viewer | ✅ 3D model visible | ⬜ |
| Server restart | ✅ Scans still visible | ⬜ |
| Chat works | ✅ Gemini answers questions | ⬜ |
| /health endpoint | ✅ Returns healthy status | ⬜ |

---

## 🐛 Troubleshooting

### "Port 8000 already in use"
```powershell
# Find and kill process
netstat -ano | findstr :8000
taskkill /F /PID <number>
```

### "Database locked"
- Close any SQLite browser tools
- Restart server

### "Mesh never becomes ready"
- Check backend console for errors
- Look for "❌ Mesh generation failed"
- Try with a clearer, well-lit image

### "No Gemini response"
- Check `.env` has valid API key
- Verify: `GEMINI_API_KEY=AIza...` (no quotes, no spaces)
- Restart server after editing `.env`

---

## 📊 What To Check

### In Browser DevTools (F12 → Console):
```javascript
// Should see polling messages
"Polling for mesh status..."
"Mesh status: processing"
"Mesh status: ready"
```

### In Backend Console:
```
✅ All green checkmarks
No ❌ red X marks
Mesh generation completes
Database saves confirmed
```

### In Database:
```powershell
# Optional: View database
sqlite3 backend/holofabricator.db
.tables
SELECT * FROM scans;
.exit
```

---

## 🎯 Final Verification

**Restart test (THE BIG ONE):**

1. Upload 3 different objects
2. Wait for all meshes to complete
3. Stop server (Ctrl+C)
4. Restart: `python main_v3.py`
5. Check: http://localhost:8000/scans
6. **Should show all 3 scans!** ✅

If you see all 3 scans after restart: **🎉 100% SUCCESS**

---

## 📝 Notes

- First mesh generation may take 30-60 seconds
- Polling happens every 2 seconds
- Max wait time: 2 minutes
- Database grows with each scan (this is normal)
- Each scan creates: 1 DB entry + 1 image + 1 mesh file

---

**Ready to test? Start with Step 1!**
