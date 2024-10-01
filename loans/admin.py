from django.contrib import admin
from .models import Loan, LoanConfig

# Register your models here.

admin.site.register(Loan)
admin.site.register(LoanConfig)
