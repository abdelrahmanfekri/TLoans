from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from .models import Loan, LoanConfig
from .form import LoanCreationForm

# Create your views here.


@login_required
def list_loans(request):
    loans = Loan.objects.filter(user=request.user)
    return render(request, "loans/list.html", {"loans": loans})


@login_required
def loan_detail(request, loan_id):
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
