from django.urls import path

from . import views

app_name = "loans"

urlpatterns = [
    path("", views.list_loans, name="list"),
    path("<int:loan_id>/", views.loan_detail, name="details"),
    path("create/", views.create_loan, name="create"),
    path(
        "get_amortization_schedule/",
        views.get_loan_amortization_schedule,
        name="get_amortization_schedule",
    ),
    path("<int:loan_id>/approve/", views.approve_loan, name="approve"),
    path("<int:loan_id>/reject/", views.reject_loan, name="reject"),
    path("pending/", views.list_pending_loans, name="pending"),
    path("approved/", views.list_approved_loans, name="approved"),
    path("rejected/", views.list_rejected_loans, name="rejected"),
]
