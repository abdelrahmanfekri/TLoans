from django.shortcuts import render
from django.http import HttpResponse

# Create your views here.


def list_loans(request):
    return HttpResponse("List of loans")


def loan_detail(request, loan_id):
    return HttpResponse(f"Loan detail for loan with id {loan_id}")


def create_loan(request):
    return HttpResponse("Create a new loan")
