from django.db import models
from django.conf import settings
from django.utils import timezone
from .utils import create_amortization_schedule, calculate_loan_details
from django.core.exceptions import ValidationError


class LoanConfig(models.Model):
    max_loan_amount = models.DecimalField(max_digits=10, decimal_places=2)
    min_loan_amount = models.DecimalField(max_digits=10, decimal_places=2)
    max_loan_duration = models.PositiveIntegerField()
    min_loan_duration = models.PositiveIntegerField()
    interest_rate = models.DecimalField(max_digits=10, decimal_places=2)

    def clean(self):
        if self.min_loan_amount >= self.max_loan_amount:
            raise ValidationError(
                "Minimum loan amount must be less than maximum loan amount."
            )
        if self.min_loan_duration >= self.max_loan_duration:
            raise ValidationError(
                "Minimum loan duration must be less than maximum loan duration."
            )

    def save(self, *args, **kwargs):
        if not self.pk and LoanConfig.objects.exists():
            raise ValidationError("There can be only one LoanConfig instance.")
        self.full_clean()
        return super().save(*args, **kwargs)

    @classmethod
    def load(cls):
        config, created = cls.objects.get_or_create(pk=1)
        return config


class Loan(models.Model):

    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("approved", "Approved"),
        ("rejected", "Rejected"),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    duration = models.PositiveIntegerField()
    interest_rate = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    approved_at = models.DateTimeField(null=True, blank=True)
    rejected_at = models.DateTimeField(null=True, blank=True)
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="approved_by",
    )
    rejected_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="rejected_by",
    )
    monthly_payment = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True
    )
    number_of_payments = models.PositiveIntegerField(null=True, blank=True)
    rate_per_period = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True
    )
    total_interest = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True
    )

    def save(self, *args, **kwargs):
        if self.pk is None:
            loan_config = LoanConfig.load()
            self.interest_rate = loan_config.interest_rate
            if (
                self.amount < loan_config.min_loan_amount
                or self.amount > loan_config.max_loan_amount
            ):
                raise ValueError("Loan amount is not within the allowed range")
            if (
                self.duration < loan_config.min_loan_duration
                or self.duration > loan_config.max_loan_duration
            ):
                raise ValueError("Loan duration is not within the allowed range")

        super(Loan, self).save(*args, **kwargs)

    def calculate_loan_details(self):
        loan_details = calculate_loan_details(
            self.amount, self.duration, self.interest_rate
        )
        self.monthly_payment = loan_details["monthly_payment"]
        self.number_of_payments = loan_details["number_of_payments"]
        self.rate_per_period = loan_details["rate_per_period"]
        self.total_interest = loan_details["total_interest"]
        self.save()

    def create_amortization_schedule(self):
        amortization_schedule = create_amortization_schedule(
            self.amount, self.duration, self.interest_rate
        )
        amortization_objects = [
            AmortizationSchedule(
                loan=self,
                year=year["year"],
                cumulative_interest=year["cumulative_interest"],
                cumulative_principal=year["cumulative_principal"],
                balance=year["balance"],
                cumulative_payment=year["cumulative_payment"],
                yearly_payment=year["yearly_payment"],
                yearly_interest=year["yearly_interest"],
            )
            for year in amortization_schedule
        ]
        AmortizationSchedule.objects.bulk_create(amortization_objects)

    def approve(self, user):
        if self.status != "pending":
            raise ValueError("Loan is not pending approval")
        if not user.is_staff:
            raise ValueError("Only staff can approve loans")

        self.status = "approved"
        self.approved_at = timezone.now()
        self.approved_by = user
        self.save()

    def reject(self, user):
        if self.status != "pending":
            raise ValueError("Loan is not pending approval")
        if not user.is_staff:
            raise ValueError("Only staff can reject loans")
        self.status = "rejected"
        self.rejected_at = timezone.now()
        self.rejected_by = user
        self.save()

    def __str__(self):
        return f"{self.user} - {self.amount} - {self.status}"


class AmortizationSchedule(models.Model):
    loan = models.ForeignKey(Loan, on_delete=models.CASCADE)
    year = models.PositiveIntegerField()
    cumulative_interest = models.DecimalField(max_digits=10, decimal_places=2)
    cumulative_principal = models.DecimalField(max_digits=10, decimal_places=2)
    balance = models.DecimalField(max_digits=10, decimal_places=2)
    cumulative_payment = models.DecimalField(max_digits=10, decimal_places=2)
    yearly_payment = models.DecimalField(max_digits=10, decimal_places=2)
    yearly_interest = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.loan} - {self.year}"
