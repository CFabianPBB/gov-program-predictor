from fastapi import FastAPI, File, Form, UploadFile
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
import json
from typing import List
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
async def read_root(request):
    """Serve the main application page"""
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/predict")
async def predict_programs(
    file: UploadFile = File(...),
    website_url: str = Form(...),
    num_programs: int = Form(...)
):
    """Generate program predictions based on department data"""
    try:
        # Create temporary file to store upload
        with tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx') as tmp_file:
            # Write uploaded file content
            content = await file.read()
            tmp_file.write(content)
            tmp_file.flush()
            
            try:
                # Initialize predictor
                predictor = ProgramPredictor(
                    excel_path=tmp_file.name,
                    website_url=website_url
                )
                
                # Generate predictions
                programs = predictor.predict(num_programs)
                
                return programs
                
            finally:
                # Clean up temporary file
                os.unlink(tmp_file.name)
    
    except Exception as e:
        return {"error": str(e)}

# Health check endpoint
@app.get("/health")
async def health_check():
    """Simple health check endpoint"""
    return {"status": "healthy"}