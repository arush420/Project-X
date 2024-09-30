from os import times

from django.db import models
from django.utils import timezone
from decimal import Decimal


# Constants for salary fields
CURRENCY_MAX_DIGITS = 10
CURRENCY_DECIMAL_PLACES = 2
PERCENTAGE_MAX_DIGITS = 5
PERCENTAGE_DECIMAL_PLACES = 2

MONTH_CHOICES = [
    (1, 'January'), (2, 'February'), (3, 'March'), (4, 'April'),
    (5, 'May'), (6, 'June'), (7, 'July'), (8, 'August'),
    (9, 'September'), (10, 'October'), (11, 'November'), (12, 'December')
]

class Employee(models.Model):
    employee_code = models.CharField(max_length=10, unique=True)
    name = models.CharField(max_length=100)
    father_name = models.CharField(max_length=100)
    basic = models.DecimalField(max_digits=CURRENCY_MAX_DIGITS, decimal_places=CURRENCY_DECIMAL_PLACES)
    transport = models.DecimalField(max_digits=CURRENCY_MAX_DIGITS, decimal_places=CURRENCY_DECIMAL_PLACES, default=0.00)
    canteen = models.DecimalField(max_digits=CURRENCY_MAX_DIGITS, decimal_places=CURRENCY_DECIMAL_PLACES, default=0.00)
    pf = models.DecimalField(max_digits=PERCENTAGE_MAX_DIGITS, decimal_places=PERCENTAGE_DECIMAL_PLACES, default=0.00)
    esic = models.DecimalField(max_digits=PERCENTAGE_MAX_DIGITS, decimal_places=PERCENTAGE_DECIMAL_PLACES, default=0.00)
    advance = models.DecimalField(max_digits=CURRENCY_MAX_DIGITS, decimal_places=CURRENCY_DECIMAL_PLACES, default=0.00)

    def __str__(self):
        return f'{self.name} ({self.employee_code})'


class Salary(models.Model):
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='salaries')
    month = models.PositiveSmallIntegerField(choices=MONTH_CHOICES)
    year = models.PositiveIntegerField()
    gross_salary = models.DecimalField(max_digits=CURRENCY_MAX_DIGITS, decimal_places=CURRENCY_DECIMAL_PLACES)
    net_salary = models.DecimalField(max_digits=CURRENCY_MAX_DIGITS, decimal_places=CURRENCY_DECIMAL_PLACES,
                                     default=0.00)
    date_generated = models.DateTimeField(default=timezone.now)  # Corrected here

    class Meta:
        unique_together = ('employee', 'month', 'year')
        ordering = ['-year', '-month']

    def get_month_display(self):
        return dict(MONTH_CHOICES).get(self.month)


class PurchaseItem(models.Model):
    CATEGORY_CHOICES = [
        ('Stationary', 'Stationary'),
        ('Furniture', 'Furniture'),
        ('Pantry', 'Pantry'),
        ('Miscellaneous', 'Miscellaneous'),
    ]

    organization_code = models.CharField(max_length=100)
    organization_name = models.CharField(max_length=255)
    gst_number = models.CharField(max_length=15)
    bill_number = models.CharField(max_length=50)
    purchased_item = models.CharField(max_length=255)
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES, default='Miscellaneous')
    hsn_code = models.CharField(max_length=10)
    date_of_purchase = models.DateField()
    per_unit_cost = models.DecimalField(max_digits=10, decimal_places=2)
    units_bought = models.PositiveIntegerField()

    gross_total = models.DecimalField(max_digits=12, decimal_places=2, editable=False)
    cgst_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)
    sgst_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)
    igst_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)

    cgst_amount = models.DecimalField(max_digits=12, decimal_places=2, editable=False, default=0.00)
    sgst_amount = models.DecimalField(max_digits=12, decimal_places=2, editable=False, default=0.00)
    igst_amount = models.DecimalField(max_digits=12, decimal_places=2, editable=False, default=0.00)
    net_price = models.DecimalField(max_digits=12, decimal_places=2, editable=False, default=0.00)

    def save(self, *args, **kwargs):
        self.gross_total = self.per_unit_cost * self.units_bought
        self.cgst_amount = self.gross_total * (self.cgst_rate / 100)
        self.sgst_amount = self.gross_total * (self.sgst_rate / 100)
        self.igst_amount = self.gross_total * (self.igst_rate / 100)
        self.net_price = self.gross_total + self.cgst_amount + self.sgst_amount + self.igst_amount
        super(PurchaseItem, self).save(*args, **kwargs)

    def __str__(self):
        return f"{self.purchased_item} ({self.category}) purchased from {self.organization_name}"


class Task(models.Model):
    title = models.CharField(max_length=255)
    completed = models.BooleanField(default=False)

    def __str__(self):
        return self.title


class Profile(models.Model):
    organisation_name = models.CharField(max_length=255)
    address = models.TextField()
    account_number = models.CharField(max_length=20)
    ifsc_code = models.CharField(max_length=11)

    def __str__(self):
        return self.organisation_name


class Payment(models.Model):
    company_name = models.CharField(max_length=255)
    amount_received = models.DecimalField(max_digits=10, decimal_places=2)
    payment_date = models.DateField()
    account_of_own_company = models.CharField(max_length=255)
    payment_against_bill = models.CharField(max_length=255)

    def __str__(self):
        return f"Payment from {self.company_name} on {self.payment_date}"


class VendorInformation(models.Model):
    vendor_id = models.CharField(max_length=4)
    firm_code = models.CharField(max_length=4)
    vendor_name = models.CharField(max_length=100)
    vendor_address = models.TextField()
    vendor_gst_number = models.CharField(max_length=20)
    vendor_account_number = models.CharField(max_length=20)
    vendor_ifsc_code = models.CharField(max_length=11)
    vendor_contact_person_name = models.CharField(max_length=100)
    vendor_contact_person_number = models.CharField(max_length=100)

    def __str__(self):
        return self.vendor_name


class Company(models.Model):
    company_code = models.CharField(max_length=4, default="0000")
    company_name = models.CharField(max_length=100, default="")
    company_address = models.TextField()
    company_gst_number = models.CharField(max_length=20)
    company_account_number = models.CharField(max_length=20)
    company_ifsc_code = models.CharField(max_length=11)
    company_contact_person_name = models.CharField(max_length=100)
    company_contact_person_number = models.CharField(max_length=100)

    def __str__(self):
        return self.company_name