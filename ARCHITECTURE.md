# Tony Stark Holographic Workshop - Architecture

## System Overview
A spatial-AI assistant that can see, understand, and teach about real-world objects using Meta Quest 3.

## Component Stack

### 1. Mixed Reality Foundation (Quest 3)
**Repository:** `mr-example-meta-openxr/`
- Unity-based MR framework with OpenXR
- Passthrough rendering
- Spatial anchors & hand tracking
- Base for holographic workspace

**Repository:** `QuestCameraKit/`
- Passthrough Camera API access
- Real-time RGB camera feed (1280×960 @ 30FPS)
- Depth sensor data (5mm accuracy)
- Object/environment scanning capabilities

### 2. Vision & Object Recognition
**Repository:** `OpenYOLO3D/`
- State-of-the-art open vocabulary 3D instance segmentation
- Identifies objects and parts from multi-view RGB images
- 16x faster than existing methods
- Perfect for real-time object identification

**Repository:** `Open3D-ML/`
- 3D point cloud processing
- Semantic segmentation of 3D meshes
- Geometry processing for digital twin creation
- Mesh manipulation for "exploded view" functionality

### 3. AI Assistant (Gemini Integration)
**Setup:** Python with Google Gemini API
- Multimodal understanding (vision + text)
- Object analysis and explanation
- Step-by-step repair/build instructions
- Natural language Q&A during work
- Voice interaction support
- Highlighting and annotation in 3D space

### 4. Procurement Agents (Fetch.ai)
**Repository:** `uAgents/`
- Autonomous agents for spec retrieval
- Parts ordering and supplier search
- Material procurement automation
- Integration with external APIs (suppliers, catalogs)

## Workflow

```
1. SCAN
   Quest 3 camera → QuestCameraKit → RGB + Depth data

2. RECOGNIZE
   3D scan → OpenYOLO3D → Object identification
                        → Open3D-ML → Digital twin mesh

3. UNDERSTAND
   Digital twin + image → Gemini API → Analysis + Instructions

4. INTERACT
   User voice/gesture → Gemini → Answers + 3D highlights
                              → Unity MR → Holographic overlays

5. PROCURE
   Part needed → uAgents → Spec lookup + Supplier search + Order
```

## Integration Points

### Unity ↔ Python Bridge
- Unity sends camera frames via socket/REST API
- Python processes with OpenYOLO3D + Gemini
- Returns JSON with object data, annotations, instructions
- Unity renders holograms and highlights

### Gemini Context
- Feed: 3D mesh, object images, depth map
- Prompt: "Analyze this {object}, explain parts, suggest repairs"
- Response: Structured JSON with part labels, instructions, diagrams

### uAgents Triggers
- Activated by Gemini when parts/specs needed
- Example: "Need torque spec for M8 bolt" → Agent fetches → Returns to Gemini → Displays in MR

## Next Steps
1. Set up Unity project from mr-example-meta-openxr
2. Configure Python environment for OpenYOLO3D + Open3D-ML
3. Create Gemini API integration script
4. Build Unity-Python communication bridge
5. Implement uAgents procurement workflows
6. Test full pipeline with sample object
