from django.test import TestCase, Client
from decimal import Decimal
from .utils import (
    quantize_decimal,
    create_amortization_schedule,
    calculate_loan_details,
)
from django.urls import reverse
from django.contrib.auth import get_user_model
from .models import Loan, LoanConfig


class LoanCalculationTestCase(TestCase):
    def setUp(self):
        self.loan_amount = Decimal("100000.00")
        self.duration = 25
        self.interest_rate = Decimal("0.07")

    def test_quantize_decimal(self):
        self.assertEqual(quantize_decimal(Decimal("1.234")), Decimal("1.23"))
        self.assertEqual(quantize_decimal(Decimal("1.235")), Decimal("1.24"))

    def test_calculate_loan_details(self):
        result = calculate_loan_details(
            self.loan_amount, self.duration, self.interest_rate
        )
        self.assertEqual(result["monthly_payment"], Decimal("706.78"))
        self.assertEqual(result["number_of_payments"], 300)
        self.assertEqual(result["rate_per_period"], Decimal("0.0058"))
        self.assertEqual(result["total_payment"], Decimal("212033.76"))
        self.assertEqual(result["total_interest"], Decimal("112033.76"))

    def test_create_amortization_schedule(self):
        schedule = create_amortization_schedule(
            self.loan_amount, self.duration, self.interest_rate
        )
        self.assertEqual(len(schedule), 25)

        # Check the first year's values
        first_year = schedule[0]
        self.assertEqual(first_year["year"], 1)
        self.assertEqual(first_year["cumulative_interest"], Decimal("6951.54"))
        self.assertEqual(first_year["cumulative_principal"], Decimal("1529.81"))
        self.assertEqual(first_year["balance"], Decimal("98470.19"))
        self.assertEqual(first_year["cumulative_payment"], Decimal("8481.35"))
        self.assertEqual(first_year["yearly_payment"], Decimal("1529.81"))
        self.assertEqual(first_year["yearly_interest"], Decimal("6951.54"))

        # Check the last year's values
        last_year = schedule[-1]
        self.assertEqual(last_year["year"], 25)
        self.assertEqual(last_year["cumulative_interest"], Decimal("112033.76"))
        self.assertEqual(last_year["cumulative_principal"], Decimal("100000.00"))
        self.assertEqual(last_year["balance"], Decimal("0.00"))
        self.assertEqual(last_year["cumulative_payment"], Decimal("212033.76"))
        self.assertEqual(last_year["yearly_payment"], Decimal("8168.33"))
        self.assertEqual(last_year["yearly_interest"], Decimal("313.02"))

        # Check year 13's values
        middle_year = schedule[12]
        self.assertEqual(middle_year["year"], 13)
        self.assertEqual(middle_year["cumulative_interest"], Decimal("78984.92"))
        self.assertEqual(middle_year["cumulative_principal"], Decimal("31272.64"))
        self.assertEqual(middle_year["balance"], Decimal("68727.36"))
        self.assertEqual(middle_year["cumulative_payment"], Decimal("110257.55"))
        self.assertEqual(middle_year["yearly_payment"], Decimal("3534.97"))
        self.assertEqual(middle_year["yearly_interest"], Decimal("4946.38"))

    def test_edge_cases(self):
        # Test with zero loan amount
        zero_loan = calculate_loan_details(
            Decimal("0"), self.duration, self.interest_rate
        )
        self.assertEqual(zero_loan["monthly_payment"], Decimal("0.00"))
        self.assertEqual(zero_loan["total_payment"], Decimal("0.00"))

        # Test with zero interest rate
        zero_interest = calculate_loan_details(
            self.loan_amount, self.duration, Decimal("0")
        )
        self.assertEqual(zero_interest["monthly_payment"], Decimal("333.33"))
        self.assertEqual(zero_interest["total_payment"], Decimal("100000.00"))

        # Test with one year duration
        one_year = calculate_loan_details(self.loan_amount, 1, self.interest_rate)
        self.assertEqual(one_year["number_of_payments"], 12)


class LoanViewsTest(TestCase):

    def setUp(self):
        self.client = Client()
        User = get_user_model()
        self.user = User.objects.create_user(
            email="test@gmail.com", password="password", phone_number="1234567890"
        )
        self.bank_admin = User.objects.create_user(
            email="admin@gmail.com",
            password="password",
            is_bank_admin_user=True,
            phone_number="1234568890",
        )
        self.loan = Loan.objects.create(
            user=self.user,
            amount=Decimal("1000.00"),
            duration=12,
            interest_rate=LoanConfig.load().interest_rate,
        )
        self.testClient = Client()
        self.testClient.login(email="test@gmail.com", password="password")
        self.adminClient = Client()
        self.adminClient.login(email="admin@gmail.com", password="password")

    def test_list_loans(self):
        response = self.testClient.get(reverse("loans:list"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "loans/list.html")
        self.assertContains(response, self.loan.amount)

    def test_loan_detail(self):
        response = self.testClient.get(reverse("loans:details", args=[self.loan.id]))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "loans/details.html")
        self.assertContains(response, self.loan.amount)
        self.assertContains(response, self.user.email)

    def test_create_loan(self):
        response = self.testClient.post(
            reverse("loans:create"),
            {"amount": "1000.00", "duration": 12},
        )
        self.assertEqual(response.status_code, 302)

    def test_get_loan_amortization_schedule(self):
        response = self.testClient.get(
            reverse("loans:get_amortization_schedule"),
            {"amount": "1000.00", "duration": 12},
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/json")

    def test_approve_loan(self):
        response = self.adminClient.post(reverse("loans:approve", args=[self.loan.id]))
        self.assertEqual(response.status_code, 302)

    def test_approve_loan_not_admin(self):
        response = self.testClient.post(reverse("loans:approve", args=[self.loan.id]))
        self.assertRedirects(
            response,
            f"/users/login/?next={reverse('loans:approve', args=[self.loan.id])}",
        )

    def test_approve_loan_not_auth(self):
        response = self.client.post(reverse("loans:approve", args=[self.loan.id]))
        self.assertRedirects(
            response,
            f"/users/login/?next={reverse('loans:approve', args=[self.loan.id])}",
        )

    def test_reject_loan(self):
        response = self.adminClient.post(reverse("loans:reject", args=[self.loan.id]))
        self.assertEqual(response.status_code, 302)

    def test_reject_loan_not_admin(self):
        response = self.testClient.post(reverse("loans:reject", args=[self.loan.id]))
        self.assertRedirects(
            response,
            f"/users/login/?next={reverse('loans:reject', args=[self.loan.id])}",
        )

    def test_reject_loan_not_auth(self):
        response = self.client.post(reverse("loans:reject", args=[self.loan.id]))
        self.assertRedirects(
            response,
            f"/users/login/?next={reverse('loans:reject', args=[self.loan.id])}",
        )

    def test_list_pending_loans(self):
        response = self.adminClient.get(reverse("loans:pending"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "loans/list.html")

    def test_list_pending_loans_not_admin(self):
        response = self.testClient.get(reverse("loans:pending"))
        self.assertRedirects(response, f"/users/login/?next={reverse('loans:pending')}")

    def test_list_pending_loans_not_auth(self):
        response = self.client.get(reverse("loans:pending"))
        self.assertRedirects(response, f"/users/login/?next={reverse('loans:pending')}")

    def test_list_approved_loans(self):
        response = self.adminClient.get(reverse("loans:approved"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "loans/list.html")

    def test_list_approved_loans_not_admin(self):
        response = self.testClient.get(reverse("loans:approved"))
        self.assertRedirects(
            response, f"/users/login/?next={reverse('loans:approved')}"
        )

    def test_list_approved_loans_not_auth(self):
        response = self.client.get(reverse("loans:approved"))
        self.assertRedirects(
            response, f"/users/login/?next={reverse('loans:approved')}"
        )

    def test_list_rejected_loans(self):
        response = self.adminClient.get(reverse("loans:rejected"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "loans/list.html")

    def test_list_rejected_loans_not_admin(self):
        response = self.testClient.get(reverse("loans:rejected"))
        self.assertRedirects(
            response, f"/users/login/?next={reverse('loans:rejected')}"
        )
