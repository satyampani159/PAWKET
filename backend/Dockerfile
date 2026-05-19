FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 7860
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "7860"]
fastapi>=0.111.0
uvicorn[standard]>=0.29.0
python-dotenv>=1.0.0
scikit-learn>=1.4.0
joblib>=1.3.0
pandas>=2.0.0
numpy>=1.26.0
pydantic>=2.0.0
sqlalchemy
psycopg2-binary