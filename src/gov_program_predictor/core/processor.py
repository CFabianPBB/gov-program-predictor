import pandas as pd
import openai
import os
from typing import List, Dict, Any
import requests
from bs4 import BeautifulSoup
import logging

class ProgramPredictor:
    def __init__(self, excel_path: str, website_url: str):
        """
        Initialize the ProgramPredictor with department data
        
        Args:
            excel_path: Path to Excel file containing staff data
            website_url: URL of the government department website
        """
        self.excel_path = excel_path
        self.website_url = website_url
        self.staff_data = None
        self.website_content = None
        
        # Set up logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
        
        # Initialize OpenAI key
        self.api_key = os.getenv('OPENAI_API_KEY')
        if not self.api_key:
            raise ValueError("OpenAI API key not found in environment variables")
        
        openai.api_key = self.api_key

    def _load_staff_data(self) -> None:
        """Load and process staff data from Excel file"""
        try:
            df = pd.read_excel(self.excel_path)
            required_columns = ['Position', 'Department', 'Skills']
            
            # Validate required columns
            missing_cols = [col for col in required_columns if col not in df.columns]
            if missing_cols:
                raise ValueError(f"Missing required columns: {missing_cols}")
            
            # Clean and process data
            df = df.fillna('')
            
            # Group staff by position
            position_summary = df.groupby('Position').agg({
                'Department': 'count',
                'Skills': lambda x: ', '.join(set(filter(None, x)))
            }).reset_index()
            
            position_summary.columns = ['Position', 'Count', 'Combined_Skills']
            self.staff_data = position_summary
            
        except Exception as e:
            self.logger.error(f"Error loading staff data: {str(e)}")
            raise

    def _fetch_website_content(self) -> None:
        """Fetch and process content from department website"""
        try:
            response = requests.get(self.website_url)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Extract relevant text content
            text_content = []
            for tag in soup.find_all(['p', 'h1', 'h2', 'h3', 'li']):
                text_content.append(tag.get_text().strip())
            
            self.website_content = ' '.join(text_content)
            
        except Exception as e:
            self.logger.error(f"Error fetching website content: {str(e)}")
            raise

    def _generate_prompt(self) -> str:
        """Generate prompt for OpenAI based on department data"""
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

Focus on programs that:
- Leverage existing staff skills and capabilities
- Address clear public needs
- Are feasible to implement
- Have measurable outcomes

Format each program as a JSON object with keys: name, description, budget, timeline, required_positions"""

        return prompt

    def _parse_ai_response(self, response: str) -> List[Dict[str, Any]]:
        """Parse and validate OpenAI response into structured format"""
        try:
            # Extract JSON from response if needed
            start_idx = response.find('[')
            end_idx = response.rfind(']') + 1
            json_str = response[start_idx:end_idx]
            
            programs = eval(json_str)  # Using eval as OpenAI response might not be valid JSON
            
            # Validate each program has required fields
            required_fields = ['name', 'description', 'budget', 'timeline']
            for program in programs:
                missing_fields = [field for field in required_fields if field not in program]
                if missing_fields:
                    raise ValueError(f"Program missing required fields: {missing_fields}")
            
            return programs
            
        except Exception as e:
            self.logger.error(f"Error parsing AI response: {str(e)}")
            raise

    def predict(self, num_programs: int = 3) -> List[Dict[str, Any]]:
        """
        Generate program predictions based on department data
        
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
            
            # Parse and validate response
            programs = self._parse_ai_response(response.choices[0].message.content)
            
            return programs
            
        except Exception as e:
            self.logger.error(f"Error in prediction process: {str(e)}")
            raise

    def validate_staff_requirements(self, programs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Validate that proposed programs have required staff available
        
        Args:
            programs: List of program dictionaries
            
        Returns:
            List of validated program dictionaries with staffing feasibility notes
        """
        available_positions = set(self.staff_data['Position'].str.lower())
        
        for program in programs:
            if 'required_positions' in program:
                required = set(pos.lower() for pos in program['required_positions'])
                missing = required - available_positions
                
                program['staffing_feasible'] = len(missing) == 0
                if missing:
                    program['staffing_gaps'] = list(missing)
        
        return programs