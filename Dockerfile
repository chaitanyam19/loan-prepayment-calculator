FROM python:3.12-slim

WORKDIR /app

COPY loan_prepayment_calculator.py .

RUN python3 -m compileall loan_prepayment_calculator.py

ENTRYPOINT ["python3", "loan_prepayment_calculator.py"]
