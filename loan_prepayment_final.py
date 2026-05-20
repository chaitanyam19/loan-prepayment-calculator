"""Non-interactive loan prepayment calculator.

This script accepts command-line arguments instead of interactive prompts.
"""

from __future__ import annotations

import argparse
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


def parse_args(args: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Compute EMI, loan balance, and prepayment impact without interactive prompts."
    )
    parser.add_argument("--principal", type=float, required=True, help="Loan amount in rupees")
    parser.add_argument("--annual-rate", type=float, required=True, help="Annual interest rate (percentage)")
    parser.add_argument("--tenure-years", type=float, required=True, help="Loan tenure in years")
    parser.add_argument(
        "--prepayment-month",
        type=int,
        default=0,
        help="Prepayment month number (1-based). Use 0 to disable prepayment.",
    )
    parser.add_argument(
        "--prepayment-amount",
        type=float,
        default=0.0,
        help="Prepayment amount in rupees.",
    )
    parser.add_argument(
        "--method",
        choices=["reduce tenure", "reduce emi"],
        default="reduce tenure",
        help="How to apply prepayment: reduce tenure or reduce emi.",
    )
    return parser.parse_args(args)


def main() -> None:
    args = parse_args()
    months = int(round(args.tenure_years * 12))
    emi = calculate_emi(args.principal, args.annual_rate, months)
    total_payment = emi * months
    total_interest = total_payment - args.principal

    print("Loan Prepayment Calculator")
    print("---------------------------")
    print(f"Loan amount: {format_currency(args.principal)}")
    print(f"Annual rate: {args.annual_rate:.2f}%")
    print(f"Tenure: {months} months ({format_months(months)})")
    print(f"Monthly EMI: {format_currency(emi)}")
    print(f"Total interest over {months} months ({format_months(months)}): {format_currency(total_interest)}")

    if args.prepayment_month < 1 or args.prepayment_month > months:
        print("\nNo valid prepayment will be applied.")
        return
    if args.prepayment_amount <= 0:
        print("\nPrepayment amount must be greater than zero to apply prepayment.")
        return

    outstanding_before = remaining_balance_after_months(args.principal, args.annual_rate, months, args.prepayment_month)
    outstanding_after = max(outstanding_before - args.prepayment_amount, 0.0)
    remaining_payments = months - args.prepayment_month

    if outstanding_after <= 0:
        print("\nYour prepayment covers the remaining loan balance. Loan is fully repaid.")
        return

    print("\nPrepayment summary:")
    print(f"Outstanding balance before prepayment: {format_currency(outstanding_before)}")
    print(f"Outstanding balance after prepayment: {format_currency(outstanding_after)}")
    print(f"Prepayment month: {args.prepayment_month} ({format_months(args.prepayment_month)})")

    if args.method == "reduce tenure":
        new_months = remaining_tenure(outstanding_after, args.annual_rate, emi)
        reduction = remaining_payments - new_months
        print(f"Original remaining months: {remaining_payments} ({format_months(remaining_payments)})")
        print(f"New remaining months with same EMI: {new_months} ({format_months(new_months)})")
        print(f"Tenure reduction: {reduction} months")
        total_paid_after_prepayment = emi * new_months
    else:
        new_emi = calculate_emi(outstanding_after, args.annual_rate, remaining_payments)
        print(f"Remaining months unchanged: {remaining_payments} ({format_months(remaining_payments)})")
        print(f"New EMI with same remaining tenure: {format_currency(new_emi)}")
        total_paid_after_prepayment = new_emi * remaining_payments

    total_paid_before_prepayment = emi * args.prepayment_month
    total_paid = total_paid_before_prepayment + args.prepayment_amount + total_paid_after_prepayment
    interest_paid = total_paid - args.principal

    print(f"Estimated total payment after prepayment: {format_currency(total_paid)}")
    print(f"Estimated total interest after prepayment: {format_currency(interest_paid)}")


if __name__ == "__main__":
    main()
