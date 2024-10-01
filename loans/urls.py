from django.urls import path

from . import views

app_name = "loans"

urlpatterns = [
    path("", views.list_loans, name="list"),
    path("<int:loan_id>/", views.loan_detail, name="detail"),
    path("create/", views.create_loan, name="create"),
]
