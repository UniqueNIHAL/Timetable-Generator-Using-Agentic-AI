# Quick Commands Reference

## Local Development

### Start the Server
```bash
cd /home/nihal-ubuntu/Desktop/Development/Agentic-timetable-planner
uv run uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Access the Application
- **Web UI**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs

## Testing Chat-Based Timetable Generation

### Option 1: Chat Interface (NEW! ✨)
Just type in the chat:
```
"Create a timetable for Jain University, 3rd Sem with Cyber Security, Cloud Computing, and Mobile Application. 3 classes per week per subject, Monday to Friday, 7:50 AM to 11:40 AM, 50 minutes each"
```

The AI will generate and display the timetable automatically!

### Option 2: File Upload + Generate Button
1. Upload CSV files from `/data` folder
2. Click "Generate Timetable"
3. View results

## Quick Test
1. Server is running ✓
2. Open http://localhost:8000 in browser
3. Try chat: "Generate a timetable for Monday to Friday with 3 subjects"
4. See the magic! 🎓✨