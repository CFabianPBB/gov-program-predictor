FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

# Make sure directories exist
RUN mkdir -p templates static temp_uploads

ENV PORT=10000
CMD uvicorn src.gov_program_predictor.api.main:app --host 0.0.0.0 --port ${PORT:-10000}



FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

CMD ["uvicorn", "src.gov_program_predictor.api.main:app", "--host", "0.0.0.0", "--port", "10000"]
