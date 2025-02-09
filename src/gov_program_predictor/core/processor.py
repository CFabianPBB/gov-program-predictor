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
            print(f"Reading file: {file_path}")
            df = pd.read_excel(file_path)
            
            # Clean column names by stripping whitespace and handling special characters
            df.columns = df.columns.str.strip().str.replace('\n', ' ').str.replace('\r', '')
            print("Cleaned column names:", df.columns.tolist())
            
            # Print debug information
            print("Available columns:", df.columns.tolist())
            print("First few rows of data:")
            print(df.head())
            print("\nChecking for null values:")
            print(df.isnull().sum())
            
            # Basic data validation
            required_columns = ['Department', 'Division', 'Position Name']
            print("Required columns:", required_columns)
            print("Column name exact comparison:")
            for col in required_columns:
                print(f"Looking for '{col}' in columns:", [f"'{c}'" for c in df.columns])
                if col not in df.columns:
                    raise ValueError(f"Required column '{col}' not found in the Excel file")
                
            # Check for empty values
            if df['Department'].isnull().any():
                print("Warning: Found null values in Department column")
                # Fill null values or handle them as needed
                df['Department'] = df['Department'].fillna('Unknown')
            
            # Generate metadata about the file
            try:
                departments = df['Department'].unique().tolist()
                print("Unique departments found:", departments)
                
                metadata = {
                    'total_positions': len(df),
                    'departments': departments,
                    'divisions': df['Division'].unique().tolist(),
                    'unique_titles': df['Position Name'].nunique()
                }
                
                print("Generated metadata:", metadata)
                return df, metadata
                
            except Exception as e:
                print(f"Error while generating metadata: {str(e)}")
                raise
            
        except Exception as e:
            print(f"Error processing file: {str(e)}")
            print(f"File path: {file_path}")
            print(f"File exists: {file_path.exists()}")
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
3. Key Positions Involved
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
        file_path = Path('Sample Data - Personnel.xlsx')
        df, metadata = predictor.process_personnel_data(file_path)
        
        # Show sample of the data
        print("\nFirst few rows of the data:")
        print(df.head())
        
        # Print metadata
        print("\nMetadata:")
        print(metadata)
        
    except Exception as e:
        print("Error:", str(e))