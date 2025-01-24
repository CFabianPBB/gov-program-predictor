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

# Add the parent directory to the Python path so we can import the ProgramPredictor
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

# Create templates directory
templates_dir = Path(__file__).parent.parent.parent.parent / "templates"
templates_dir.mkdir(exist_ok=True)
templates = Jinja2Templates(directory=str(templates_dir))

# Create a temporary directory for file uploads
UPLOAD_DIR = Path(__file__).parent.parent.parent.parent / "temp_uploads"
UPLOAD_DIR.mkdir(exist_ok=True)

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
            website_content = predictor.fetch_website_content(website_url)
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
            positions = metadata['department_summaries'][dept]['unique_positions']
            predictions = predictor.predict_programs_for_department(
                positions,
                dept,
                website_content=website_content,
                num_programs=num_programs
            )
            # Clean up the predictions output for better display
            results[dept] = {
                'programs': predictions,
                'total_positions': metadata['department_summaries'][dept]['position_count'],
                'unique_positions': len(metadata['department_summaries'][dept]['unique_positions'])
            }
        
        return {
            "status": "success",
            "message": "Analysis complete",
            "note": "Website content unavailable - predictions based on position data only" if 'Note:' in website_content['department_specific'][0] else "All data processed successfully",
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
