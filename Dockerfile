FROM python:3.12-slim

WORKDIR /app

COPY loan_prepayment_final.py .

RUN python3 -m compileall loan_prepayment_final.py

ENTRYPOINT ["python3", "loan_prepayment_final.py"]
