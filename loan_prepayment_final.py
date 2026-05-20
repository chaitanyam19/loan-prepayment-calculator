"""Non-interactive loan prepayment calculator.

This script accepts command-line arguments or can run as an HTTP service.
"""

from __future__ import annotations

import argparse
import http.server
import json
import math
import socketserver
import urllib.parse
from http import HTTPStatus


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


def build_loan_data(
    principal: float,
    annual_rate: float,
    tenure_years: float,
    prepayment_month: int = 0,
    prepayment_amount: float = 0.0,
    method: str = "reduce tenure",
) -> dict[str, object]:
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


def parse_args(args: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Compute EMI, loan balance, and prepayment impact without interactive prompts or start an HTTP service."
    )
    parser.add_argument(
        "--serve",
        action="store_true",
        help="Start the HTTP service on the configured port.",
    )
    parser.add_argument("--port", type=int, default=8080, help="Port to run the HTTP service on.")
    parser.add_argument("--principal", type=float, help="Loan amount in rupees")
    parser.add_argument("--annual-rate", type=float, help="Annual interest rate (percentage)")
    parser.add_argument("--tenure-years", type=float, help="Loan tenure in years")
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
    parsed_args = parser.parse_args(args)

    if not parsed_args.serve:
        missing = [
            name
            for name in ("principal", "annual_rate", "tenure_years")
            if getattr(parsed_args, name) is None
        ]
        if missing:
            parser.error(
                "Missing required arguments: "
                + ", ".join(f"--{name.replace('_', '-')}" for name in missing)
            )
    return parsed_args


def render_cli_output(data: dict[str, object]) -> None:
    print("Loan Prepayment Calculator")
    print("---------------------------")
    print(f"Loan amount: {format_currency(data['principal'])}")
    print(f"Annual rate: {data['annual_rate']:.2f}%")
    print(f"Tenure: {data['months']} months ({data['formatted_tenure']})")
    print(f"Monthly EMI: {format_currency(data['emi'])}")
    print(f"Total interest over {data['months']} months ({data['formatted_tenure']}): {format_currency(data['total_interest'])}")

    if not data["prepayment_applied"]:
        print(f"\n{data['message']}")
        return

    print("\nPrepayment summary:")
    print(f"Outstanding balance before prepayment: {format_currency(data['outstanding_before_prepayment'])}")
    print(f"Outstanding balance after prepayment: {format_currency(data['outstanding_after_prepayment'])}")
    print(f"Prepayment month: {data['prepayment_month']} ({format_months(data['prepayment_month'])})")

    if data["method_result"] == "reduce tenure":
        print(f"Original remaining months: {data['remaining_payments']} ({data['formatted_remaining_payments']})")
        print(f"New remaining months with same EMI: {data['new_months']} ({data['formatted_new_months']})")
        print(f"Tenure reduction: {data['tenure_reduction_months']} months")
    else:
        print(f"Remaining months unchanged: {data['remaining_payments']} ({data['formatted_remaining_payments']})")
        print(f"New EMI with same remaining tenure: {format_currency(data['new_emi'])}")

    print(f"Estimated total payment after prepayment: {format_currency(data['total_paid'])}")
    print(f"Estimated total interest after prepayment: {format_currency(data['interest_paid'])}")


def format_json(value: object) -> str:
    return json.dumps(value, indent=2)


def parse_request_params(params: dict[str, list[str]]) -> dict[str, object]:
    def get(name: str, cast, required: bool = False, default=None):
        values = params.get(name)
        if values is None or not values:
            if required:
                raise ValueError(f"Missing required parameter: {name}")
            return default
        value = values[0]
        try:
            return cast(value)
        except ValueError:
            raise ValueError(f"Invalid value for {name}: {value}")

    return {
        "principal": get("principal", float, required=True),
        "annual_rate": get("annual_rate", float, required=True),
        "tenure_years": get("tenure_years", float, required=True),
        "prepayment_month": get("prepayment_month", int, default=0),
        "prepayment_amount": get("prepayment_amount", float, default=0.0),
        "method": get("method", str, default="reduce tenure"),
    }


class LoanCalculatorHandler(http.server.BaseHTTPRequestHandler):
    def do_GET(self) -> None:
        parsed = urllib.parse.urlparse(self.path)
        if parsed.path != "/calculate":
            self.send_error(HTTPStatus.NOT_FOUND, "Use /calculate with query parameters")
            return

        try:
            request_params = urllib.parse.parse_qs(parsed.query)
            request_data = parse_request_params(request_params)
            response_data = build_loan_data(**request_data)
            response_body = json.dumps(response_data, indent=2).encode("utf-8")

            self.send_response(HTTPStatus.OK)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(response_body)))
            self.end_headers()
            self.wfile.write(response_body)
        except ValueError as exc:
            self.send_error(HTTPStatus.BAD_REQUEST, str(exc))

    def log_message(self, format: str, *args: object) -> None:
        return


def serve(port: int = 8080) -> None:
    handler = LoanCalculatorHandler
    with socketserver.TCPServer(("0.0.0.0", port), handler) as httpd:
        print(f"Serving loan calculator on http://0.0.0.0:{port}/calculate")
        httpd.serve_forever()


def main() -> None:
    args = parse_args()
    if args.serve:
        serve(args.port)
        return

    data = build_loan_data(
        args.principal,
        args.annual_rate,
        args.tenure_years,
        args.prepayment_month,
        args.prepayment_amount,
        args.method,
    )
    render_cli_output(data)


if __name__ == "__main__":
    main()
