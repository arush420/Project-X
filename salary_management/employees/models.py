import os
from datetime import datetime
from os import times
from random import choices

from django.contrib.auth.decorators import login_required, user_passes_test
from django.core.exceptions import ValidationError
from django.db import models
from django.shortcuts import get_object_or_404, redirect, render
from django.template.context_processors import request
from django.utils import timezone
from decimal import Decimal
from django.contrib.auth.models import User
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from django.db.models.signals import post_migrate, post_save
from django.dispatch import receiver
from django.core.validators import RegexValidator
from pyexpat.errors import messages
from django.contrib import messages


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

GENDER_CHOICES = [('Male', 'Male'), ('Female', 'Female')]
MARITAL_STATUS_CHOICES = [
    ('UnMarried', 'UnMarried'), ('Married', 'Married'),
    ('Divorced', 'Divorced'), ('Widow/Widower', 'Widow/Widower')
]
KYC_STATUS_CHOICES = [('Verified', 'Verified'), ('Pending', 'Pending')]

phone_regex = RegexValidator(regex=r'^\+?1?\d{9,15}$', message="Phone number must be entered in the format: '+999999999'. Up to 15 digits allowed.")



class Company(models.Model):
    company_code = models.CharField(max_length=4, default="0000")
    company_name = models.CharField(max_length=100, default="")
    company_address = models.CharField(max_length=255, default="")
    company_contact_person_name = models.CharField(max_length=100, default="")
    company_contact_person_number = models.CharField(validators=[phone_regex], max_length=10, default="0000000000")
    company_contact_person_email = models.EmailField(max_length=100, default="")
    company_gst_number = models.CharField(max_length=20, default="0")
    company_pf_code = models.CharField(max_length=20, default="0")
    company_esic_code = models.CharField(max_length=20, default="0")
    company_service_charge_salary = models.CharField(max_length=20, default="0")
    company_service_charge_over_time = models.CharField(max_length=20, default="0")
    company_account_number = models.CharField(max_length=20, default="0")
    company_ifsc_code = models.CharField(max_length=11, default="0")
    USER_TYPE_CHOICES = [
        ('Hour', 'Hour'),
        ('Day', 'Day'),
        ('Month', 'Month')
    ]
    company_salary_component_type = models.CharField(max_length=20,choices=USER_TYPE_CHOICES , default="0")
    company_ot_rule = models.CharField(max_length=20, default="0")
    company_bonus_formula = models.CharField(max_length=20, default="0")
    company_pf_deduction = models.CharField(max_length=20, default="0")
    company_esic_deduction_rule = models.CharField(max_length=20, default="0")
    company_welfare_deduction_rule = models.CharField(max_length=20, default="0")

    def __str__(self):
        return self.company_name



class SalaryRule(models.Model):
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='salary_rules')

    RATE_TYPE_CHOICES = [
        ('Per Month', 'Per Month'),
        ('Per Day', 'Per Day' )
    ]

    PAY_TYPE_CHOICES = [
        ('PayDay', 'PayDay'),
        ('OTHour', 'OTHour')
    ]


    # Fields with both rate type and pay type choices
    Basic_rate_type = models.CharField(max_length=20, choices=RATE_TYPE_CHOICES, default='Per Month')
    Basic_pay_type = models.CharField(max_length=20, choices=PAY_TYPE_CHOICES, default='PayDay')

    Sr_All_rate_type = models.CharField(max_length=20, choices=RATE_TYPE_CHOICES, default='Per Month')
    Sr_All_pay_type = models.CharField(max_length=20, choices=PAY_TYPE_CHOICES, default='PayDay')

    DA_rate_type = models.CharField(max_length=20, choices=RATE_TYPE_CHOICES, default='Per Month')
    DA_pay_type = models.CharField(max_length=20, choices=PAY_TYPE_CHOICES, default='PayDay')

    HRA_rate_type = models.CharField(max_length=20, choices=RATE_TYPE_CHOICES, default='Per Month')
    HRA_pay_type = models.CharField(max_length=20, choices=PAY_TYPE_CHOICES, default='PayDay')

    TA_rate_type = models.CharField(max_length=20, choices=RATE_TYPE_CHOICES, default='Per Month')
    TA_pay_type = models.CharField(max_length=20, choices=PAY_TYPE_CHOICES, default='PayDay')

    Med_rate_type = models.CharField(max_length=20, choices=RATE_TYPE_CHOICES, default='Per Month')
    Med_pay_type = models.CharField(max_length=20, choices=PAY_TYPE_CHOICES, default='PayDay')

    Conv_rate_type = models.CharField(max_length=20, choices=RATE_TYPE_CHOICES, default='Per Month')
    Conv_pay_type = models.CharField(max_length=20, choices=PAY_TYPE_CHOICES, default='PayDay')

    Wash_rate_type = models.CharField(max_length=20, choices=RATE_TYPE_CHOICES, default='Per Month')
    Wash_pay_type = models.CharField(max_length=20, choices=PAY_TYPE_CHOICES, default='PayDay')

    Eff_rate_type = models.CharField(max_length=20, choices=RATE_TYPE_CHOICES, default='Per Month')
    Eff_pay_type = models.CharField(max_length=20, choices=PAY_TYPE_CHOICES, default='PayDay')

    Other_rate_type = models.CharField(max_length=20, choices=RATE_TYPE_CHOICES, default='Per Month')
    Other_pay_type = models.CharField(max_length=20, choices=PAY_TYPE_CHOICES, default='PayDay')

    Incentive_rate_type = models.CharField(max_length=20, choices=RATE_TYPE_CHOICES, default='Per Month')
    Incentive_pay_type = models.CharField(max_length=20, choices=PAY_TYPE_CHOICES, default='PayDay')

    Bonus_rate_type = models.CharField(max_length=20, choices=RATE_TYPE_CHOICES, default='Per Month')
    Bonus_pay_type = models.CharField(max_length=20, choices=PAY_TYPE_CHOICES, default='PayDay')

    Over_Time_rate_type = models.CharField(max_length=20, choices=RATE_TYPE_CHOICES, default='Per Month')
    Over_Time_pay_type = models.CharField(max_length=20, choices=PAY_TYPE_CHOICES, default='PayDay')

    add = models.BooleanField(default=False)  # Track if this rule was selected

    def __str__(self):
        return f"{self.company.company_name} - {self.standard_head}"


class SalaryOtherField(models.Model):
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='salary_other_fields')

    RATE_TYPE_CHOICES = [
        ('Per Month', 'Per Month'),
        ('Per Day', 'Per Day' )
    ]

    PAY_TYPE_CHOICES = [
        ('PayDay', 'PayDay'),
        ('OTHour', 'OTHour')
    ]

    # Fields with both rate type and pay type choices
    Good_Work_Allowance_rate_type = models.CharField(max_length=20, choices=RATE_TYPE_CHOICES, default='Per Month')
    Good_Work_Allowance_pay_type = models.CharField(max_length=20, choices=PAY_TYPE_CHOICES, default='PayDay')

    ABRY_rate_type = models.CharField(max_length=20, choices=RATE_TYPE_CHOICES, default='Per Month')
    ABRY_pay_type = models.CharField(max_length=20, choices=PAY_TYPE_CHOICES, default='PayDay')

    Add_Bonus_rate_type = models.CharField(max_length=20, choices=RATE_TYPE_CHOICES, default='Per Month')
    Add_Bonus_pay_type = models.CharField(max_length=20, choices=PAY_TYPE_CHOICES, default='PayDay')

    Arrears_rate_type = models.CharField(max_length=20, choices=RATE_TYPE_CHOICES, default='Per Month')
    Arrears_pay_type = models.CharField(max_length=20, choices=PAY_TYPE_CHOICES, default='PayDay')

    Attnd_Award_rate_type = models.CharField(max_length=20, choices=RATE_TYPE_CHOICES, default='Per Month')
    Attnd_Award_pay_type = models.CharField(max_length=20, choices=PAY_TYPE_CHOICES, default='PayDay')

    Attnd_Incentive_rate_type = models.CharField(max_length=20, choices=RATE_TYPE_CHOICES, default='Per Month')
    Attnd_Incentive_pay_type = models.CharField(max_length=20, choices=PAY_TYPE_CHOICES, default='PayDay')

    Bonus_Allowance_rate_type = models.CharField(max_length=20, choices=RATE_TYPE_CHOICES, default='Per Month')
    Bonus_Allowance_pay_type = models.CharField(max_length=20, choices=PAY_TYPE_CHOICES, default='PayDay')

    Conveyance_Allowance_rate_type = models.CharField(max_length=20, choices=RATE_TYPE_CHOICES, default='Per Month')
    Conveyance_Allowance_pay_type = models.CharField(max_length=20, choices=PAY_TYPE_CHOICES, default='PayDay')

    Festival_Bonus_refund_rate_type = models.CharField(max_length=20, choices=RATE_TYPE_CHOICES, default='Per Month')
    Festival_Bonus_refund_pay_type = models.CharField(max_length=20, choices=PAY_TYPE_CHOICES, default='PayDay')

    Gratuity_rate_type = models.CharField(max_length=20, choices=RATE_TYPE_CHOICES, default='Per Month')
    Gratuity_pay_type = models.CharField(max_length=20, choices=PAY_TYPE_CHOICES, default='PayDay')

    Night_Allowance_rate_type = models.CharField(max_length=20, choices=RATE_TYPE_CHOICES, default='Per Month')
    Night_Allowance_pay_type = models.CharField(max_length=20, choices=PAY_TYPE_CHOICES, default='PayDay')

    Production_incentive_rate_type = models.CharField(max_length=20, choices=RATE_TYPE_CHOICES, default='Per Month')
    Production_incentive_pay_type = models.CharField(max_length=20, choices=PAY_TYPE_CHOICES, default='PayDay')

    Welding_Allowance_rate_type = models.CharField(max_length=20, choices=RATE_TYPE_CHOICES, default='Per Month')
    Welding_Allowance_pay_type = models.CharField(max_length=20, choices=PAY_TYPE_CHOICES, default='PayDay')

    add = models.BooleanField(default=False)  # Track if this field was selected

    def __str__(self):
        return f"{self.company.company_name} - Salary Other Fields"



class CompanyAdvanceTransaction(models.Model):
    company = models.ForeignKey(Company, on_delete=models.CASCADE)
    employee_id = models.CharField(max_length=50)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    month = models.IntegerField()
    year = models.IntegerField()

    def __str__(self):
        return f"{self.employee_id} - Advance for {self.month}/{self.year}"


class Arrear(models.Model):
    company = models.ForeignKey(Company, on_delete=models.CASCADE)
    employee_id = models.CharField(max_length=50)
    month = models.IntegerField()
    year = models.IntegerField()

    # Subcategories for arrears
    basic_salary_arrears = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    bonus_arrears = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    overtime_arrears = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    allowances_arrears = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    leave_encashment_arrears = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    salary_increment_arrears = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)

    def __str__(self):
        return f"{self.employee_id} - Arrears for {self.month}/{self.year}"



# User Profile details
class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)  # Linking to the User model
    theme_preference = models.CharField(max_length=10, default='light')  # choosing 'light' or 'dark'
    database =models.CharField(max_length=255, default="yada yada") # Add a field to reference the company's database if needed
    USER_TYPE_CHOICES = [
        ('Owner', 'Owner'),
        ('Manager', 'Manager'),
        ('Employee', 'Employee'),
    ]
    user_type = models.CharField(max_length=10, choices=USER_TYPE_CHOICES, default='Employee')
    company = models.ForeignKey(Company, null=True, blank=True, on_delete=models.SET_NULL)

    # Owner-specific fields
    organisation_name = models.CharField(max_length=255, blank=True, null=True)
    organisation_address = models.TextField(blank=True, null=True)
    contact_number = models.CharField(max_length=15, blank=True, null=True)
    account_number = models.CharField(max_length=20, blank=True, null=True)
    ifsc_code = models.CharField(max_length=11, blank=True, null=True)
    gst_number = models.CharField(max_length=15, blank=True, null=True)

    def __str__(self):
        return f"{self.user.username} - {self.user_type}"


@receiver(post_migrate)
def create_user_groups(sender, **kwargs):
    # Create groups
    superuser_group, superuser_created = Group.objects.get_or_create(name='Superuser')
    read_write_group, rw_created = Group.objects.get_or_create(name='Read and Write')
    read_only_group, ro_created = Group.objects.get_or_create(name='Read Only')

    # Fetch content types for the relevant models
    content_types = [
        ContentType.objects.get_for_model(Employee),
        ContentType.objects.get_for_model(Salary),
        ContentType.objects.get_for_model(Profile),
        ContentType.objects.get_for_model(Payment),
        ContentType.objects.get_for_model(VendorInformation),
        ContentType.objects.get_for_model(PurchaseItem),
    ]

    # Assign all permissions to the "Superuser" group
    if superuser_created:
        for content_type in content_types:
            all_permissions = Permission.objects.filter(content_type=content_type)
            superuser_group.permissions.add(*all_permissions)

    # Assign permissions for the "Read and Write" group
    if rw_created:
        for content_type in content_types:
            # Exclude delete permissions for read-write group
            read_write_permissions = Permission.objects.filter(content_type=content_type).exclude(
                codename__startswith='delete')
            read_write_group.permissions.add(*read_write_permissions)

    # Assign read-only permissions for the "Read Only" group
    if ro_created:
        for content_type in content_types:
            # Only assign 'view' permissions for read-only group
            read_only_permissions = Permission.objects.filter(content_type=content_type, codename__startswith='view')
            read_only_group.permissions.add(*read_only_permissions)


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    instance.profile.save()

class Employee(models.Model):
    # Personal Details
    employee_code = models.CharField(max_length=10, unique=True)
    name = models.CharField(max_length=100)
    father_name = models.CharField(max_length=100)
    mother_name = models.CharField(max_length=100, blank=True, null=True)
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES, blank=True)
    dob = models.DateField("Date of Birth", blank=True, null=True)
    marital_status = models.CharField(max_length=15, choices=MARITAL_STATUS_CHOICES, blank=True)
    spouse_name = models.CharField(max_length=100, blank=True, null=True)
    mobile = models.CharField(max_length=15, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    district = models.CharField(max_length=50, blank=True, null=True)
    state = models.CharField(max_length=50, blank=True, null=True)
    pincode = models.CharField(max_length=6, blank=True, null=True)
    # Professional details
    pf_no = models.CharField(max_length=20, blank=True, null=True)
    esi_no = models.CharField(max_length=20, blank=True, null=True)
    uan = models.CharField(max_length=20, blank=True, null=True)
    pan = models.CharField(max_length=20, blank=True, null=True)
    company = models.CharField(max_length=100, blank=True, null=True)
    department = models.CharField(max_length=50, blank=True, null=True)
    designation = models.CharField(max_length=50, blank=True, null=True)
    doj = models.DateField("Date of Joining", blank=True, null=True)
    doe = models.DateField("Date of Exit", blank=True, null=True)
    PAY_MODE_CHOICES = [
        ('bank', 'Bank'),
        ('cash', 'Cash')]
    pay_mode = models.CharField(max_length=50, blank=True, null=False, choices=PAY_MODE_CHOICES, default='bank')
    employer_account = models.CharField(max_length=50, blank=True, null=True)
    employee_account = models.CharField(max_length=50, blank=True, null=True)
    ifsc = models.CharField(max_length=11, blank=True, null=True)
    kyc_status = models.CharField(max_length=10, choices=KYC_STATUS_CHOICES, blank=True)
    handicap = models.BooleanField(default=False)
    remarks = models.TextField(blank=True, null=True)
    # Salary details
    basic = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    sr_allowance = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    da = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    hra = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    travel_allowance = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    medical = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    conveyance = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    wash_allowance = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    efficiency = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    other_payable = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))


    EMPLOYEE_STATUS_CHOICES = [
        ('working', 'Working'),
        ('not_working', 'Not Working')
    ]

    PERFORMANCE_COLOR_CHOICES = [
        ('green', 'Green'),
        ('yellow', 'Yellow'),
        ('red', 'Red')
    ]

    employee_status = models.CharField(max_length=15, choices=EMPLOYEE_STATUS_CHOICES, default='working')
    performance_color = models.CharField(max_length=10, choices=PERFORMANCE_COLOR_CHOICES, default='green')

    def __str__(self):
        return f'{self.name} ({self.employee_code})'

class EmployeesAttendance(models.Model):
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name="attendance_records")
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name="attendance_records")
    year = models.PositiveIntegerField()
    month = models.PositiveIntegerField(choices=MONTH_CHOICES)
    days_worked = models.PositiveIntegerField()

    class Meta:
        unique_together = ('company', 'employee', 'year', 'month')
        verbose_name = "Employee Attendance"
        verbose_name_plural = "Employee Attendance Records"

    def __str__(self):
        return f"{self.employee.name} - {self.company.company_name} ({self.month}/{self.year})"


class Salary(models.Model):
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='salaries')
    month = models.PositiveSmallIntegerField(choices=MONTH_CHOICES)
    year = models.PositiveIntegerField()
    advance = models.DecimalField(max_digits=CURRENCY_MAX_DIGITS, decimal_places=CURRENCY_DECIMAL_PLACES, default=0)
    basic_salary = models.DecimalField(max_digits=CURRENCY_MAX_DIGITS, decimal_places=CURRENCY_DECIMAL_PLACES, default=0)
    transport = models.DecimalField(max_digits=CURRENCY_MAX_DIGITS, decimal_places=CURRENCY_DECIMAL_PLACES, default=0)
    canteen = models.DecimalField(max_digits=CURRENCY_MAX_DIGITS, decimal_places=CURRENCY_DECIMAL_PLACES, default=0)
    pf = models.DecimalField(max_digits=CURRENCY_MAX_DIGITS, decimal_places=CURRENCY_DECIMAL_PLACES, default=0)
    esic = models.DecimalField(max_digits=CURRENCY_MAX_DIGITS, decimal_places=CURRENCY_DECIMAL_PLACES, default=0)
    advance_deduction = models.DecimalField(max_digits=CURRENCY_MAX_DIGITS, decimal_places=CURRENCY_DECIMAL_PLACES, default=0)
    gross_salary = models.DecimalField(max_digits=CURRENCY_MAX_DIGITS, decimal_places=CURRENCY_DECIMAL_PLACES, default=0)
    net_salary = models.DecimalField(max_digits=CURRENCY_MAX_DIGITS, decimal_places=CURRENCY_DECIMAL_PLACES, default=0)
    date_generated = models.DateTimeField(default=timezone.now)

    class Meta:
        constraints = [
                models.UniqueConstraint(fields=['employee', 'month', 'year'], name='unique_salary_per_month_year')
            ]
        ordering = ['-year', '-month']
        permissions = [
            ('can_generate_payroll', 'Can generate payroll'),
            ('can_modify_salary', 'Can modify salary records'),
            ('can_view_confidential_data', 'Can view confidential data'),
        ]

    def get_month_display(self):
        return dict(MONTH_CHOICES).get(self.month)

class SalaryTotals(models.Model):
    month = models.IntegerField()
    year = models.IntegerField()
    total_gross_salary = models.DecimalField(max_digits=12, decimal_places=2)
    total_pf = models.DecimalField(max_digits=12, decimal_places=2)
    total_esic = models.DecimalField(max_digits=12, decimal_places=2)
    total_canteen = models.DecimalField(max_digits=12, decimal_places=2)
    total_advance = models.DecimalField(max_digits=12, decimal_places=2)
    total_net_salary = models.DecimalField(max_digits=12, decimal_places=2)


class Task(models.Model):
    title = models.CharField(max_length=255)
    completed = models.BooleanField(default=False)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='transferred_tasks')

    def __str__(self):
        return self.title

# company Payment to Us
class Payment(models.Model):
    company_name = models.CharField(max_length=100)
    amount_received = models.DecimalField(max_digits=10, decimal_places=2)
    payment_date = models.DateField()
    account_of_own_company = models.CharField(max_length=5)
    payment_against_bill = models.CharField(max_length=5, unique=True)
    remark = models.CharField(max_length=100, blank=True)
    PAYMENT_CHOICES = [
        ('full_payment_received', 'Full Payment Received'),
        ('part_payment_received', 'part Payment Received')
    ]
    payment_status = models.CharField(max_length=100, choices=PAYMENT_CHOICES, default='Full Payment Received')

    def __str__(self):
        return f"Payment from {self.company_name} on {self.payment_date}"


class VendorInformation(models.Model):
    vendor_id = models.CharField(max_length=4)
    vendor_name = models.CharField(max_length=100)
    vendor_address = models.CharField(max_length=100)
    district = models.CharField(max_length=100, default='none')
    state = models.CharField(max_length=100, default='none')
    pincode = models.CharField(max_length=6, validators=[RegexValidator(r'^\d{6}$', message="Pincode must be 6 digits.")], default='000000')
    vendor_gst_number = models.CharField(max_length=20)
    vendor_account_number = models.CharField(max_length=20)
    vendor_ifsc_code = models.CharField(max_length=11)
    vendor_contact_person_name = models.CharField(max_length=100)
    vendor_contact_person_number = models.CharField(validators=[phone_regex], max_length=10)

    def __str__(self):
        return self.vendor_name


# Upload purchase bills
def bill_upload_path(instance, filename):
    return os.path.join("purchase_bills", filename)

# Purchases from vendor
class PurchaseItem(models.Model):
    CATEGORY_CHOICES = [
        ('Stationary', 'Stationary'),
        ('Furniture', 'Furniture'),
        ('Pantry', 'Pantry'),
        ('Miscellaneous', 'Miscellaneous'),
    ]
    organization_code = models.CharField(max_length=5)
    organization_name = models.CharField(max_length=255)
    organization_gst_number = models.CharField(max_length=15)
    bill_number = models.CharField(max_length=5)
    po_number = models.CharField(max_length=5, blank=True, default="0000")  # Fixed default and renamed field
    order_by = models.CharField(max_length=50, blank=True, default="")  # Optional and blank default
    order_for = models.CharField(max_length=50, blank=True, default="")  # Optional and blank default
    purchased_item = models.CharField(max_length=50)
    category = models.CharField(max_length=25, choices=CATEGORY_CHOICES, default='Miscellaneous')
    hsn_code = models.CharField(max_length=10)
    date_of_purchase = models.DateField()
    per_unit_cost = models.DecimalField(max_digits=10, decimal_places=2)
    units_bought = models.PositiveIntegerField()

    # Tax rates
    cgst_rate = models.DecimalField(max_digits=4, decimal_places=2)  # Adjusted max_digits for tax rates
    sgst_rate = models.DecimalField(max_digits=4, decimal_places=2)
    igst_rate = models.DecimalField(max_digits=4, decimal_places=2)

    # Totals
    gross_total = models.DecimalField(max_digits=12, decimal_places=2, editable=False, default=0)  # Updated precision
    total_gst = models.DecimalField(max_digits=12, decimal_places=2, editable=False, default=0)
    net_price = models.DecimalField(max_digits=12, decimal_places=2, editable=False, default=0)

    # Payment Details
    Vendor_PAYMENT_CHOICES = [
        ('full_payment_vendor', 'Full Payment Done'),
        ('part_payment_vendor', 'Part Payment Done'),
        ('unpaid_vendor', 'Payment Pending'),
    ]
    payment_status = models.CharField(max_length=50, choices=Vendor_PAYMENT_CHOICES, default='full_payment_vendor')  # Fixed defaut
    payment_by = models.CharField(max_length=50, blank=True, default="")  # Optional payment_by
    payment_date = models.DateField(blank=True, null=True)  # Changed to DateField
    PAYMENT_CHOICES = [
        ('bank_transfer', 'Bank Transfer'),
        ('cash', 'Cash'),
        ('upi', 'UPI'),
    ]
    payment_mode = models.CharField(max_length=20, choices=PAYMENT_CHOICES, blank=True, default="")  # Added payment_mode
    remark = models.CharField(max_length=255, blank=True)  # Extended length for detailed remarks

    # Bill upload
    bill_file = models.FileField(upload_to=bill_upload_path, blank=True, null=True)

    def save(self, *args, **kwargs):
        # Calculate gross total, GST, and net price
        self.gross_total = self.per_unit_cost * self.units_bought
        self.total_gst = self.gross_total * (self.cgst_rate + self.sgst_rate + self.igst_rate) / 100
        self.net_price = self.gross_total + self.total_gst
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.purchased_item} ({self.category}) purchased from {self.organization_name}"



# Staff salary
class StaffSalary(models.Model):
    pf_no = models.CharField(max_length=20, unique=True)
    name = models.CharField(max_length=100)
    father_name = models.CharField(max_length=100, null=True, blank=True)
    gross_rate = models.DecimalField(max_digits=10, decimal_places=2)

    esic_applicable = models.BooleanField(default=False)
    pf_applicable = models.BooleanField(default=False)
    lwf_applicable = models.BooleanField(default=False)

    pd = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    gross_salary = models.DecimalField(max_digits=10, decimal_places=2)

    esic_deduction = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    pf_deduction = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    lwf_deduction = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)

    net_salary = models.DecimalField(max_digits=10, decimal_places=2)
    advance_given = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, blank=True)
    advance_deduction = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, blank=True)
    advance_pending = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, blank=True)

    salary_paid_from_account = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    date = models.DateField(default=timezone.now)

    opening_balance = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    amount_paid_to_employee = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    amount_recovered = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    amount_left = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)

    comment = models.TextField(null=True, blank=True)
    column_1 = models.CharField(max_length=100, null=True, blank=True)

    def save(self, *args, **kwargs):
        # Carry forward opening balance from the previous month
        if self.pk is None:  # New entry
            previous_month_entry = StaffSalary.objects.filter(name=self.name).order_by('-date').first()
            if previous_month_entry:
                self.opening_balance = previous_month_entry.amount_left
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


# Staff Advance transaction
class AdvanceTransaction(models.Model):
    staff_salary = models.ForeignKey(StaffSalary, on_delete=models.CASCADE, related_name='transactions')

    # New fields added
    serial_number = models.IntegerField(default=1)  # S.NO
    name = models.CharField(max_length=100, default='unknown')  # Name
    amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, default="") # Amount
    ifsc_code = models.CharField(max_length=11, null=True, blank=True, default="")
    paid_received = models.CharField(max_length=10,
                                     choices=[('paid', 'Paid'), ('received', 'Received')], default='paid')  # Paid to/Received
    NATURE_CHOICES = [
        ('personal', 'Personal'),
        ('office', 'Office Expense'),
        ('company', 'Company Expense'),]
    nature = models.CharField(max_length=100,choices=NATURE_CHOICES ,default='personal')  # Nature, will be dynamically filtered
    company = models.CharField(max_length=100, null=True, blank=True, default='Shree Hanuman')  # Company
    MODE_CHOICES = [
        ('cash', 'Cash'),
        ('bank', 'Bank')]
    mode = models.CharField(max_length=50, choices=MODE_CHOICES, default='cash')  # Mode
    cheque_no = models.CharField(max_length=50, null=True, blank=True)  # Cheque No.
    month = models.CharField(max_length=20, default=datetime.now().strftime('%B'))  # Month
    net_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)  # Net Amount
    account = models.CharField(max_length=50, null=True, blank=True, default=0.00)  # A/C
    ifsc_code = models.CharField(max_length=50, null=True, blank=True, default=0.00)  # IFSC Code
    column1 = models.CharField(max_length=100, null=True, blank=True)  # Column1

    # Existing fields
    date = models.DateField(default=timezone.now)
    advance_taken = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    advance_deducted = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    advance_balance = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    paid_received_by = models.CharField(max_length=100, default='Unknown')
    paid_received_account = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    comment = models.TextField(null=True, blank=True)

    def save(self, *args, **kwargs):
        # Update the advance pending field on the related StaffSalary instance
        self.advance_balance = self.staff_salary.advance_pending - self.advance_deducted + self.advance_taken
        self.staff_salary.advance_pending = self.advance_balance
        self.staff_salary.save()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Transaction on {self.date} for {self.staff_salary.name}"

# E - Invoice



REPORT_TYPE_CHOICES = [
    ('Salary', 'Salary'),
    ('Attendance', 'Attendance'),
    ('Arrear', 'Arrear'),
    ('Advance', 'Advance'),
    ('PF', 'PF'),
    ('ESIC', 'ESIC'),
]

class Report(models.Model):
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name="reports")
    report_type = models.CharField(max_length=20, choices=REPORT_TYPE_CHOICES)
    from_date = models.DateField()
    to_date = models.DateField()

    def __str__(self):
        return f"{self.report_type} Report for {self.company.company_name} ({self.from_date} to {self.to_date})"

    def clean(self):
        # Ensure from_date is not later than to_date
        if self.from_date > self.to_date:
            raise ValidationError("From Date cannot be later than To Date.")

    def generate_report_data(self):
        """Generate data for the report based on the selected report type and date range."""
        filters = {
            'employee__company': self.company,
            'year__gte': self.from_date.year,
            'year__lte': self.to_date.year,
            'month__gte': self.from_date.month,
            'month__lte': self.to_date.month,
        }

        if self.report_type == 'Salary':
            return Salary.objects.filter(**filters)
        elif self.report_type == 'Attendance':
            return EmployeesAttendance.objects.filter(company=self.company, **filters)
        elif self.report_type == 'Arrear':
            return Arrear.objects.filter(company=self.company, **filters)
        elif self.report_type == 'Advance':
            return CompanyAdvanceTransaction.objects.filter(company=self.company, **filters)
        elif self.report_type == 'PF':
            return Salary.objects.filter(employee__company=self.company, year__gte=self.from_date.year,
                                         year__lte=self.to_date.year).values('pf')
        elif self.report_type == 'ESIC':
            return Salary.objects.filter(employee__company=self.company, year__gte=self.from_date.year,
                                         year__lte=self.to_date.year).values('esic')
        return None

