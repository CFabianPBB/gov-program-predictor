from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
import pandas as pd
import os
from dotenv import load_dotenv
from pathlib import Path
import requests
from bs4 import BeautifulSoup
import re

# Load environment variables
load_dotenv()

class ProgramPredictor:
    def __init__(self, model_name="gpt-3.5-turbo"):
        self.llm = ChatOpenAI(
            model=model_name,
            temperature=0.7
        )
    
    def test_connection(self):
        prompt = ChatPromptTemplate.from_template(
            "Return the phrase 'Connection successful!' if you receive this message."
        )
        chain = prompt | self.llm
        return chain.invoke({})
    
    def process_personnel_data(self, file_path: Path):
        try:
            # Read the Excel file
            df = pd.read_excel(file_path)
            
            # Clean column names (remove trailing spaces)
            df.columns = df.columns.str.strip()
            
            # Group by Department and get position counts
            dept_summary = df.groupby('Department').agg({
                'Position Name': ['count', 'unique']
            }).reset_index()
            
            # Generate metadata about the file
            metadata = {
                'total_positions': len(df),
                'departments': df['Department'].unique().tolist(),
                'divisions': df['Division'].unique().tolist(),
                'department_summaries': {
                    dept: {
                        'position_count': len(dept_df),
                        'unique_positions': dept_df['Position Name'].unique().tolist()
                    }
                    for dept, dept_df in df.groupby('Department')
                }
            }
            
            print("\nFile processed successfully!")
            print(f"\nFound {metadata['total_positions']} total positions")
            print(f"Found {len(metadata['departments'])} departments:")
            for dept in metadata['departments']:
                summary = metadata['department_summaries'][dept]
                print(f"\n{dept}:")
                print(f"  - {summary['position_count']} positions")
                print(f"  - {len(summary['unique_positions'])} unique position types")
            
            return df, metadata
            
        except Exception as e:
            print(f"Error processing file: {str(e)}")
            raise

    def fetch_website_content(self, url: str) -> dict:
        """
        Fetch and process content from a government website.
        Returns a dictionary of relevant content.
        """
        try:
            # Add headers to mimic a browser
            headers = {
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1'
            }
            # Fetch the webpage
            response = requests.get(url, headers=headers, verify=False)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Extract relevant content
            content = {
                'page_title': soup.title.string if soup.title else '',
                'main_content': [],
                'department_specific': []
            }
            
            # Look for main content
            main_content = soup.find_all(['p', 'h1', 'h2', 'h3', 'div'], class_=re.compile(r'content|main|text'))
            content['main_content'] = [elem.get_text(strip=True) for elem in main_content if elem.get_text(strip=True)]
            
            # Look specifically for finance-related content
            finance_content = soup.find_all(
                text=re.compile(r'finance|budget|grant|payment|bill', re.IGNORECASE)
            )
            content['department_specific'] = [text.strip() for text in finance_content if text.strip()]
            
            print(f"\nWebsite content processed successfully!")
            print(f"Found {len(content['main_content'])} content blocks")
            print(f"Found {len(content['department_specific'])} finance-related content blocks")
            
            return content
            
        except Exception as e:
            print(f"Error processing website: {str(e)}")
            raise

    def predict_programs_for_department(self, positions: list, department: str, website_content: dict = None, num_programs: int = 5):
        """Predict programs based on position titles and website content."""
        
        # Prepare the prompt with optional website content
        base_prompt = """
        Based on the following information about the {department}, suggest {num_programs} likely programs 
        that this department runs. Consider how these positions work together to deliver services.
        
        Position Titles:
        {positions}
        """
        
        if website_content:
            base_prompt += """
            
            Relevant Website Content:
            {website_content}
            """
        
        base_prompt += """
        
        For each program, provide:
        1. Program Name
        2. Program Description
        3. Key Positions Involved
        4. Alignment with Website Content (if available)
        
        Format your response as a numbered list with these components for each program.
        """
        
        prompt = ChatPromptTemplate.from_template(base_prompt)
        
        # Prepare the website content if available
        website_text = "\n".join(website_content['department_specific']) if website_content else ""
        
        chain = prompt | self.llm
        
        try:
            result = chain.invoke({
                "department": department,
                "positions": "\n".join([f"- {pos}" for pos in positions]),
                "num_programs": num_programs,
                "website_content": website_text
            })
            
            print(f"\nPredicted Programs for {department}:")
            print(result)
            return result
            
        except Exception as e:
            print(f"Error predicting programs: {str(e)}")
            raise

# Test the processing
if __name__ == "__main__":
    predictor = ProgramPredictor()
    try:
        # First process the personnel data
        df, metadata = predictor.process_personnel_data(Path('Sample Data - Personnel.xlsx'))
        
        # Get the website URL from user
        website_url = input("\nEnter the government organization's website URL: ")
        website_content = predictor.fetch_website_content(website_url)
        
        # Get number of programs from user
        while True:
            try:
                num_programs = int(input("\nHow many programs would you like to see per department? "))
                if num_programs > 0:
                    break
                print("Please enter a positive number")
            except ValueError:
                print("Please enter a valid number")
        
        # For each department, predict programs
        for dept in metadata['departments']:
            positions = metadata['department_summaries'][dept]['unique_positions']
            print(f"\n{'='*50}")
            print(f"Analyzing {dept}")
            print(f"{'='*50}")
            programs = predictor.predict_programs_for_department(
                positions, 
                dept,
                website_content=website_content,
                num_programs=num_programs
            )
            
    except Exception as e:
        print("Error:", str(e))
