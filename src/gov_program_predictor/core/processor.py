from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
import pandas as pd
import os
from dotenv import load_dotenv
from pathlib import Path

# Load environment variables
load_dotenv()

class ProgramPredictor:
    def __init__(self, model_name="gpt-3.5-turbo"):
        self.llm = ChatOpenAI(
            model=model_name,
            temperature=0.7
        )
    
    def process_personnel_data(self, file_path: Path) -> tuple[pd.DataFrame, dict]:
        """Process personnel data from Excel file."""
        try:
            # Read the Excel file
            df = pd.read_excel(file_path)
            
            # Generate metadata about the file
            metadata = {
                'total_positions': len(df),
                'departments': df['Department'].unique().tolist(),
                'divisions': df['Division'].unique().tolist(),
                'unique_titles': df['Position Title'].nunique()
            }
            
            return df, metadata
            
        except Exception as e:
            print(f"Error processing file: {str(e)}")
            raise

    def predict_programs_for_department(self, df: pd.DataFrame, website_url: str, programs_per_department: int) -> str:
        """Predict programs based on personnel data and website."""
        try:
            # Create prompt for the LLM
            prompt = ChatPromptTemplate.from_template("""
            Based on the following department information and website:
            
            Personnel Data:
            {personnel_data}
            
            Website: {website_url}
            
            Generate {programs_per_department} detailed program descriptions that this department could realistically implement.
            For each program include:
            1. Program Name
            2. Description
            3. Key Positions involved
            4. Website Alignment (how it would be featured on the website)
            
            Format each program with clear section breaks.
            """)
            
            # Convert DataFrame to string representation
            personnel_str = df.to_string()
            
            # Create the chain and invoke it
            chain = prompt | self.llm
            
            result = chain.invoke({
                "personnel_data": personnel_str,
                "website_url": website_url,
                "programs_per_department": programs_per_department
            })
            
            return result.content
            
        except Exception as e:
            print(f"Error predicting programs: {str(e)}")
            raise

    def test_connection(self):
        """Test the connection to OpenAI."""
        prompt = ChatPromptTemplate.from_template(
            "Return the phrase 'Connection successful!' if you receive this message."
        )
        chain = prompt | self.llm
        return chain.invoke({})

# Test the processing
if __name__ == "__main__":
    predictor = ProgramPredictor()
    try:
        # First test the OpenAI connection
        response = predictor.test_connection()
        print("API Test result:", response)
        
        # Then test file processing
        # Replace 'your_file.xlsx' with your actual filename
        df, metadata = predictor.process_personnel_data(Path('your_file.xlsx'))
        
        # Show sample of the data
        print("\nFirst few rows of the data:")
        print(df.head())
        
    except Exception as e:
        print("Error:", str(e))
