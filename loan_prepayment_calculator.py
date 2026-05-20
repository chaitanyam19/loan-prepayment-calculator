"""Loan prepayment calculator.

This script computes EMI, amortization schedule, and the effect of a one-time prepayment.
It supports:
- principal, annual interest rate, tenure
- prepayment month and amount
- prepayment method: reduce tenure or reduce EMI
"""

from __future__ import annotations

import math


def calculate_emi(principal: float, annual_rate: float, months: int) -> float:
    """Calculate the fixed monthly EMI for a loan."""
    if annual_rate == 0:
        return principal / months
    monthly_rate = annual_rate / 12 / 100
    return principal * monthly_rate * (1 + monthly_rate) ** months / ((1 + monthly_rate) ** months - 1)


def amortization_schedule(principal: float, annual_rate: float, months: int) -> list[dict[str, float]]:
    """Build a monthly amortization schedule for the loan."""
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
    """Return the outstanding balance after a given number of EMI payments."""
    schedule = amortization_schedule(principal, annual_rate, months)
    if paid_months >= len(schedule):
        return 0.0
    return schedule[paid_months - 1]["balance"]


def remaining_tenure(principal: float, annual_rate: float, emi: float) -> int:
    """Compute the number of remaining months for a loan given a fixed EMI."""
    if principal <= 0:
        return 0
    if annual_rate == 0:
        return math.ceil(principal / emi)
    monthly_rate = annual_rate / 12 / 100
    numerator = math.log(emi / (emi - principal * monthly_rate))
    denominator = math.log(1 + monthly_rate)
    return math.ceil(numerator / denominator)


def format_currency(value: float) -> str:
    return f"Rs - {value:,.2f}"


def format_months(months: int) -> str:
    years = months // 12
    remaining_months = months % 12
    if years and remaining_months:
        return f"{years} years {remaining_months} months"
    if years:
        return f"{years} years"
    return f"{months} months"


def ask_float(prompt: str) -> float:
    while True:
        try:
            value = float(input(prompt).strip())
            if value < 0:
                raise ValueError
            return value
        except ValueError:
            print("Please enter a valid non-negative number.")


def ask_int(prompt: str) -> int:
    while True:
        try:
            value = int(input(prompt).strip())
            if value < 0:
                raise ValueError
            return value
        except ValueError:
            print("Please enter a valid non-negative integer.")


def main() -> None:
    print("Loan Prepayment Calculator")
    print("---------------------------")

    principal = ask_float("Loan amount: ")
    annual_rate = ask_float("Annual interest rate (percentage): ")
    tenure_years = ask_float("Loan tenure in years: ")
    months = int(round(tenure_years * 12))

    emi = calculate_emi(principal, annual_rate, months)
    total_payment = emi * months
    total_interest = total_payment - principal

    print(f"\nMonthly EMI: {format_currency(emi)}")
    print(f"Total interest over {months} months ({format_months(months)}): {format_currency(total_interest)}")

    prepayment_month = ask_int("Prepayment month number (1-based, 0 to skip): ")
    if prepayment_month < 1 or prepayment_month > months:
        print("No prepayment will be applied.")
        return

    prepayment_amount = ask_float("Prepayment amount: ")
    if prepayment_amount <= 0:
        print("No prepayment will be applied.")
        return

    method = input(
        "Prepayment method ('reduce tenure' or 'reduce emi'): "
    ).strip().lower()
    if method not in {"reduce tenure", "reduce emi"}:
        print("Unknown method. Defaulting to 'reduce tenure'.")
        method = "reduce tenure"

    outstanding_before = remaining_balance_after_months(principal, annual_rate, months, prepayment_month)
    outstanding_after = max(outstanding_before - prepayment_amount, 0.0)

    remaining_payments = months - prepayment_month

    if outstanding_after <= 0:
        print("\nYour prepayment covers the remaining loan balance. Loan is fully repaid.")
        return

    if method == "reduce tenure":
        new_months = remaining_tenure(outstanding_after, annual_rate, emi)
        print("\nPrepayment summary:")
        print(f"Outstanding balance before prepayment: {format_currency(outstanding_before)}")
        print(f"Outstanding balance after prepayment: {format_currency(outstanding_after)}")
        print(f"Original remaining months: {remaining_payments} ({format_months(remaining_payments)})")
        print(f"New remaining months with same EMI: {new_months} ({format_months(new_months)})")
        print(f"Tenure reduction: {remaining_payments - new_months} months")
    else:
        new_emi = calculate_emi(outstanding_after, annual_rate, remaining_payments)
        print("\nPrepayment summary:")
        print(f"Outstanding balance before prepayment: {format_currency(outstanding_before)}")
        print(f"Outstanding balance after prepayment: {format_currency(outstanding_after)}")
        print(f"Remaining months unchanged: {remaining_payments} ({format_months(remaining_payments)})")
        print(f"New EMI with same remaining tenure: {format_currency(new_emi)}")

    total_paid_before_prepayment = emi * prepayment_month
    total_paid_after_prepayment = emi * new_months if method == "reduce tenure" else new_emi * remaining_payments
    total_paid = total_paid_before_prepayment + prepayment_amount + total_paid_after_prepayment
    interest_paid = total_paid - principal

    print(f"Estimated total payment after prepayment: {format_currency(total_paid)}")
    print(f"Estimated total interest after prepayment: {format_currency(interest_paid)}")


if __name__ == "__main__":
    main()
