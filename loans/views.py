from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from .models import Loan, LoanConfig
from .form import LoanCreationForm
from .utils import create_amortization_schedule, calculate_loan_details
from django.http import JsonResponse
from decimal import Decimal


def is_bank_admin(user):
    return user.is_authenticated and user.is_bank_admin_user


@login_required
def list_loans(request):
    if request.user.is_bank_admin_user:
        loans = Loan.objects.all()
    else:
        loans = Loan.objects.filter(user=request.user)
    return render(request, "loans/list.html", {"loans": loans})


@login_required
def loan_detail(request, loan_id):
    if request.user.is_bank_admin_user:
        loan = Loan.objects.get(pk=loan_id)
    else:
        loan = Loan.objects.get(pk=loan_id, user=request.user)
    return render(request, "loans/details.html", {"loan": loan})


@login_required
def create_loan(request):
    if request.method == "POST":
        form = LoanCreationForm(request.POST)
        if form.is_valid():
            loan = form.save(commit=False)
            loan.user = request.user
            loan.save()
            loan.calculate_loan_details()
            loan.create_amortization_schedule()
            return redirect("loans:list")
    else:
        form = LoanCreationForm()
    loan_config = LoanConfig.load()
    return render(
        request, "loans/create.html", {"form": form, "loan_config": loan_config}
    )


@login_required
def get_loan_amortization_schedule(request):
    amount = Decimal(request.GET.get("amount"))
    duration = int(request.GET.get("duration"))
    interest_rate = LoanConfig.load().interest_rate
    amortization_schedule = create_amortization_schedule(
        amount, duration, interest_rate
    )
    details = calculate_loan_details(amount, duration, interest_rate)
    return JsonResponse(
        {"amortization_schedule": amortization_schedule, "details": details}
    )


@login_required
@user_passes_test(is_bank_admin)
def approve_loan(request, loan_id):
    loan = Loan.objects.get(pk=loan_id)
    loan.approve(request.user)
    return redirect("loans:list")


@login_required
@user_passes_test(is_bank_admin)
def reject_loan(request, loan_id):
    loan = Loan.objects.get(pk=loan_id)
    loan.reject(request.user)
    return redirect("loans:list")


@login_required
@user_passes_test(is_bank_admin)
def list_pending_loans(request):
    loans = Loan.objects.filter(status="pending")
    return render(request, "loans/list.html", {"loans": loans})


@login_required
@user_passes_test(is_bank_admin)
def list_approved_loans(request):
    loans = Loan.objects.filter(status="approved")
    return render(request, "loans/list.html", {"loans": loans})


@login_required
@user_passes_test(is_bank_admin)
def list_rejected_loans(request):
    loans = Loan.objects.filter(status="rejected")
    return render(request, "loans/list.html", {"loans": loans})
