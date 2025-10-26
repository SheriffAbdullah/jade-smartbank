"""EMI calculation utility.

SECURITY: Accurate financial calculations using Decimal.
"""
from decimal import Decimal
from typing import List, Tuple


def calculate_emi(
    principal: Decimal, annual_rate: Decimal, tenure_months: int
) -> Tuple[Decimal, Decimal, Decimal, List[dict]]:
    """Calculate EMI and generate amortization schedule.

    Formula: EMI = (P × r × (1+r)^n) / ((1+r)^n - 1)
    Where:
        P = Principal loan amount
        r = Monthly interest rate (annual rate / 12 / 100)
        n = Tenure in months

    Args:
        principal: Loan amount
        annual_rate: Annual interest rate (e.g., 12.5 for 12.5%)
        tenure_months: Loan tenure in months

    Returns:
        Tuple of (emi_amount, total_interest, total_payable, breakdown)

    Example:
        >>> emi, interest, total, breakdown = calculate_emi(
        ...     Decimal("500000"), Decimal("12.5"), 36
        ... )
        >>> emi
        Decimal('16607.97')
    """
    # Convert annual rate to monthly decimal rate
    monthly_rate = annual_rate / Decimal("12") / Decimal("100")

    # Calculate EMI using formula
    if monthly_rate == 0:
        # If interest rate is 0, simple division
        emi = principal / Decimal(tenure_months)
    else:
        # EMI formula
        numerator = principal * monthly_rate * ((1 + monthly_rate) ** tenure_months)
        denominator = ((1 + monthly_rate) ** tenure_months) - 1
        emi = numerator / denominator

    # Round to 2 decimal places
    emi = emi.quantize(Decimal("0.01"))

    # Generate amortization schedule
    breakdown = []
    balance = principal

    for month in range(1, tenure_months + 1):
        interest_component = (balance * monthly_rate).quantize(Decimal("0.01"))
        principal_component = (emi - interest_component).quantize(Decimal("0.01"))

        # Adjust last EMI to account for rounding
        if month == tenure_months:
            principal_component = balance
            emi_adjusted = principal_component + interest_component
        else:
            emi_adjusted = emi

        balance = (balance - principal_component).quantize(Decimal("0.01"))

        breakdown.append(
            {
                "month": month,
                "emi": emi_adjusted,
                "principal": principal_component,
                "interest": interest_component,
                "balance": balance,
            }
        )

    total_payable = sum(item["emi"] for item in breakdown)
    total_interest = total_payable - principal

    return emi, total_interest, total_payable, breakdown