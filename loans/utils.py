from decimal import Decimal, ROUND_HALF_UP


def quantize_decimal(value, precision="0.01"):
    return value.quantize(Decimal(precision), rounding=ROUND_HALF_UP)


def create_amortization_schedule(loan_amount, duration, interest_rate):
    loan_amount = Decimal(loan_amount)
    monthly_interest_rate = Decimal(interest_rate) / 12
    number_of_payments = duration * 12

    if interest_rate == 0:
        monthly_payment = loan_amount / number_of_payments
    else:
        monthly_payment = (
            loan_amount
            * monthly_interest_rate
            * (1 + monthly_interest_rate) ** number_of_payments
        ) / ((1 + monthly_interest_rate) ** number_of_payments - 1)

    amortization_schedule_yearly = []
    balance = loan_amount
    cumulative_interest = Decimal("0")
    cumulative_principal = Decimal("0")

    for year in range(1, duration + 1):
        yearly_interest = Decimal("0")
        yearly_principal = Decimal("0")
        for _i in range(1, 13):
            if balance <= 0:
                break
            monthly_interest = balance * monthly_interest_rate
            monthly_principal = min(monthly_payment - monthly_interest, balance)
            balance -= monthly_principal
            yearly_interest += monthly_interest
            yearly_principal += monthly_principal

        cumulative_interest += yearly_interest
        cumulative_principal += yearly_principal
        amortization_schedule_yearly.append(
            {
                "year": year,
                "cumulative_interest": quantize_decimal(cumulative_interest),
                "cumulative_principal": quantize_decimal(cumulative_principal),
                "balance": quantize_decimal(balance),
                "cumulative_payment": quantize_decimal(
                    cumulative_interest + cumulative_principal
                ),
                "yearly_payment": quantize_decimal(yearly_principal),
                "yearly_interest": quantize_decimal(yearly_interest),
            }
        )

    return amortization_schedule_yearly


def calculate_loan_details(loan_amount, duration, interest_rate):
    loan_amount = Decimal(loan_amount)
    monthly_interest_rate = Decimal(interest_rate) / 12
    number_of_payments = duration * 12

    if interest_rate == 0:
        monthly_payment = loan_amount / number_of_payments
        total_payment = loan_amount
        total_interest = Decimal("0")
    else:
        monthly_payment = (
            loan_amount
            * monthly_interest_rate
            * (1 + monthly_interest_rate) ** number_of_payments
        ) / ((1 + monthly_interest_rate) ** number_of_payments - 1)
        total_payment = monthly_payment * number_of_payments
        total_interest = total_payment - loan_amount

    return {
        "monthly_payment": quantize_decimal(monthly_payment),
        "number_of_payments": number_of_payments,
        "rate_per_period": quantize_decimal(monthly_interest_rate, "0.0001"),
        "total_payment": quantize_decimal(total_payment),
        "total_interest": quantize_decimal(total_interest),
    }
