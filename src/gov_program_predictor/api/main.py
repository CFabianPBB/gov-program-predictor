from fastapi import FastAPI, File, Form, UploadFile, Request
from fastapi.responses import HTMLResponse, JSONResponse
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
        
        if not isinstance(dept_data, list):
            return JSONResponse(
                status_code=400,
                content={"error": "Departments data must be a list"}
            )
        
        # Validate we have all required files
        if len(dept_data) != len(files):
            return JSONResponse(
                status_code=400,
                content={"error": f"Number of files ({len(files)}) does not match number of departments ({len(dept_data)})"}
            )
        
        results = []
        
        # Process each department
        for i, (dept, file) in enumerate(zip(dept_data, files)):
            # Validate required fields
            required_fields = ['name', 'url', 'programs']
            if not all(field in dept for field in required_fields):
                return JSONResponse(
                    status_code=400,
                    content={"error": f"Missing required fields for department {i+1}. Need: {required_fields}"}
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
                    num_programs = int(dept['programs'])
                    programs = predictor.predict(num_programs)
                    
                    # Add results
                    results.append({
                        "department": dept['name'],
                        "programs": programs
                    })
                    
                finally:
                    # Clean up temporary file
                    if os.path.exists(tmp_file.name):
                        os.unlink(tmp_file.name)
        
        return JSONResponse(content=results)
        
    except json.JSONDecodeError:
        return JSONResponse(
            status_code=400,
            content={"error": "Invalid JSON format in departments data"}
        )
    except ValueError as e:
        return JSONResponse(
            status_code=400,
            content={"error": str(e)}
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

# Error handler for all exceptions
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler for all unhandled errors"""
    return JSONResponse(
        status_code=500,
        content={"error": f"An unexpected error occurred: {str(exc)}"}
    )