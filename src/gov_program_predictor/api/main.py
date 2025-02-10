from fastapi import FastAPI, File, Form, UploadFile, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
import json
from typing import List, Optional
import os
from pathlib import Path
import tempfile
from ..core.processor import ProgramPredictor

app = FastAPI()

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Set up template and static file serving
templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    """Serve the main application page"""
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/predict")
async def predict_programs(
    request: Request,
    departments: str = Form(...),
    files: List[UploadFile] = File(...)
):
    """
    Process multiple department submissions and generate program predictions
    """
    try:
        # Parse departments JSON
        dept_data = json.loads(departments)
        
        # Validate we have all required files
        if len(dept_data) > len(files):
            return JSONResponse(
                status_code=400,
                content={"error": "Missing files for some departments"}
            )
        
        results = []
        
        # Process each department
        for i, dept in enumerate(dept_data):
            if i >= len(files):
                break
                
            file = files[i]
            
            # Validate required fields
            if not all(key in dept for key in ['name', 'url', 'programs']):
                return JSONResponse(
                    status_code=400,
                    content={"error": f"Missing required fields for department {dept.get('name', f'#{i+1}')}"}
                )
            
            # Create temporary file
            with tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx') as tmp_file:
                content = await file.read()
                tmp_file.write(content)
                tmp_file.flush()
                
                try:
                    # Initialize predictor
                    predictor = ProgramPredictor(
                        excel_path=tmp_file.name,
                        website_url=dept['url']
                    )
                    
                    # Generate predictions
                    programs = predictor.predict(int(dept['programs']))
                    
                    # Add results
                    results.append({
                        "department": dept['name'],
                        "programs": programs
                    })
                    
                finally:
                    # Clean up temporary file
                    os.unlink(tmp_file.name)
        
        return JSONResponse(content=results)
    
    except json.JSONDecodeError:
        return JSONResponse(
            status_code=400,
            content={"error": "Invalid departments JSON format"}
        )
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"error": f"Server error: {str(e)}"}
        )

# Health check endpoint
@app.get("/health")
async def health_check():
    """Simple health check endpoint"""
    return {"status": "healthy"}