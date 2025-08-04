from django import forms
from .models import (Employee, Task, Payment, PurchaseItem, VendorInformation,
                     Company, SalaryRule, Profile, StaffSalary, AdvanceTransaction, SalaryOtherField, Report,
                     VerificationRequest, EInvoice, EInvoiceLineItem, BillTemplate, ServiceBill, ServiceBillItem,
                     Purchase, PurchaseLineItem, Site)
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.contrib.auth.models import User
import re
from django.forms import modelformset_factory, inlineformset_factory
from django.core.exceptions import ValidationError
import json


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
        fields = ('username', 'password2', 'password2', 'first_name', 'last_name', 'user_type', 'company_name')

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
        fields = '__all__'
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Employee Name'}),
            'father_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': "Father's Name"}),
            'mother_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': "Mother's Name"}),
            'mobile': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Mobile Number'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Address'}),
            'remarks': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Remarks'}),
            'dob': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'doj': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'doe': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'site': forms.Select(attrs={'class': 'form-control'}),
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
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            if field.required:
                field.label = f"{field.label} *"
    
    def clean_mobile(self):
        mobile = self.cleaned_data.get('mobile')
        if mobile and not mobile.isdigit():
            raise forms.ValidationError("Mobile number must contain only digits.")
        if mobile and len(mobile) != 10:
            raise forms.ValidationError("Mobile number must be exactly 10 digits long.")
        return mobile


# Excel upload form
class ExcelUploadForm(forms.Form):
    file = forms.FileField(widget=forms.ClearableFileInput(attrs={'class': 'form-control'}))


# Employee search form
class EmployeeSearchForm(forms.Form):
    employee_code_or_name = forms.CharField(label='Employee Code or Name', max_length=100, widget=forms.TextInput(
        attrs={'class': 'form-control', 'placeholder': 'Search by Code or Name'}))

# Employee Aadhar and Bank Account form
class VerificationRequestForm(forms.ModelForm):
    class Meta:
        model = VerificationRequest
        fields = [
            'verification_type', 'full_name', 'date_of_birth', 'mobile_number', 'email',
            'aadhaar_number', 'bank_account_number', 'bank_ifsc_code'
        ]
        widgets = {
            'date_of_birth': forms.DateInput(attrs={'type': 'date'}),
        }


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
    class Meta:
        model = PurchaseItem
        fields = [
            'organization_code', 'organization_name', 'organization_gst_number', 'bill_number', 'po_number',
            'order_by', 'order_for', 'purchased_item', 'hsn_code', 'date_of_purchase',
            'per_unit_cost', 'units_bought', 'cgst_rate', 'sgst_rate', 'igst_rate', 'payment_status',
            'payment_by', 'payment_date', 'payment_mode', 'remark', 'bill_file'
        ]
        widgets = {
            'organization_code': forms.TextInput(attrs={'class': 'form-control'}),
            'organization_name': forms.TextInput(attrs={'class': 'form-control'}),
            'organization_gst_number': forms.TextInput(attrs={'class': 'form-control'}),
            'bill_number': forms.TextInput(attrs={'class': 'form-control'}),
            'purchased_item': forms.TextInput(attrs={'class': 'form-control'}),
            'hsn_code': forms.TextInput(attrs={'class': 'form-control'}),
            'date_of_purchase': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'per_unit_cost': forms.NumberInput(attrs={'class': 'form-control'}),
            'units_bought': forms.NumberInput(attrs={'class': 'form-control'}),
            'cgst_rate': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'placeholder': '0.0'}),
            'sgst_rate': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'placeholder': '0.0'}),
            'igst_rate': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'placeholder': '0.0'}),
            'payment_status': forms.Select(attrs={'class': 'form-select'}),
            'payment_by': forms.TextInput(attrs={'class': 'form-control'}),
            'payment_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'payment_mode': forms.Select(attrs={'class': 'form-select'}),
            'remark': forms.TextInput(attrs={'class': 'form-control'}),
            'bill_file': forms.ClearableFileInput(attrs={'class': 'form-control'}),
            'order_for': forms.Select(attrs={'class': 'form-select'}),
        }

# Formset for handling multiple purchase items
PurchaseItemFormSet = modelformset_factory(
    PurchaseItem,
    form=PurchaseItemForm,
    extra=1,  # Number of additional blank forms to display
    can_delete=True,  # Allow deletion of existing items
)

# New Tabular Purchase Forms
class PurchaseForm(forms.ModelForm):
    class Meta:
        model = Purchase
        fields = [
            'organization_code', 'organization_name', 'organization_gst_number', 
            'bill_number', 'po_number', 'order_by', 'order_for', 'date_of_purchase',
            'cgst_rate', 'sgst_rate', 'igst_rate', 'payment_status', 'payment_by', 
            'payment_date', 'payment_mode', 'amount_paid', 'account_detail', 'transaction_id', 'remark', 'bill_file'
        ]
        widgets = {
            'organization_code': forms.TextInput(attrs={'class': 'form-control', 'readonly': True}),
            'organization_name': forms.TextInput(attrs={'class': 'form-control', 'readonly': True}),
            'organization_gst_number': forms.TextInput(attrs={'class': 'form-control', 'readonly': True}),
            'bill_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '0000'}),
            'po_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '0000'}),
            'order_by': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'NA'}),
            'order_for': forms.Select(attrs={'class': 'form-select'}),
            'date_of_purchase': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'cgst_rate': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'placeholder': '0.0'}),
            'sgst_rate': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'placeholder': '0.0'}),
            'igst_rate': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'placeholder': '0.0'}),
            'payment_status': forms.Select(attrs={'class': 'form-select'}),
            'payment_by': forms.TextInput(attrs={'class': 'form-control', 'placeholder': ''}),
            'payment_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'payment_mode': forms.Select(attrs={'class': 'form-select'}),
            'amount_paid': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'placeholder': '0.00'}),
            'account_detail': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Account detail'}),
            'transaction_id': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Transaction ID (if any)'}),
            'remark': forms.TextInput(attrs={'class': 'form-control'}),
            'bill_file': forms.FileInput(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Set the queryset for order_for to use VendorInformation
        self.fields['order_for'].queryset = VendorInformation.objects.all()
        self.fields['order_for'].empty_label = "Select Vendor"
        
        # Make tax rate fields optional
        self.fields['cgst_rate'].required = False
        self.fields['sgst_rate'].required = False
        self.fields['igst_rate'].required = False
        
        # Set default values for tax rate fields if no instance is provided
        if not self.instance.pk:
            self.fields['cgst_rate'].initial = 0.0
            self.fields['sgst_rate'].initial = 0.0
            self.fields['igst_rate'].initial = 0.0

    def clean(self):
        cleaned_data = super().clean()
        
        # Set empty tax rates to 0
        if not cleaned_data.get('cgst_rate'):
            cleaned_data['cgst_rate'] = 0.0
        if not cleaned_data.get('sgst_rate'):
            cleaned_data['sgst_rate'] = 0.0
        if not cleaned_data.get('igst_rate'):
            cleaned_data['igst_rate'] = 0.0
            
        return cleaned_data

class PurchaseLineItemForm(forms.ModelForm):
    class Meta:
        model = PurchaseLineItem
        fields = ['purchased_item', 'hsn_code', 'per_unit_cost', 'units_bought', 'cgst_rate', 'sgst_rate', 'igst_rate']
        widgets = {
            'purchased_item': forms.TextInput(attrs={'class': 'form-control'}),
            'hsn_code': forms.TextInput(attrs={'class': 'form-control'}),
            'per_unit_cost': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'units_bought': forms.NumberInput(attrs={'class': 'form-control', 'min': '1'}),
            'cgst_rate': forms.NumberInput(attrs={'class': 'form-control form-control-sm', 'step': '0.01', 'min': '0', 'max': '100', 'placeholder': '0'}),
            'sgst_rate': forms.NumberInput(attrs={'class': 'form-control form-control-sm', 'step': '0.01', 'min': '0', 'max': '100', 'placeholder': '0'}),
            'igst_rate': forms.NumberInput(attrs={'class': 'form-control form-control-sm', 'step': '0.01', 'min': '0', 'max': '100', 'placeholder': '0'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Make all fields optional for empty forms
        if not kwargs.get('instance'):
            for field in self.fields.values():
                field.required = False
        
        # Set GST fields as not required and with default values
        self.fields['cgst_rate'].required = False
        self.fields['sgst_rate'].required = False
        self.fields['igst_rate'].required = False

# Formset for handling multiple purchase line items
PurchaseLineItemFormSet = inlineformset_factory(
    Purchase,
    PurchaseLineItem,
    form=PurchaseLineItemForm,
    extra=1,  # Start with one extra form
    can_delete=True,  # Allow deletion of existing items
    min_num=1,  # Require at least one item
    validate_min=True,  # Validate minimum number
    max_num=20,  # Maximum number of items
    validate_max=True,  # Validate maximum number
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

# Adding a Company form
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

#Adding Site
class SiteForm(forms.ModelForm):
    class Meta:
        model = Site
        fields = [
            'site_code', 'site_name',
            'site_address_line1', 'site_address_line2', 'site_city', 'site_state', 'site_pincode',
            'site_gst_number', 'site_account_number', 'site_ifsc_code',
            'site_contact_person_name', 'site_contact_person_number', 'site_contact_person_email',
            'site_pf_code', 'site_esic_code',
            'site_service_charge_salary', 'site_service_charge_over_time',
            'site_salary_component_type', 'site_ot_rule', 'site_bonus_formula',
            'site_pf_deduction', 'site_esic_deduction_rule', 'site_welfare_deduction_rule',
        ]

        widgets = {
            'site_code': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter 4-digit site code'
            }),
            'site_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter site name'
            }),
            'site_address_line1': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Address Line 1'
            }),
            'site_address_line2': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Address Line 2 (optional)'
            }),
            'site_city': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'City'
            }),
            'site_state': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'State'
            }),
            'site_pincode': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Pincode'
            }),
            'site_gst_number': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter GST number'
            }),
            'site_account_number': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter bank account number'
            }),
            'site_ifsc_code': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter IFSC code'
            }),
            'site_contact_person_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter contact person name'
            }),
            'site_contact_person_number': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter 10-digit mobile number'
            }),
            'site_contact_person_email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter email address'
            }),
            'site_pf_code': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter PF code'
            }),
            'site_esic_code': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter ESIC code'
            }),
            'site_service_charge_salary': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g. 5 for 5%'
            }),
            'site_service_charge_over_time': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g. 7.5 for 7.5%'
            }),
            'site_salary_component_type': forms.Select(attrs={
                'class': 'form-control'
            }),
            'site_ot_rule': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g. 2x for double rate OT'
            }),
            'site_bonus_formula': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Bonus calculation rule (if any)'
            }),
            'site_pf_deduction': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'PF deduction rule'
            }),
            'site_esic_deduction_rule': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'ESIC deduction rule'
            }),
            'site_welfare_deduction_rule': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Welfare fund rule'
            }),
        }

    def clean_site_code(self):
        site_code = self.cleaned_data.get('site_code', '').strip()
        if len(site_code) != 4:
            raise forms.ValidationError("Site code must be exactly 4 characters long.")
        return site_code.upper()

    def clean_site_contact_person_number(self):
        number = self.cleaned_data.get('site_contact_person_number', '')
        if not number.isdigit() or len(number) < 10 or len(number) > 15:
            raise forms.ValidationError("Contact number must be between 10 and 15 digits.")
        return number

    def clean_site_ifsc_code(self):
        code = self.cleaned_data.get('site_ifsc_code', '').strip()
        if code and len(code) != 11:
            raise forms.ValidationError("IFSC code must be exactly 11 characters long.")
        return code.upper()

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





# Upload form for attendance, advance, and arrears
class UploadForm(forms.Form):
    site = forms.ModelChoiceField(queryset=Site.objects.all(), required=True, label="Select Site", widget=forms.Select(attrs={'class': 'form-control'}))
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

# E invoice forms
class EInvoiceForm(forms.ModelForm):
    class Meta:
        model = EInvoice
        fields = [
            # Invoice Basic Information
            'invoice_number', 'invoice_date', 'invoice_type', 'document_type', 'reverse_charge',
            
            # Supplier Information
            'supplier_gstin', 'supplier_legal_name', 'supplier_address', 'supplier_place_of_supply', 'supplier_state_code',
            
            # Buyer Information
            'buyer_gstin', 'buyer_legal_name', 'buyer_address', 'buyer_state_code',
            
            # Additional Information
            'dispatch_from_address', 'shipping_address', 'payment_terms', 'due_date', 'reference_document',
            
            # Transporter Details
            'transporter_name', 'transporter_id', 'vehicle_number'
        ]
        widgets = {
            'invoice_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'due_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'invoice_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter invoice number'}),
            'invoice_type': forms.Select(attrs={'class': 'form-select'}),
            'document_type': forms.Select(attrs={'class': 'form-select'}),
            'reverse_charge': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            
            # Supplier fields
            'supplier_gstin': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '22AAAAA0000A1Z5', 'maxlength': '15'}),
            'supplier_legal_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter supplier legal name'}),
            'supplier_address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Enter supplier address'}),
            'supplier_place_of_supply': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter place of supply'}),
            'supplier_state_code': forms.Select(attrs={'class': 'form-select'}),
            
            # Buyer fields
            'buyer_gstin': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '22AAAAA0000A1Z5', 'maxlength': '15'}),
            'buyer_legal_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter buyer legal name'}),
            'buyer_address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Enter buyer address'}),
            'buyer_state_code': forms.Select(attrs={'class': 'form-select'}),
            
            # Additional fields
            'dispatch_from_address': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Enter dispatch address'}),
            'shipping_address': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Enter shipping address'}),
            'payment_terms': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., Net 30 days'}),
            'reference_document': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., PO Number'}),
            
            # Transporter fields
            'transporter_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter transporter name'}),
            'transporter_id': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter transporter ID'}),
            'vehicle_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter vehicle number'}),
        }


class EInvoiceLineItemForm(forms.ModelForm):
    class Meta:
        model = EInvoiceLineItem
        fields = [
            'product_service_name', 'hsn_sac_code', 'quantity', 'unit_price',
            'cgst_rate', 'sgst_rate', 'igst_rate'
        ]
        widgets = {
            'product_service_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter product/service name'}),
            'hsn_sac_code': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter HSN/SAC code'}),
            'quantity': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.001', 'placeholder': '1.000'}),
            'unit_price': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'placeholder': '0.00'}),
            'cgst_rate': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0', 'max': '100', 'placeholder': '0.00'}),
            'sgst_rate': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0', 'max': '100', 'placeholder': '0.00'}),
            'igst_rate': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0', 'max': '100', 'placeholder': '0.00'}),
        }

# Formset for handling multiple line items
EInvoiceLineItemFormSet = modelformset_factory(
    EInvoiceLineItem,
    form=EInvoiceLineItemForm,
    extra=1,  # Number of additional blank forms to display
    can_delete=True,  # Allow deletion of existing items
)

from .models import MONTH_CHOICES

class ReportForm(forms.ModelForm):
    class Meta:
        model = Report
        fields = ['site', 'report_type', 'month', 'year']
        widgets = {
            'month': forms.Select(attrs={'class': 'form-control'}),
            'year': forms.NumberInput(attrs={'class': 'form-control', 'min': '2000', 'max': '2100'}),
            'site': forms.Select(attrs={'class': 'form-control'}),
            'report_type': forms.Select(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Add choices for month field
        self.fields['month'].choices = MONTH_CHOICES
        # Set current year as initial value
        from datetime import datetime
        current_year = datetime.now().year
        self.fields['year'].initial = current_year


# Bill Template Forms
class BillTemplateForm(forms.ModelForm):
    class Meta:
        model = BillTemplate
        fields = [
            'template_name', 'description', 'default_hsn_code',
            'esi_rate', 'service_charge_rate', 'cgst_rate', 'sgst_rate', 'igst_rate',
            'apply_esi', 'apply_service_charge', 'apply_cgst_sgst', 'apply_igst',
            'round_to_nearest', 'is_default', 'is_active', 'site'
        ]
        widgets = {
            'template_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., Monthly Manpower Service'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Description of when to use this template'}),
            'default_hsn_code': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '998519'}),
            
            # Tax rates
            'esi_rate': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0', 'max': '100', 'placeholder': '3.25'}),
            'service_charge_rate': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0', 'max': '100', 'placeholder': '6.00'}),
            'cgst_rate': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0', 'max': '100', 'placeholder': '0.0'}),
            'sgst_rate': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0', 'max': '100', 'placeholder': '0.0'}),
            'igst_rate': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0', 'max': '100', 'placeholder': '0.0'}),
            
            # Checkboxes
            'apply_esi': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'apply_service_charge': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'apply_cgst_sgst': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'apply_igst': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'is_default': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            
            # Rounding
            'round_to_nearest': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0.01', 'placeholder': '0.01'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        apply_cgst_sgst = cleaned_data.get('apply_cgst_sgst')
        apply_igst = cleaned_data.get('apply_igst')
        
        # Ensure only one tax type is selected
        if apply_cgst_sgst and apply_igst:
            raise ValidationError("Cannot apply both CGST/SGST and IGST. Please select only one.")
        
        return cleaned_data


class ServiceBillForm(forms.ModelForm):
    class Meta:
        model = ServiceBill
        fields = [
            'bill_number', 'bill_date', 'template', 'client_name', 'client_address',
            'client_gst_number', 'status', 'site'
        ]
        widgets = {
            'bill_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Auto-generated if blank'}),
            'bill_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'template': forms.Select(attrs={'class': 'form-select'}),
            'client_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter client name'}),
            'client_address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Enter client address'}),
            'client_gst_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '22AAAAA0000A1Z5', 'maxlength': '15'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'site': forms.Select(attrs={'class': 'form-select'}),
        }

    def __init__(self, *args, **kwargs):
        site = kwargs.pop('site', None)
        super().__init__(*args, **kwargs)
        
        if not self.instance.pk:
            self.fields['status'].initial = 'draft'
        
        self.fields['status'].required = False
        
        if site:
            self.fields['template'].queryset = BillTemplate.objects.filter(site=site, is_active=True)
        else:
            self.fields['template'].queryset = BillTemplate.objects.filter(is_active=True)
        
        self.fields['template'].empty_label = "Select Template"
        
        choices = []
        for template in self.fields['template'].queryset:
            choices.append((template.pk, {
                'label': template.template_name,
                'data-cgst-rate': str(template.cgst_rate),
                'data-sgst-rate': str(template.sgst_rate),
                'data-igst-rate': str(template.igst_rate),
                'data-apply-cgst-sgst': template.apply_cgst_sgst,
                'data-apply-igst': template.apply_igst,
            }))
        
        self.fields['template'].choices = [("", "Select Template")] + [
            (pk, attrs['label']) for pk, attrs in choices
        ]
        
        self.fields['template'].widget.choices = self.fields['template'].choices
        self.fields['template'].widget.attrs.update({
            'data-options': json.dumps({pk: attrs for pk, attrs in choices})
        })


class ServiceBillItemForm(forms.ModelForm):
    class Meta:
        model = ServiceBillItem
        fields = [
            'description', 'hsn_code', 'amount'
        ]
        widgets = {
            'description': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., Manpower Supply'}),
            'hsn_code': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'HSN'}),
            'amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'placeholder': '0.00'}),
        }


# Formset for handling multiple service bill items
ServiceBillItemFormSet = modelformset_factory(
    ServiceBillItem,
    form=ServiceBillItemForm,
    extra=1,  # Number of additional blank forms to display
    can_delete=True,  # Allow deletion of existing items
)
