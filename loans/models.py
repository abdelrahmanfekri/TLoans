from django.db import models
from django.conf import settings
from django.utils import timezone


class LoanConfig(models.Model):
    max_loan_amount = models.DecimalField(max_digits=10, decimal_places=2)
    min_loan_amount = models.DecimalField(max_digits=10, decimal_places=2)
    max_loan_duration = models.PositiveIntegerField()
    min_loan_duration = models.PositiveIntegerField()
    interest_rate = models.DecimalField(max_digits=10, decimal_places=2)

    # This is a singleton model
    def save(self, *args, **kwargs):
        self.pk = 1
        super(LoanConfig, self).save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        pass


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
            loan_config = LoanConfig.objects.first()
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
