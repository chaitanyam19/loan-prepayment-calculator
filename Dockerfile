FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN python3 -m pip install --no-cache-dir -r requirements.txt

COPY loan_prepayment_fastapi.py .

EXPOSE 8080

ENTRYPOINT ["uvicorn", "loan_prepayment_fastapi:app", "--host", "0.0.0.0", "--port", "8080"]
