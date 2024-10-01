from django import forms
from .models import Loan, LoanConfig


class LoanCreationForm(forms.ModelForm):
    class Meta:
        model = Loan
        fields = ["amount", "duration"]

    def clean(self):
        cleaned_data = super().clean()
        amount = cleaned_data.get("amount")
        duration = cleaned_data.get("duration")
        loan_config = LoanConfig.load()
        if amount < loan_config.min_loan_amount or amount > loan_config.max_loan_amount:
            raise forms.ValidationError("Loan amount is not within the allowed range")
        if (
            duration < loan_config.min_loan_duration
            or duration > loan_config.max_loan_duration
        ):
            raise forms.ValidationError("Loan duration is not within the allowed range")
        return cleaned_data
