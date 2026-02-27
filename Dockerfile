FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY src/ ./src/
COPY api/ ./api/
COPY fly6_data/ ./fly6_data/
ENV PYTHONPATH=/app
ENV ZILLOW_DATA_ROOT=/data/zillow
ENV ZILLOW_DB_PATH=/data/zillow/db/zillow.sqlite
ENV API_PORT=8471
EXPOSE 8471
CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8471"]
