from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class ProgramPredictor:
    def __init__(self, model_name="gpt-3.5-turbo"):
        self.llm = ChatOpenAI(
            model=model_name,
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
            
            print("\nFile processed successfully!")
            print(f"Found {metadata['total_positions']} positions")
            print(f"Found {len(metadata['departments'])} departments")
            print(f"Found {len(metadata['divisions'])} divisions")
            print(f"Found {metadata['unique_titles']} unique position titles")
            
            return df, metadata
            
        except Exception as e:
            print(f"Error processing file: {str(e)}")
            raise

    def test_connection(self):
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
