import pandas as pd
import openai
import os
from typing import List, Dict, Any
import requests
from bs4 import BeautifulSoup

class ProgramPredictor:
    def __init__(self, excel_path: str, website_url: str):
        """
        Initialize the ProgramPredictor
        
        Args:
            excel_path: Path to Excel file containing staff data
            website_url: URL of the government department website
        """
        self.excel_path = excel_path
        self.website_url = website_url
        self.staff_data = None
        self.website_content = None
        
        # Initialize OpenAI key
        self.api_key = os.getenv('OPENAI_API_KEY')
        if not self.api_key:
            raise ValueError("OpenAI API key not found in environment variables")
        
        openai.api_key = self.api_key

    def _load_staff_data(self) -> None:
        """Load and process staff data from Excel file"""
        try:
            df = pd.read_excel(self.excel_path)
            
            # Group staff by position
            position_summary = df.groupby('Position').agg({
                'Department': 'count',
                'Skills': lambda x: ', '.join(set(filter(None, x)))
            }).reset_index()
            
            position_summary.columns = ['Position', 'Count', 'Combined_Skills']
            self.staff_data = position_summary
            
        except Exception as e:
            raise Exception(f"Error loading staff data: {str(e)}")

    def _fetch_website_content(self) -> None:
        """Fetch and process content from department website"""
        try:
            response = requests.get(self.website_url)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Extract text content
            text_content = []
            for tag in soup.find_all(['p', 'h1', 'h2', 'h3', 'li']):
                text_content.append(tag.get_text().strip())
            
            self.website_content = ' '.join(text_content)
            
        except Exception as e:
            raise Exception(f"Error fetching website content: {str(e)}")

    def _generate_prompt(self) -> str:
        """Generate prompt for OpenAI"""
        staff_summary = self.staff_data.to_string()
        
        prompt = f"""Based on the following department staff data and website content, suggest {self.num_programs} innovative government programs:

Staff Information:
{staff_summary}

Department Website Content Summary:
{self.website_content[:1000]}  # Limit website content length

For each program, provide:
1. Program Name
2. Description (2-3 sentences)
3. Estimated Budget Range
4. Implementation Timeline
5. Key Staff Positions Required

Format each program as a JSON object with keys: name, description, budget, timeline, required_positions"""

        return prompt

    def predict(self, num_programs: int = 3) -> List[Dict[str, Any]]:
        """
        Generate program predictions
        
        Args:
            num_programs: Number of programs to generate
            
        Returns:
            List of dictionaries containing program details
        """
        try:
            self.num_programs = num_programs
            
            # Load and process data
            self._load_staff_data()
            self._fetch_website_content()
            
            # Generate predictions using OpenAI
            response = openai.ChatCompletion.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are a government program planning expert."},
                    {"role": "user", "content": self._generate_prompt()}
                ],
                temperature=0.7,
                max_tokens=2000
            )
            
            # Parse response
            content = response.choices[0].message.content
            
            # Extract JSON from response
            start_idx = content.find('[')
            end_idx = content.rfind(']') + 1
            json_str = content[start_idx:end_idx]
            
            # Parse JSON into list of programs
            programs = eval(json_str)  # Using eval since OpenAI response might not be valid JSON
            
            return programs
            
        except Exception as e:
            raise Exception(f"Error in prediction process: {str(e)}")