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
    departments: str = Form(...),  # JSON string containing department details
    files: List[UploadFile] = File(...)  # List of uploaded files
):
    """
    Process multiple department submissions and generate program predictions
    
    Args:
        departments: JSON string containing list of department details
        files: List of uploaded Excel files containing staff data
    
    Returns:
        List of predictions for each department
    """
    try:
        # Parse departments JSON
        dept_data = json.loads(departments)
        
        # Validate input lengths match
        if len(dept_data) != len(files):
            return {"error": "Number of files does not match number of departments"}
        
        results = []
        
        # Process each department
        for i, (dept, file) in enumerate(zip(dept_data, files)):
            # Create temporary file to store upload
            with tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx') as tmp_file:
                # Write uploaded file content to temporary file
                content = await file.read()
                tmp_file.write(content)
                tmp_file.flush()
                
                try:
                    # Initialize predictor for this department
                    predictor = ProgramPredictor(
                        excel_path=tmp_file.name,
                        website_url=dept['url']
                    )
                    
                    # Generate predictions
                    programs = predictor.predict(int(dept['programs']))
                    
                    # Add results for this department
                    results.append({
                        "department": dept['name'],
                        "programs": programs
                    })
                    
                finally:
                    # Clean up temporary file
                    os.unlink(tmp_file.name)
        
        return results
    
    except Exception as e:
        return {"error": f"Error processing departments: {str(e)}"}

@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler for all unhandled errors"""
    return {"error": f"An unexpected error occurred: {str(exc)}"}

# Health check endpoint
@app.get("/health")
async def health_check():
    """Simple health check endpoint"""
    return {"status": "healthy"}