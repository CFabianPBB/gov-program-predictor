from fastapi import FastAPI, File, UploadFile, Form, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
import uvicorn
from pathlib import Path
import tempfile
import shutil
import sys
import os

# Add the parent directory to the Python path
sys.path.append(str(Path(__file__).parent.parent.parent))
from gov_program_predictor.core.processor import ProgramPredictor

app = FastAPI(title="Government Program Predictor")

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Get the absolute path to the project root
PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
TEMPLATES_DIR = PROJECT_ROOT / "templates"
STATIC_DIR = PROJECT_ROOT / "static"

# Ensure directories exist
TEMPLATES_DIR.mkdir(exist_ok=True)
STATIC_DIR.mkdir(exist_ok=True)
UPLOAD_DIR = PROJECT_ROOT / "temp_uploads"
UPLOAD_DIR.mkdir(exist_ok=True)

# Set up templates and static files
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse(
        "index.html",
        {"request": request}
    )

@app.post("/predict")
async def predict_programs(
    file: UploadFile = File(...),
    website_url: str = Form(...),
    num_programs: int = Form(...)
):
    # Save uploaded file
    temp_path = UPLOAD_DIR / file.filename
    with temp_path.open("wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    try:
        # Create predictor instance
        predictor = ProgramPredictor()
        
        # Process the file
        df, metadata = predictor.process_personnel_data(temp_path)
        
        # Try to get website content, but continue even if it fails
        try:
            website_content = {"url": website_url}
        except Exception as web_error:
            print(f"Warning: Could not fetch website content: {str(web_error)}")
            website_content = {
                'main_content': [],
                'department_specific': [
                    "Note: Website content could not be accessed. Predictions will be based on position data only."
                ]
            }

        # Generate predictions for each department
        results = {}
        for dept in metadata['departments']:
            dept_df = df[df['Department'] == dept]
            predictions = predictor.predict_programs_for_department(
                dept_df,
                website_url,
                num_programs
            )
            
            # Clean up the predictions output for better display
            results[dept] = {
                'programs': {'content': predictions},
                'total_positions': len(dept_df),
                'unique_positions': dept_df['Position Name'].nunique()
            }
        
        return {
            "status": "success",
            "message": "Analysis complete",
            "note": "Website content unavailable – predictions based on position data only" if 'Note:' in str(website_content) else "",
            "results": results,
            "metadata": {
                "total_positions": metadata['total_positions'],
                "departments": metadata['departments'],
                "departments_analyzed": len(metadata['departments'])
            }
        }
        
    except Exception as e:
        return {
            "status": "error",
            "message": str(e),
            "details": "An error occurred while processing your request. Please check your input data and try again."
        }
    
    finally:
        # Clean up
        if temp_path.exists():
            temp_path.unlink()

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)