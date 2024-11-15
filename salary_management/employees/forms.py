from django import forms
from .models import (Employee, Task, Payment, PurchaseItem, VendorInformation,
                     Company, SalaryRule, Profile, StaffSalary, AdvanceTransaction, SalaryOtherField, EInvoice, Report)
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.contrib.auth.models import User
import re
from django.forms import modelformset_factory
from django.core.exceptions import ValidationError


# Constants for validation
GST_REGEX = r'\d{2}[A-Z]{5}\d{4}[A-Z]{1}[A-Z\d]{1}[Z]{1}[A-Z\d]{1}'
IFSC_REGEX = r'^[A-Za-z]{4}\d{7}$'


# Helper function for validating GST and IFSC codes
def validate_gst_number(gst_number):
    if gst_number and not re.match(GST_REGEX, gst_number):
        raise forms.ValidationError("Invalid GST number format.")
    return gst_number


def validate_ifsc_code(ifsc_code):
    if ifsc_code and not re.match(IFSC_REGEX, ifsc_code):
        raise forms.ValidationError("Invalid IFSC code format.")
    return ifsc_code


# User Registration
USER_TYPE_CHOICES = [
    ('Owner', 'Owner'),
    ('Manager', 'Manager'),
    ('Employee', 'Employee'),
]


class CustomUserCreationForm(UserCreationForm):
    first_name = forms.CharField(max_length=30, required=True,
                                 widget=forms.TextInput(attrs={'placeholder': 'Enter First Name'}))
    last_name = forms.CharField(max_length=30, required=True,
                                widget=forms.TextInput(attrs={'placeholder': 'Enter Last Name'}))
    user_type = forms.ChoiceField(choices=USER_TYPE_CHOICES, required=True)

    company_name = forms.ModelChoiceField(queryset=Company.objects.all(), required=True, empty_label="Select Company")

    class Meta:
        model = User
        fields = ('username', 'password1', 'password2', 'first_name', 'last_name', 'user_type', 'company_name')

    def clean(self):
        cleaned_data = super().clean()
        user_type = cleaned_data.get('user_type')

        if user_type == 'Owner':
            # Owner-specific validation
            gst_number = cleaned_data.get('gst_number')
            ifsc_code = cleaned_data.get('ifsc_code')
            cleaned_data['gst_number'] = validate_gst_number(gst_number)
            cleaned_data['ifsc_code'] = validate_ifsc_code(ifsc_code)

        return cleaned_data


class ProfileEditForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = [
            'theme_preference', 'organisation_name', 'organisation_address',
            'contact_number', 'account_number', 'ifsc_code', 'gst_number', 'company'
        ]
        widgets = {
            'company': forms.Select(attrs={'class': 'form-select'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Customize company field
        self.fields['company'].empty_label = "Select Company"
        self.fields['company'].widget.attrs.update({'class': 'form-select'})


# User login form
class LoginForm(AuthenticationForm):
    username = forms.CharField(max_length=254,
                               widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Username'}))
    password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Password'}))
    company_name = forms.ModelChoiceField(
        queryset=Company.objects.all(),
        required=True,
        empty_label="Select Company",
        widget=forms.Select(attrs={'class': 'form-select'})
    )



# Employee Form
class EmployeeForm(forms.ModelForm):
    class Meta:
        model = Employee
        fields = [
            # Personal Details
            'employee_code', 'name', 'father_name', 'mother_name', 'gender', 'dob', 'marital_status', 'spouse_name',
            'mobile', 'email', 'address', 'district', 'state', 'pincode',

            # Professional Details
            'pf_no', 'esi_no', 'uan', 'pan', 'company', 'department', 'designation', 'doj', 'doe',

            # Account Details
            'pay_mode', 'employer_account', 'employee_account', 'ifsc', 'kyc_status', 'handicap', 'remarks',

            # Salary Details
            'basic', 'sr_allowance', 'da', 'hra', 'travel_allowance', 'medical', 'conveyance',
            'wash_allowance', 'efficiency', 'other_payable', 'employee_status', 'performance_color'
        ]
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Employee Name'}),
            'father_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Father\'s Name'}),
            'mother_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Mother\'s Name'}),
            'mobile': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Mobile Number'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Address'}),
            'remarks': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Remarks'}),
            'dob': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'doj': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'doe': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'employee_status': forms.Select(attrs={'class': 'form-control'}),
            'performance_color': forms.Select(attrs={'class': 'form-control'}),
            'basic': forms.NumberInput(attrs={'class': 'form-control'}),
            'sr_allowance': forms.NumberInput(attrs={'class': 'form-control'}),
            'da': forms.NumberInput(attrs={'class': 'form-control'}),
            'hra': forms.NumberInput(attrs={'class': 'form-control'}),
            'travel_allowance': forms.NumberInput(attrs={'class': 'form-control'}),
            'medical': forms.NumberInput(attrs={'class': 'form-control'}),
            'conveyance': forms.NumberInput(attrs={'class': 'form-control'}),
            'wash_allowance': forms.NumberInput(attrs={'class': 'form-control'}),
            'efficiency': forms.NumberInput(attrs={'class': 'form-control'}),
            'other_payable': forms.NumberInput(attrs={'class': 'form-control'}),
            # Add more widgets as needed
        }



# Excel upload form
class ExcelUploadForm(forms.Form):
    file = forms.FileField(widget=forms.ClearableFileInput(attrs={'class': 'form-control'}))


# Employee search form
class EmployeeSearchForm(forms.Form):
    employee_code_or_name = forms.CharField(label='Employee Code or Name', max_length=100, widget=forms.TextInput(
        attrs={'class': 'form-control', 'placeholder': 'Search by Code or Name'}))


# Task form
class TaskForm(forms.ModelForm):
    class Meta:
        model = Task
        fields = ['title']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Add new task'})
        }


# Payment form for vendor companies
class PaymentForm(forms.ModelForm):
    payment_date = forms.DateField(widget=forms.SelectDateWidget)

    class Meta:
        model = Payment
        fields = ['company_name', 'payment_against_bill', 'amount_received', 'payment_date', 'remark', 'payment_status']
        widgets = {
            'company_name': forms.TextInput(attrs={'class': 'form-control'}),
            'remark': forms.TextInput(attrs={'class': 'form-control'}),
            'payment_status': forms.Select(attrs={'class': 'form-select'}),
        }


# Vendor Information form
class VendorInformationForm(forms.ModelForm):
    class Meta:
        model = VendorInformation
        fields = [
            'vendor_id', 'vendor_name', 'vendor_address','district',
            'state', 'pincode', 'vendor_gst_number', 'vendor_account_number',
            'vendor_ifsc_code', 'vendor_contact_person_name', 'vendor_contact_person_number'
        ]


class PurchaseItemForm(forms.ModelForm):
    date_of_purchase = forms.DateField(widget=forms.SelectDateWidget)

    class Meta:
        model = PurchaseItem
        fields = [
            'organization_code', 'organization_name', 'organization_gst_number', 'bill_number', 'po_number',
            'order_by', 'order_for', 'purchased_item', 'category', 'hsn_code', 'date_of_purchase',
            'per_unit_cost', 'units_bought', 'cgst_rate', 'sgst_rate', 'igst_rate', 'payment_status',
            'payment_by', 'payment_date', 'payment_mode', 'remark', 'bill_file'
        ]
        widgets = {
            'organization_code': forms.TextInput(attrs={'class': 'form-control'}),
            'organization_name': forms.TextInput(attrs={'class': 'form-control'}),
            'organization_gst_number': forms.TextInput(attrs={'class': 'form-control'}),
            'bill_number': forms.TextInput(attrs={'class': 'form-control'}),
            'purchased_item': forms.TextInput(attrs={'class': 'form-control'}),
            'category': forms.Select(attrs={'class': 'form-select'}),
            'hsn_code': forms.TextInput(attrs={'class': 'form-control'}),
            'date_of_purchase': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'per_unit_cost': forms.NumberInput(attrs={'class': 'form-control'}),
            'units_bought': forms.NumberInput(attrs={'class': 'form-control'}),
            'cgst_rate': forms.NumberInput(attrs={'class': 'form-control'}),
            'sgst_rate': forms.NumberInput(attrs={'class': 'form-control'}),
            'igst_rate': forms.NumberInput(attrs={'class': 'form-control'}),
            'payment_status': forms.Select(attrs={'class': 'form-select'}),
            'payment_by': forms.TextInput(attrs={'class': 'form-control'}),
            'payment_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'payment_mode': forms.Select(attrs={'class': 'form-select'}),
            'remark': forms.TextInput(attrs={'class': 'form-control'}),
            'bill_file': forms.ClearableFileInput(attrs={'class': 'form-control'}),
        }

# Formset for handling multiple purchase items
PurchaseItemFormSet = modelformset_factory(
    PurchaseItem,
    form=PurchaseItemForm,
    extra=1,  # Number of additional blank forms to display
    can_delete=True,  # Allow deletion of existing items
)

# Company form
class CompanyForm(forms.ModelForm):
    class Meta:
        model = Company
        fields = [
            'company_code', 'company_name', 'company_address', 'company_gst_number', 'company_account_number',
            'company_ifsc_code', 'company_contact_person_name', 'company_contact_person_number',
            'company_contact_person_email', 'company_pf_code', 'company_esic_code',
            'company_service_charge_salary', 'company_service_charge_over_time', 'company_salary_component_type',
            'company_ot_rule', 'company_bonus_formula', 'company_pf_deduction',
            'company_esic_deduction_rule', 'company_welfare_deduction_rule',
             # add new fields here
        ]

class SalaryRuleForm(forms.ModelForm):
    # Checkbox fields
    pf = forms.BooleanField(required=False)
    esic = forms.BooleanField(required=False)
    lwf = forms.BooleanField(required=False)
    ot = forms.BooleanField(required=False)
    tr = forms.BooleanField(required=False)
    add = forms.BooleanField(required=False)

    class Meta:
        model = SalaryRule
        fields = [
            'Basic_rate_type', 'Basic_pay_type',
            'Sr_All_rate_type', 'Sr_All_pay_type',
            'DA_rate_type', 'DA_pay_type',
            'HRA_rate_type', 'HRA_pay_type',
            'TA_rate_type', 'TA_pay_type',
            'Med_rate_type', 'Med_pay_type',
            'Conv_rate_type', 'Conv_pay_type',
            'Wash_rate_type', 'Wash_pay_type',
            'Eff_rate_type', 'Eff_pay_type',
            'Other_rate_type', 'Other_pay_type',
            'Incentive_rate_type', 'Incentive_pay_type',
            'Bonus_rate_type', 'Bonus_pay_type',
            'Over_Time_rate_type', 'Over_Time_pay_type',

        ]

# Define a formset for adding multiple salary rules at once
SalaryRuleFormSet = modelformset_factory(SalaryRule, form=SalaryRuleForm, extra=1)

class SalaryOtherFieldForm(forms.ModelForm):
    # Checkbox fields
    pf = forms.BooleanField(required=False)
    esic = forms.BooleanField(required=False)
    lwf = forms.BooleanField(required=False)
    ot = forms.BooleanField(required=False)
    tr = forms.BooleanField(required=False)
    add = forms.BooleanField(required=False)

    class Meta:
        model = SalaryOtherField
        fields = [
            'Good_Work_Allowance_rate_type', 'Good_Work_Allowance_pay_type',
            'ABRY_rate_type', 'ABRY_pay_type',
            'Add_Bonus_rate_type', 'Add_Bonus_pay_type',
            'Arrears_rate_type', 'Arrears_pay_type',
            'Attnd_Award_rate_type', 'Attnd_Award_pay_type',
            'Attnd_Incentive_rate_type', 'Attnd_Incentive_pay_type',
            'Bonus_Allowance_rate_type', 'Bonus_Allowance_pay_type',
            'Conveyance_Allowance_rate_type', 'Conveyance_Allowance_pay_type',
            'Festival_Bonus_refund_rate_type', 'Festival_Bonus_refund_pay_type',
            'Gratuity_rate_type', 'Gratuity_pay_type',
            'Night_Allowance_rate_type', 'Night_Allowance_pay_type',
            'Production_incentive_rate_type', 'Production_incentive_pay_type',
            'Welding_Allowance_rate_type', 'Welding_Allowance_pay_type'
        ]

# Define a formset for adding multiple salary rules at once
SalaryOtherFieldFormSet = modelformset_factory(SalaryOtherField, form=SalaryOtherFieldForm, extra=1)


# Adding Company form
class AddCompanyForm(forms.Form):
    company_code = forms.CharField(max_length=4)
    company_name = forms.CharField(max_length=100)
    company_address = forms.CharField(widget=forms.Textarea)
    company_gst_number = forms.CharField(max_length=20, validators=[validate_gst_number])
    company_account_number = forms.CharField(max_length=20)
    company_ifsc_code = forms.CharField(max_length=11, validators=[validate_ifsc_code])
    company_contact_person_name = forms.CharField(max_length=100)
    company_contact_person_number = forms.CharField(max_length=10)
    company_contact_person_email = forms.EmailField()
    company_pf_code = forms.CharField(max_length=20)
    company_esic_code = forms.CharField(max_length=20)
    company_service_charge_salary = forms.CharField(max_length=20)
    company_service_charge_over_time = forms.CharField(max_length=20)
    company_salary_component_type = forms.ChoiceField(choices=Company.USER_TYPE_CHOICES)
    company_ot_rule = forms.CharField(max_length=20)
    company_bonus_formula = forms.CharField(max_length=20)
    company_pf_deduction = forms.CharField(max_length=20)
    company_esic_deduction_rule = forms.CharField(max_length=20)
    company_welfare_deduction_rule = forms.CharField(max_length=20),
    hra = forms.BooleanField(required=False, initial=False, label="HRA")
    allowance = forms.BooleanField(required=False, initial=False, label="Allowance")


# attendance and advance upload form
class UploadForm(forms.Form):
    company = forms.ModelChoiceField(queryset=Company.objects.all(), required=True, label="Select Company", widget=forms.Select(attrs={'class': 'form-control'}))
    month = forms.ChoiceField(choices=[(i, i) for i in range(1, 13)], required=True, label="Select Month", widget=forms.Select(attrs={'class': 'form-control'}))
    year = forms.IntegerField(min_value=2000, max_value=2100, required=True, label="Select Year", widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'YYYY'}))
    upload_type = forms.ChoiceField(choices=[('attendance', 'Attendance'), ('advance', 'Advance')], required=True, label="Upload Type", widget=forms.Select(attrs={'class': 'form-control'}))
    upload_file = forms.FileField(required=True, label="Upload File", widget=forms.ClearableFileInput(attrs={'class': 'form-control-file'}))


# Arrear form with 6 sub categories
class UploadForm(forms.Form):
    company = forms.ModelChoiceField(queryset=Company.objects.all(), required=True, label="Select Company", widget=forms.Select(attrs={'class': 'form-control'}))
    month = forms.ChoiceField(choices=[(i, i) for i in range(1, 13)], required=True, label="Select Month", widget=forms.Select(attrs={'class': 'form-control'}))
    year = forms.IntegerField(min_value=2000, max_value=2100, required=True, label="Select Year", widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'YYYY'}))
    upload_type = forms.ChoiceField(choices=[
        ('attendance', 'Attendance'),
        ('advance', 'Advance'),
        ('arrears', 'Arrears')
    ], required=True, label="Upload Type", widget=forms.Select(attrs={'class': 'form-control'}))
    upload_file = forms.FileField(required=True, label="Upload File", widget=forms.ClearableFileInput(attrs={'class': 'form-control-file'}))


# Staff salary form
class StaffSalaryForm(forms.ModelForm):
    class Meta:
        model = StaffSalary
        fields = [
            'pf_no', 'name', 'father_name', 'gross_rate', 'esic_applicable', 'pf_applicable', 'lwf_applicable',
            'pd', 'gross_salary', 'esic_deduction', 'pf_deduction', 'lwf_deduction', 'net_salary', 'advance_given',
            'advance_deduction', 'advance_pending', 'salary_paid_from_account', 'date', 'opening_balance',
            'amount_paid_to_employee',
            'amount_recovered', 'amount_left', 'comment', 'column_1'
        ]
        widgets = {
            'date': forms.SelectDateWidget(),
        }


# Advance Transaction form for staff
class AdvanceTransactionForm(forms.ModelForm):
    class Meta:
        model = AdvanceTransaction
        fields = ['date', 'advance_taken', 'advance_deducted', 'nature', 'company', 'mode', 'cheque_no',
                  'paid_received_by', 'paid_received_account', 'comment']
        widgets = {
            'date': forms.SelectDateWidget(),
        }

# E invoice for company
class EInvoiceForm(forms.ModelForm):
    class Meta:
        model = EInvoice
        fields = [
            'site', 'department', 'month', 'invoice_no', 'date', 'type', 'category', 'service',
            'po_number', 'buyer', 'address', 'gstin', 'contact_person', 'mobile', 'state', 'city',
            'pincode', 'taxable', 'igst', 'cgst', 'sgst', 'cess', 'st_cess', 'cess_non_adv', 'total',
            'bill_amount', 'deduction_narration_1', 'deduction_amount_1', 'deduction_narration_2', 'deduction_amount_2',
            'cancelled', 'print_proprietor_name'
        ]
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date'}),
        }


class ReportForm(forms.ModelForm):
    class Meta:
        model = Report
        fields = ['company', 'report_type', 'from_date', 'to_date']
        widgets = {
            'from_date': forms.DateInput(attrs={'type': 'date'}),
            'to_date': forms.DateInput(attrs={'type': 'date'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        from_date = cleaned_data.get('from_date')
        to_date = cleaned_data.get('to_date')

        if from_date and to_date and from_date > to_date:
            raise ValidationError("From Date cannot be later than To Date.")