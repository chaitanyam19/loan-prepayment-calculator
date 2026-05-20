"""FastAPI loan prepayment calculator."""

from __future__ import annotations

from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel, Field
import math

app = FastAPI(title="Loan Prepayment Calculator API", version="1.0")


class LoanRequest(BaseModel):
    principal: float = Field(..., gt=0, description="Loan amount in rupees")
    annual_rate: float = Field(..., ge=0, description="Annual interest rate in percentage")
    tenure_years: float = Field(..., gt=0, description="Loan tenure in years")
    prepayment_month: int = Field(0, ge=0, description="Prepayment month (1-based). 0 to disable prepayment")
    prepayment_amount: float = Field(0.0, ge=0.0, description="Prepayment amount in rupees")
    method: str = Field("reduce tenure", description="Prepayment method: reduce tenure or reduce emi")


def calculate_emi(principal: float, annual_rate: float, months: int) -> float:
    if annual_rate == 0:
        return principal / months
    monthly_rate = annual_rate / 12 / 100
    return principal * monthly_rate * (1 + monthly_rate) ** months / ((1 + monthly_rate) ** months - 1)


def amortization_schedule(principal: float, annual_rate: float, months: int) -> list[dict[str, float]]:
    schedule = []
    monthly_rate = annual_rate / 12 / 100
    emi = calculate_emi(principal, annual_rate, months)
    balance = principal

    for month in range(1, months + 1):
        interest = balance * monthly_rate
        principal_paid = emi - interest
        balance -= principal_paid
        schedule.append(
            {
                "month": month,
                "interest": interest,
                "principal_paid": principal_paid,
                "emi": emi,
                "balance": max(balance, 0.0),
            }
        )
        if balance <= 0:
            break

    return schedule


def remaining_balance_after_months(principal: float, annual_rate: float, months: int, paid_months: int) -> float:
    schedule = amortization_schedule(principal, annual_rate, months)
    if paid_months >= len(schedule):
        return 0.0
    return schedule[paid_months - 1]["balance"]


def remaining_tenure(principal: float, annual_rate: float, emi: float) -> int:
    if principal <= 0:
        return 0
    if annual_rate == 0:
        return math.ceil(principal / emi)
    monthly_rate = annual_rate / 12 / 100
    numerator = math.log(emi / (emi - principal * monthly_rate))
    denominator = math.log(1 + monthly_rate)
    return math.ceil(numerator / denominator)


def format_months(months: int) -> str:
    years = months // 12
    remaining_months = months % 12
    if years and remaining_months:
        return f"{years} years {remaining_months} months"
    if years:
        return f"{years} years"
    return f"{months} months"


def build_loan_data(
    principal: float,
    annual_rate: float,
    tenure_years: float,
    prepayment_month: int = 0,
    prepayment_amount: float = 0.0,
    method: str = "reduce tenure",
) -> dict[str, object]:
    if method not in {"reduce tenure", "reduce emi"}:
        raise ValueError("method must be 'reduce tenure' or 'reduce emi'")

    months = int(round(tenure_years * 12))
    emi = calculate_emi(principal, annual_rate, months)
    total_payment = emi * months
    total_interest = total_payment - principal

    data: dict[str, object] = {
        "principal": principal,
        "annual_rate": annual_rate,
        "tenure_years": tenure_years,
        "months": months,
        "emi": emi,
        "total_interest": total_interest,
        "total_payment": total_payment,
        "formatted_tenure": format_months(months),
        "prepayment_month": prepayment_month,
        "prepayment_amount": prepayment_amount,
        "prepayment_method": method,
        "prepayment_applied": False,
        "message": "No valid prepayment applied.",
    }

    if prepayment_month < 1 or prepayment_month > months:
        data["message"] = "No valid prepayment will be applied."
        return data

    if prepayment_amount <= 0:
        data["message"] = "Prepayment amount must be greater than zero to apply prepayment."
        return data

    outstanding_before = remaining_balance_after_months(principal, annual_rate, months, prepayment_month)
    outstanding_after = max(outstanding_before - prepayment_amount, 0.0)
    remaining_payments = months - prepayment_month

    data.update(
        {
            "outstanding_before_prepayment": outstanding_before,
            "outstanding_after_prepayment": outstanding_after,
            "remaining_payments": remaining_payments,
            "formatted_remaining_payments": format_months(remaining_payments),
            "prepayment_applied": True,
        }
    )

    if outstanding_after <= 0:
        data["message"] = "Your prepayment covers the remaining loan balance. Loan is fully repaid."
        return data

    if method == "reduce tenure":
        new_months = remaining_tenure(outstanding_after, annual_rate, emi)
        reduction = remaining_payments - new_months
        total_paid_after_prepayment = emi * new_months
        data.update(
            {
                "new_months": new_months,
                "formatted_new_months": format_months(new_months),
                "tenure_reduction_months": reduction,
                "new_emi": emi,
                "method_result": "reduce tenure",
            }
        )
    else:
        new_emi = calculate_emi(outstanding_after, annual_rate, remaining_payments)
        total_paid_after_prepayment = new_emi * remaining_payments
        data.update(
            {
                "new_emi": new_emi,
                "formatted_new_months": format_months(remaining_payments),
                "method_result": "reduce emi",
            }
        )

    total_paid_before_prepayment = emi * prepayment_month
    total_paid = total_paid_before_prepayment + prepayment_amount + total_paid_after_prepayment
    interest_paid = total_paid - principal

    data.update(
        {
            "total_paid_after_prepayment": total_paid_after_prepayment,
            "total_paid": total_paid,
            "interest_paid": interest_paid,
            "message": "Prepayment applied successfully.",
        }
    )

    return data


@app.get("/")
def root() -> dict[str, str]:
    return {
        "message": "Loan Prepayment Calculator API",
        "calculate": "/calculate?principal=100000&annual_rate=10&tenure_years=5",
        "docs": "/docs",
    }


@app.get("/calculate")
def calculate_get(
    principal: float = Query(..., gt=0),
    annual_rate: float = Query(..., ge=0),
    tenure_years: float = Query(..., gt=0),
    prepayment_month: int = Query(0, ge=0),
    prepayment_amount: float = Query(0.0, ge=0.0),
    method: str = Query("reduce tenure"),
) -> dict[str, object]:
    try:
        return build_loan_data(
            principal,
            annual_rate,
            tenure_years,
            prepayment_month,
            prepayment_amount,
            method,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@app.post("/calculate")
def calculate_post(request: LoanRequest) -> dict[str, object]:
    try:
        return build_loan_data(
            request.principal,
            request.annual_rate,
            request.tenure_years,
            request.prepayment_month,
            request.prepayment_amount,
            request.method,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
