import os
import uuid
from datetime import datetime
from os import times
from random import choices
import math

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

class Site(models.Model):
    site_code = models.CharField(max_length=4, default="0000")
    site_name = models.CharField(max_length=100, default="")
    site_address_line1 = models.CharField(max_length=200, help_text="Address line 1", default="")
    site_address_line2 = models.CharField(max_length=200, blank=True, help_text="Address line 2 (optional)", default="")
    site_city = models.CharField(max_length=100, default="")
    site_state = models.CharField(max_length=100, default="")
    site_pincode = models.CharField(max_length=10, default="")
    site_gst_number = models.CharField(max_length=15, help_text="GST registration number")
    site_contact_person_name = models.CharField(max_length=100, default="")
    site_contact_person_number = models.CharField(validators=[phone_regex], max_length=15, default="0000000000")
    site_contact_person_email = models.EmailField(max_length=100, default="")
    site_pf_code = models.CharField(max_length=20, default="0")
    site_esic_code = models.CharField(max_length=20, default="0")
    site_service_charge_salary = models.CharField(max_length=20, default="0")
    site_service_charge_over_time = models.CharField(max_length=20, default="0")
    site_account_number = models.CharField(max_length=20, default="0")
    site_ifsc_code = models.CharField(max_length=11, default="0")

    USER_TYPE_CHOICES = [
        ('Hour', 'Hour'),
        ('Day', 'Day'),
        ('Month', 'Month')
    ]
    site_salary_component_type = models.CharField(max_length=20, choices=USER_TYPE_CHOICES, default="Month")
    site_ot_rule = models.CharField(max_length=20, default="0")
    site_bonus_formula = models.CharField(max_length=20, default="0")
    site_pf_deduction = models.CharField(max_length=20, default="0")
    site_esic_deduction_rule = models.CharField(max_length=20, default="0")
    site_welfare_deduction_rule = models.CharField(max_length=20, default="0")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.site_name



class SalaryRule(models.Model):
    site = models.ForeignKey(Site, on_delete=models.CASCADE, related_name='salary_rules', null=True, blank=True)

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
        site_name = self.site.site_name if self.site_id else "Unknown Site"
        return f"{site_name} - Salary Rule"


class SalaryOtherField(models.Model):
    site = models.ForeignKey(Site, on_delete=models.CASCADE, related_name='salary_other_fields', null=True, blank=True)

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
        site_name = self.site.site_name if self.site_id else "Unknown Site"
        return f"{site_name} - Salary Other Fields"



class CompanyAdvanceTransaction(models.Model):
    site = models.ForeignKey(Site, on_delete=models.CASCADE, null=True, blank=True)
    employee_id = models.CharField(max_length=50)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    month = models.IntegerField()
    year = models.IntegerField()

    def __str__(self):
        return f"{self.employee_id} - Advance for {self.month}/{self.year}"


class Arrear(models.Model):
    site = models.ForeignKey(Site, on_delete=models.CASCADE, null=True, blank=True)
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
    theme_preference = models.CharField(max_length=10, default='light', choices=[('light', 'Light'), ('dark', 'Dark')])
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
    site = models.ForeignKey(Site, on_delete=models.CASCADE, related_name='employees', null=True, blank=True)
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
    transport = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    canteen = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
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
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name="attendance_records")
    year = models.PositiveIntegerField()
    month = models.PositiveIntegerField(choices=MONTH_CHOICES)
    days_worked = models.PositiveIntegerField()

    class Meta:
        unique_together = ('employee', 'year', 'month')
        verbose_name = "Employee Attendance"
        verbose_name_plural = "Employee Attendance Records"

    def __str__(self):
        site_name = self.employee.site.site_name if self.employee.site else "No Site"
        return f"{self.employee.name} - {site_name} ({self.month}/{self.year})"

# Employee Aadhar and Bank account verification
class VerificationRequest(models.Model):
    VERIFICATION_TYPES = [
        ('aadhaar', 'Aadhaar Verification'),
        ('bank_account', 'Bank Account Verification'),
    ]

    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('in_progress', 'In Progress'),
        ('verified', 'Verified'),
        ('failed', 'Failed'),
        ('expired', 'Expired'),
    ]

    # Request Details
    request_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    verification_type = models.CharField(max_length=20, choices=VERIFICATION_TYPES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')

    # Personal Information
    full_name = models.CharField(max_length=200)
    date_of_birth = models.DateField()
    mobile_number = models.CharField(max_length=15)
    email = models.EmailField()

    # Aadhaar Details
    aadhaar_number = models.CharField(
        max_length=12,
        validators=[RegexValidator(r'^\d{12}$', 'Aadhaar must be 12 digits')],
        null=True,
        blank=True
    )

    # Bank Details
    bank_account_number = models.CharField(max_length=20, null=True, blank=True)
    bank_ifsc_code = models.CharField(
        max_length=11,
        validators=[RegexValidator(r'^[A-Z]{4}0[A-Z0-9]{6}$', 'Invalid IFSC code format')],
        null=True,
        blank=True
    )
    bank_name = models.CharField(max_length=100, null=True, blank=True)
    account_holder_name = models.CharField(max_length=100, null=True, blank=True)

    # Verification Results
    verification_response = models.JSONField(default=dict)
    verification_score = models.IntegerField(null=True, blank=True)
    verification_message = models.TextField(null=True, blank=True)
    verified_at = models.DateTimeField(null=True, blank=True)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.full_name} - {self.verification_type} - {self.status}"

    class Meta:
        ordering = ['-created_at']


class VerificationActivity(models.Model):
    verification_request = models.ForeignKey(VerificationRequest, on_delete=models.CASCADE)
    activity_type = models.CharField(max_length=50)
    description = models.TextField()
    metadata = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']


class Salary(models.Model):
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='salaries')
    month = models.PositiveSmallIntegerField(choices=MONTH_CHOICES)
    year = models.PositiveIntegerField()

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
    site = models.ForeignKey(Site, on_delete=models.CASCADE, related_name="reports", null=True, blank=True)
    report_type = models.CharField(max_length=20, choices=REPORT_TYPE_CHOICES)
    month = models.PositiveSmallIntegerField(choices=MONTH_CHOICES)
    year = models.PositiveIntegerField()

    def __str__(self):
        return f"{self.report_type} Report for {self.site.site_name} ({self.get_month_display()}/{self.year})"

    def get_month_display(self):
        return dict(MONTH_CHOICES).get(self.month)

    def clean(self):
        pass

    def generate_report_data(self):
        """Generate data for the report based on the selected report type and month/year."""
        base_filters = {
            'year': self.year,
            'month': self.month,
        }

        if self.report_type == 'Salary':
            queryset = Salary.objects.filter(
                employee__site=self.site,
                **base_filters
            ).select_related('employee')
            
            data = []
            for salary in queryset:
                data.append({
                    'Employee Code': salary.employee.employee_code,
                    'Employee Name': salary.employee.name,
                    'Basic Salary': salary.basic_salary,
                    'Transport': salary.transport,
                    'Canteen': salary.canteen,
                    'PF': salary.pf,
                    'ESIC': salary.esic,
                    'Advance Deduction': salary.advance_deduction,
                    'Gross Salary': salary.gross_salary,
                    'Net Salary': salary.net_salary,
                    'Month': salary.get_month_display(),
                    'Year': salary.year
                })
            return data
        elif self.report_type == 'Attendance':
            queryset = EmployeesAttendance.objects.filter(
                site=self.site,
                **base_filters
            ).select_related('employee')
            
            data = []
            for attendance in queryset:
                data.append({
                    'Employee Code': attendance.employee.employee_code,
                    'Employee Name': attendance.employee.name,
                    'Days Worked': attendance.days_worked,
                    'Month': dict(MONTH_CHOICES).get(attendance.month),
                    'Year': attendance.year
                })
            return data

        elif self.report_type == 'Arrear':
            queryset = Arrear.objects.filter(
                site=self.site,
                **base_filters
            ).select_related('employee')
            
            data = []
            for arrear in queryset:
                data.append({
                    'Employee Code': arrear.employee_id,
                    'Employee Name': Employee.objects.get(employee_code=arrear.employee_id).name,
                    'Amount': arrear.amount,
                    'Month': dict(MONTH_CHOICES).get(arrear.month),
                    'Year': arrear.year
                })
            return data

        elif self.report_type == 'Advance':
            queryset = CompanyAdvanceTransaction.objects.filter(
                site=self.site,
                **base_filters
            )
            
            data = []
            for advance in queryset:
                try:
                    employee = Employee.objects.get(employee_code=advance.employee_id)
                    data.append({
                        'Employee Code': advance.employee_id,
                        'Employee Name': employee.name,
                        'Bank Account': employee.employee_account or '-',
                        'IFSC Code': employee.ifsc or '-',
                        'Amount': advance.amount,
                        'Month': dict(MONTH_CHOICES).get(advance.month),
                        'Year': advance.year
                    })
                except Employee.DoesNotExist:
                    data.append({
                        'Employee Code': advance.employee_id,
                        'Employee Name': 'Not Found',
                        'Bank Account': '-',
                        'IFSC Code': '-',
                        'Amount': advance.amount,
                        'Month': dict(MONTH_CHOICES).get(advance.month),
                        'Year': advance.year
                    })
            return data

        elif self.report_type == 'PF':
            queryset = Salary.objects.filter(
                employee__site=self.site,
                **base_filters
            ).select_related('employee')
            
            data = []
            for salary in queryset:
                data.append({
                    'Employee Code': salary.employee.employee_code,
                    'Employee Name': salary.employee.name,
                    'PF Amount': salary.pf,
                    'Month': salary.get_month_display(),
                    'Year': salary.year
                })
            return data

        elif self.report_type == 'ESIC':
            queryset = Salary.objects.filter(
                employee__site=self.site,
                **base_filters
            ).select_related('employee')
            
            data = []
            for salary in queryset:
                data.append({
                    'Employee Code': salary.employee.employee_code,
                    'Employee Name': salary.employee.name,
                    'ESIC Amount': salary.esic,
                    'Month': salary.get_month_display(),
                    'Year': salary.year
                })
            return data
        return None



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

# Main Purchase Record (Header)
class Purchase(models.Model):
    # Organization Details
    organization_code = models.CharField(max_length=5)
    organization_name = models.CharField(max_length=255)
    organization_gst_number = models.CharField(max_length=15)
    
    # Bill & Order Details
    bill_number = models.CharField(max_length=5, unique=True, default='0000')
    po_number = models.CharField(max_length=5, blank=True, default='0000')
    order_by = models.CharField(max_length=50, blank=True)
    order_for = models.ForeignKey(VendorInformation, on_delete=models.SET_NULL, null=True, blank=True, help_text="Vendor for this purchase")
    
    # Purchase Date
    date_of_purchase = models.DateField()
    
    # Tax Rates (Common for all items in this purchase)
    cgst_rate = models.DecimalField(max_digits=4, decimal_places=2, default=0.0)
    sgst_rate = models.DecimalField(max_digits=4, decimal_places=2, default=0.0)
    igst_rate = models.DecimalField(max_digits=4, decimal_places=2, default=0.0)
    
    # Payment Details
    Vendor_PAYMENT_CHOICES = [
        ('full_payment_vendor', 'Full Payment Done'),
        ('part_payment_vendor', 'Part Payment Done'),
        ('unpaid_vendor', 'Payment Pending'),
    ]
    payment_status = models.CharField(max_length=50, choices=Vendor_PAYMENT_CHOICES, default='full_payment_vendor')
    payment_by = models.CharField(max_length=50, blank=True, default='')
    payment_date = models.DateField(blank=True, null=True)
    
    # Partial Payment Tracking
    amount_paid = models.DecimalField(max_digits=12, decimal_places=2, default=0, help_text="Amount paid so far")
    account_detail = models.CharField(max_length=100, blank=True, default='', help_text="Account detail for payment")
    transaction_id = models.CharField(max_length=100, blank=True, default='', help_text="Transaction ID if any")
    
    PAYMENT_CHOICES = [
        ('bank_transfer', 'Bank Transfer'),
        ('cash', 'Cash'),
        ('upi', 'UPI'),
    ]
    payment_mode = models.CharField(max_length=20, choices=PAYMENT_CHOICES, blank=True, default='bank_transfer')
    remark = models.CharField(max_length=255, blank=True)
    
    # Bill upload
    bill_file = models.FileField(upload_to=bill_upload_path, blank=True, null=True)
    
    # Calculated Totals
    total_gross_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0, editable=False)
    total_gst_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0, editable=False)
    total_net_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0, editable=False)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    @property
    def balance_amount(self):
        """Calculate remaining balance amount"""
        return self.total_net_amount - self.amount_paid
    
    @property
    def is_fully_paid(self):
        """Check if purchase is fully paid"""
        return self.balance_amount <= 0
    
    @property
    def payment_percentage(self):
        """Calculate payment percentage"""
        if self.total_net_amount > 0:
            return (self.amount_paid / self.total_net_amount) * 100
        return 0
    
    def calculate_totals(self):
        """Calculate totals from all line items with per-item GST"""
        line_items = self.line_items.all()
        self.total_gross_amount = sum(item.total_amount for item in line_items)
        self.total_gst_amount = sum(item.cgst_amount + item.sgst_amount + item.igst_amount for item in line_items)
        self.total_net_amount = sum(item.total_with_gst for item in line_items)
        self.save()
    
    def __str__(self):
        return f"Purchase {self.bill_number} - {self.organization_name}"
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = "Purchase"
        verbose_name_plural = "Purchases"

# Purchase Line Items (Individual Items)
class PurchaseLineItem(models.Model):

    purchase = models.ForeignKey(Purchase, on_delete=models.CASCADE, related_name='line_items')
    
    # Item Details
    purchased_item = models.CharField(max_length=50)
    hsn_code = models.CharField(max_length=10)
    
    # Pricing Details
    per_unit_cost = models.DecimalField(max_digits=10, decimal_places=2)
    units_bought = models.PositiveIntegerField()
    total_amount = models.DecimalField(max_digits=12, decimal_places=2, editable=False)
    
    # GST Rates (Per Item)
    cgst_rate = models.DecimalField(max_digits=4, decimal_places=2, default=0.0)
    sgst_rate = models.DecimalField(max_digits=4, decimal_places=2, default=0.0)
    igst_rate = models.DecimalField(max_digits=4, decimal_places=2, default=0.0)
    
    # Calculated GST Amounts
    cgst_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0, editable=False)
    sgst_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0, editable=False)
    igst_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0, editable=False)
    total_with_gst = models.DecimalField(max_digits=12, decimal_places=2, default=0, editable=False)
    
    # Ordering
    order = models.PositiveIntegerField(default=0)
    
    def save(self, *args, **kwargs):
        # Calculate total amount for this line item (without GST)
        self.total_amount = self.per_unit_cost * self.units_bought
        
        # Calculate GST amounts
        self.cgst_amount = self.total_amount * self.cgst_rate / 100
        self.sgst_amount = self.total_amount * self.sgst_rate / 100
        self.igst_amount = self.total_amount * self.igst_rate / 100
        
        # Calculate total with GST
        self.total_with_gst = self.total_amount + self.cgst_amount + self.sgst_amount + self.igst_amount
        
        super().save(*args, **kwargs)
        
        # Recalculate purchase totals
        if self.purchase_id:
            self.purchase.calculate_totals()
    
    def __str__(self):
        return f"{self.purchased_item} - {self.purchase.bill_number}"
    
    class Meta:
        ordering = ['order', 'id']
        verbose_name = "Purchase Line Item"
        verbose_name_plural = "Purchase Line Items"

# Purchases from vendor
class PurchaseItem(models.Model):

    organization_code = models.CharField(max_length=5)
    organization_name = models.CharField(max_length=255)
    organization_gst_number = models.CharField(max_length=15)
    bill_number = models.CharField(max_length=5)
    po_number = models.CharField(max_length=5, blank=True, default="0000")
    order_by = models.CharField(max_length=50, blank=True, default="")
    order_for = models.ForeignKey(VendorInformation, on_delete=models.SET_NULL, null=True, blank=True, help_text="Vendor for this purchase")
    purchased_item = models.CharField(max_length=50)
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



# E-Invoice Model
class EInvoice(models.Model):
    INVOICE_TYPE_CHOICES = [
        ('B2B', 'B2B - Business to Business'),
        ('B2C', 'B2C - Business to Consumer'),
        ('SEZWP', 'SEZ with Payment'),
        ('SEZWOP', 'SEZ without Payment'),
        ('EXPWP', 'Export with Payment'),
        ('EXPWOP', 'Export without Payment'),
        ('DEXPW', 'Deemed Export'),
    ]
    
    DOCUMENT_TYPE_CHOICES = [
        ('INV', 'Tax Invoice'),
        ('CRN', 'Credit Note'),
        ('DBN', 'Debit Note'),
    ]
    
    STATE_CODE_CHOICES = [
        ('01', '01 - Jammu and Kashmir'),
        ('02', '02 - Himachal Pradesh'),
        ('03', '03 - Punjab'),
        ('04', '04 - Chandigarh'),
        ('05', '05 - Uttarakhand'),
        ('06', '06 - Haryana'),
        ('07', '07 - Delhi'),
        ('08', '08 - Rajasthan'),
        ('09', '09 - Uttar Pradesh'),
        ('10', '10 - Bihar'),
        ('11', '11 - Sikkim'),
        ('12', '12 - Arunachal Pradesh'),
        ('13', '13 - Nagaland'),
        ('14', '14 - Manipur'),
        ('15', '15 - Mizoram'),
        ('16', '16 - Tripura'),
        ('17', '17 - Meghalaya'),
        ('18', '18 - Assam'),
        ('19', '19 - West Bengal'),
        ('20', '20 - Jharkhand'),
        ('21', '21 - Odisha'),
        ('22', '22 - Chhattisgarh'),
        ('23', '23 - Madhya Pradesh'),
        ('24', '24 - Gujarat'),
        ('25', '25 - Daman and Diu'),
        ('26', '26 - Dadra and Nagar Haveli'),
        ('27', '27 - Maharashtra'),
        ('28', '28 - Andhra Pradesh'),
        ('29', '29 - Karnataka'),
        ('30', '30 - Goa'),
        ('31', '31 - Lakshadweep'),
        ('32', '32 - Kerala'),
        ('33', '33 - Tamil Nadu'),
        ('34', '34 - Puducherry'),
        ('35', '35 - Andaman and Nicobar Islands'),
        ('36', '36 - Telangana'),
        ('37', '37 - Andhra Pradesh (New)'),
        ('38', '38 - Ladakh'),
    ]
    
    # Invoice Basic Information
    invoice_number = models.CharField(max_length=50, unique=True)
    invoice_date = models.DateField()
    invoice_type = models.CharField(max_length=10, choices=INVOICE_TYPE_CHOICES, default='B2B')
    document_type = models.CharField(max_length=3, choices=DOCUMENT_TYPE_CHOICES, default='INV')
    reverse_charge = models.BooleanField(default=False)
    irn = models.CharField(max_length=64, blank=True, null=True)  # Generated automatically
    
    # Supplier (Seller) Information
    supplier_gstin = models.CharField(max_length=15, validators=[RegexValidator(r'^[0-9]{2}[A-Z]{5}[0-9]{4}[A-Z]{1}[A-Z0-9]{1}[Z]{1}[A-Z0-9]{1}$', 'Invalid GSTIN format')])
    supplier_legal_name = models.CharField(max_length=200)
    supplier_address = models.TextField()
    supplier_place_of_supply = models.CharField(max_length=100)
    supplier_state_code = models.CharField(max_length=2, choices=STATE_CODE_CHOICES)
    
    # Recipient (Buyer) Information
    buyer_gstin = models.CharField(max_length=15, blank=True, null=True, validators=[RegexValidator(r'^[0-9]{2}[A-Z]{5}[0-9]{4}[A-Z]{1}[A-Z0-9]{1}[Z]{1}[A-Z0-9]{1}$', 'Invalid GSTIN format')])
    buyer_legal_name = models.CharField(max_length=200)
    buyer_address = models.TextField()
    buyer_state_code = models.CharField(max_length=2, choices=STATE_CODE_CHOICES)
    
    # Additional Addresses (if applicable)
    dispatch_from_address = models.TextField(blank=True, null=True)
    shipping_address = models.TextField(blank=True, null=True)
    
    # Payment and Reference Information
    payment_terms = models.CharField(max_length=200, blank=True, null=True)
    due_date = models.DateField(blank=True, null=True)
    reference_document = models.CharField(max_length=100, blank=True, null=True, help_text="e.g., PO Number")
    
    # Transporter Details (for e-Way Bill linkage)
    transporter_name = models.CharField(max_length=200, blank=True, null=True)
    transporter_id = models.CharField(max_length=15, blank=True, null=True)
    vehicle_number = models.CharField(max_length=20, blank=True, null=True)
    
    # Calculated Totals (will be calculated from line items)
    total_taxable_value = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    total_cgst = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    total_sgst = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    total_igst = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    total_tax_amount = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    total_invoice_value = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('sent', 'Sent'),
        ('paid', 'Paid'),
        ('cancelled', 'Cancelled'),
    ]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    def save(self, *args, **kwargs):
        # Calculate totals from line items
        if self.pk:
            line_items = self.line_items.all()
            self.total_taxable_value = sum(item.total_value for item in line_items)
            self.total_cgst = sum(item.cgst_amount for item in line_items)
            self.total_sgst = sum(item.sgst_amount for item in line_items)
            self.total_igst = sum(item.igst_amount for item in line_items)
            self.total_tax_amount = self.total_cgst + self.total_sgst + self.total_igst
            self.total_invoice_value = self.total_taxable_value + self.total_tax_amount
        super().save(*args, **kwargs)
    
    def generate_irn(self):
        """Generate IRN - In real implementation, this would call GST API"""
        import hashlib
        import uuid
        data = f"{self.supplier_gstin}{self.invoice_number}{self.invoice_date}"
        return hashlib.sha256(data.encode()).hexdigest()[:64]
    
    def __str__(self):
        return f"{self.invoice_number} - {self.buyer_legal_name}"
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = "E-Invoice"
        verbose_name_plural = "E-Invoices"


# E-Invoice Line Item Model
class EInvoiceLineItem(models.Model):
    invoice = models.ForeignKey(EInvoice, on_delete=models.CASCADE, related_name='line_items')
    
    # Item Details
    product_service_name = models.CharField(max_length=200)
    hsn_sac_code = models.CharField(max_length=10)
    quantity = models.DecimalField(max_digits=10, decimal_places=3)
    unit_price = models.DecimalField(max_digits=12, decimal_places=2)
    total_value = models.DecimalField(max_digits=12, decimal_places=2)
    
    # Tax Details
    cgst_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    sgst_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    igst_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    
    # Calculated Tax Amounts
    cgst_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    sgst_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    igst_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    item_total_with_tax = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    def save(self, *args, **kwargs):
        # Calculate totals
        self.total_value = self.quantity * self.unit_price
        self.cgst_amount = (self.total_value * self.cgst_rate) / 100
        self.sgst_amount = (self.total_value * self.sgst_rate) / 100
        self.igst_amount = (self.total_value * self.igst_rate) / 100
        
        # Calculate item total with tax
        self.item_total_with_tax = self.total_value + self.cgst_amount + self.sgst_amount + self.igst_amount
        
        super().save(*args, **kwargs)
        
        # Update invoice totals
        self.invoice.save()

    def __str__(self):
        return f"{self.product_service_name} - {self.invoice.invoice_number}"


# Bill Template Models for Manpower Service Bills
class BillTemplate(models.Model):
    """
    Template for reusable bill calculation rules and configurations
    """
    site = models.ForeignKey(Site, on_delete=models.CASCADE, related_name='bill_templates', null=True, blank=True)
    template_name = models.CharField(max_length=100, help_text="Name for this template (e.g., 'Monthly Manpower Service')")
    description = models.TextField(blank=True, help_text="Description of when to use this template")
    
    # Default service parameters
    default_hsn_code = models.CharField(max_length=10, default="998519", help_text="Default HSN code for manpower services")
    
    # Tax Configuration
    esi_rate = models.DecimalField(max_digits=5, decimal_places=2, default=3.25, help_text="ESI rate as percentage")
    service_charge_rate = models.DecimalField(max_digits=5, decimal_places=2, default=6.0, help_text="Service charge rate as percentage")
    cgst_rate = models.DecimalField(max_digits=5, decimal_places=2, default=9.0, help_text="CGST rate as percentage")
    sgst_rate = models.DecimalField(max_digits=5, decimal_places=2, default=9.0, help_text="SGST rate as percentage")
    igst_rate = models.DecimalField(max_digits=5, decimal_places=2, default=18.0, help_text="IGST rate as percentage")
    
    # Calculation Rules
    apply_esi = models.BooleanField(default=True, help_text="Apply ESI contribution")
    apply_service_charge = models.BooleanField(default=True, help_text="Apply service charge")
    apply_cgst_sgst = models.BooleanField(default=True, help_text="Apply CGST/SGST (for same state)")
    apply_igst = models.BooleanField(default=False, help_text="Apply IGST (for different state)")
    
    # Rounding Rules
    round_to_nearest = models.DecimalField(max_digits=5, decimal_places=2, default=0.01, help_text="Round final amount to nearest value")
    
    # Template Settings
    is_default = models.BooleanField(default=False, help_text="Make this the default template")
    is_active = models.BooleanField(default=True, help_text="Template is active and can be used")
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['site', 'template_name']
        ordering = ['-created_at']
        verbose_name = "Bill Template"
        verbose_name_plural = "Bill Templates"
    
    def __str__(self):
        return f"{self.company.company_name} - {self.template_name}"
    
    def save(self, *args, **kwargs):
        # Ensure only one default template per company
        if self.is_default:
            BillTemplate.objects.filter(company=self.company, is_default=True).update(is_default=False)
        super().save(*args, **kwargs)

def number_to_indian_words(number):
    # Helper for integer part
    def int_to_words(n):
        units = ["", "One", "Two", "Three", "Four", "Five", "Six", "Seven", "Eight", "Nine", "Ten", "Eleven", "Twelve", "Thirteen", "Fourteen", "Fifteen", "Sixteen", "Seventeen", "Eighteen", "Nineteen"]
        tens = ["", "", "Twenty", "Thirty", "Forty", "Fifty", "Sixty", "Seventy", "Eighty", "Ninety"]
        thousands = ["", "Thousand", "Lakh", "Crore"]
        if n == 0:
            return "Zero"
        words = ""
        if n >= 10000000:
            words += int_to_words(n // 10000000) + " Crore "
            n %= 10000000
        if n >= 100000:
            words += int_to_words(n // 100000) + " Lakh "
            n %= 100000
        if n >= 1000:
            words += int_to_words(n // 1000) + " Thousand "
            n %= 1000
        if n >= 100:
            words += int_to_words(n // 100) + " Hundred "
            n %= 100
        if n > 0:
            if n < 20:
                words += units[n] + " "
            else:
                words += tens[n // 10] + " "
                if n % 10:
                    words += units[n % 10] + " "
        return words.strip()

    rupees = int(math.floor(number))
    paise = int(round((number - rupees) * 100))
    words = int_to_words(rupees) + " Rupees"
    if paise > 0:
        words += " and " + int_to_words(paise) + " Paise"
    words += " Only"
    return words

class ServiceBill(models.Model):
    """
    Manpower Service Bill Model
    """
    # Bill Information
    bill_number = models.CharField(max_length=50, unique=True, blank=True)
    bill_date = models.DateField(default=timezone.now)
    site = models.ForeignKey(Site, on_delete=models.CASCADE, related_name='service_bills', null=True, blank=True)
    template = models.ForeignKey(BillTemplate, on_delete=models.PROTECT, related_name='bills')
    
    # Client Information (Bill To)
    client_name = models.CharField(max_length=200)
    client_address = models.TextField()
    client_gst_number = models.CharField(max_length=15, blank=True, null=True)
    
    # Calculated Totals
    total_gross_wages = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    taxable_value = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    cgst_amount = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    sgst_amount = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    igst_amount = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    total_amount = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    
    # Status
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('sent', 'Sent'),
        ('paid', 'Paid'),
        ('overdue', 'Overdue'),
        ('cancelled', 'Cancelled'),
    ]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = "Service Bill"
        verbose_name_plural = "Service Bills"

    def __str__(self):
        return f"Bill {self.bill_number} for {self.client_name}"

    def save(self, *args, **kwargs):
        # Generate bill number if not provided
        if not self.bill_number:
            self.bill_number = self.generate_bill_number()
        
        # Save first to get the pk
        super().save(*args, **kwargs)
        
        # Calculate totals after saving (when pk exists)
        if self.pk:
            self.calculate_totals()
            # Save again with updated totals
            super().save(*args, **kwargs)

    def generate_bill_number(self):
        # Generate a unique bill number, e.g., "BILL-2023-10-0001"
        today = timezone.now()
        year = today.year
        month = today.month
        
        last_bill = ServiceBill.objects.filter(created_at__year=year, created_at__month=month).order_by('id').last()
        
        if last_bill and last_bill.bill_number:
            try:
                last_num = int(last_bill.bill_number.split('-')[-1])
                new_num = last_num + 1
            except (IndexError, ValueError):
                new_num = 1
        else:
            new_num = 1
            
        return f"BILL-{year}-{month:02d}-{new_num:04d}"

    def calculate_totals(self):
        line_items = self.line_items.all()
        
        # Calculate total gross wages from line items
        self.total_gross_wages = sum(item.amount for item in line_items)
        
        # Start with gross wages as base
        taxable_amount = self.total_gross_wages
        
        # Apply ESI contribution if enabled in template
        if self.template.apply_esi:
            esi_contribution = (self.total_gross_wages * self.template.esi_rate) / 100
            taxable_amount += esi_contribution
        
        # Apply service charge if enabled in template
        if self.template.apply_service_charge:
            service_charge = (self.total_gross_wages * self.template.service_charge_rate) / 100
            taxable_amount += service_charge
        
        # Set taxable value
        self.taxable_value = taxable_amount
        
        # Calculate taxes based on template settings
        if self.template.apply_cgst_sgst:
            self.cgst_amount = (self.taxable_value * self.template.cgst_rate) / 100
            self.sgst_amount = (self.taxable_value * self.template.sgst_rate) / 100
            self.igst_amount = 0
        elif self.template.apply_igst:
            self.igst_amount = (self.taxable_value * self.template.igst_rate) / 100
            self.cgst_amount = 0
            self.sgst_amount = 0
        else:
            self.cgst_amount = 0
            self.sgst_amount = 0
            self.igst_amount = 0
        
        # Calculate total amount
        self.total_amount = self.taxable_value + self.cgst_amount + self.sgst_amount + self.igst_amount
        
        # Apply rounding if specified
        if self.template.round_to_nearest > 0:
            self.total_amount = round(self.total_amount / self.template.round_to_nearest) * self.template.round_to_nearest

    def get_amount_in_words(self):
        return number_to_indian_words(float(self.total_amount))

    @property
    def total_esi_contribution(self):
        if self.template and self.template.apply_esi:
            return round(self.total_gross_wages * (Decimal(self.template.esi_rate) / Decimal('100')), 2)
        return Decimal('0.00')

    @property
    def total_service_charge(self):
        if self.template and self.template.apply_service_charge:
            return round(self.total_gross_wages * (Decimal(self.template.service_charge_rate) / Decimal('100')), 2)
        return Decimal('0.00')

    @property
    def rounding_difference(self):
        if self.template and self.template.round_to_nearest and self.template.round_to_nearest > 0:
            unrounded = self.taxable_value
            if self.template.apply_cgst_sgst:
                unrounded += self.cgst_amount + self.sgst_amount
            elif self.template.apply_igst:
                unrounded += self.igst_amount
            rounded = round(unrounded / self.template.round_to_nearest) * float(self.template.round_to_nearest)
            return Decimal(str(rounded)) - Decimal(str(unrounded))
        return Decimal('0.00')

class ServiceBillItem(models.Model):
    """
    Individual line items for Service Bills
    """
    bill = models.ForeignKey(ServiceBill, on_delete=models.CASCADE, related_name='line_items')
    
    # Item Details
    description = models.CharField(max_length=200, help_text="e.g., Manpower Supply")
    hsn_code = models.CharField(max_length=10)
    amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    
    # Ordering
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['order', 'id']
        verbose_name = "Service Bill Item"
        verbose_name_plural = "Service Bill Items"

    def __str__(self):
        return self.description

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        
        # Update parent bill totals
        if self.bill:
            self.bill.save() # This will trigger calculate_totals on the bill

