from django import forms
from .models import Employee, Task, Payment, PurchaseItem, VendorInformation, Company, Profile
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.contrib.auth.models import User


USER_TYPE_CHOICES = [
    ('Owner', 'Owner'),
    ('Manager', 'Manager'),
    ('Employee', 'Employee'),
]


class CustomUserCreationForm(UserCreationForm):
    first_name = forms.CharField(max_length=30, required=True)
    last_name = forms.CharField(max_length=30, required=True)
    user_type = forms.ChoiceField(choices=USER_TYPE_CHOICES, required=True)

    company_name = forms.ModelChoiceField(queryset=Company.objects.all(),
                                          required=False, empty_label="Select Company")


    class Meta:
        model = User
        fields = ('username', 'password1', 'password2', 'first_name', 'last_name', 'user_type', 'company_name')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Adding "Other" option manually to company_name
        self.fields['company_name'].choices = list(self.fields['company_name'].choices) + [("Other", "Other")]

    def clean_gst_number(self):
        gst_number = self.cleaned_data.get('gst_number')
        if gst_number and not re.match(r'\d{2}[A-Z]{5}\d{4}[A-Z]{1}[A-Z\d]{1}[Z]{1}[A-Z\d]{1}', gst_number):
            raise forms.ValidationError("Invalid GST number format.")
        return gst_number

    def clean_ifsc_code(self):
        ifsc_code = self.cleaned_data.get('ifsc_code')
        if ifsc_code and not re.match(r'^[A-Za-z]{4}\d{7}$', ifsc_code):
            raise forms.ValidationError("Invalid IFSC code format.")
        return ifsc_code

    def clean(self):
        cleaned_data = super().clean()
        user_type = cleaned_data.get('user_type')

        if user_type == 'Owner':
            # Validate Owner-specific fields
            organisation_name = cleaned_data.get('organisation_name')
            account_number = cleaned_data.get('account_number')
            confirm_account_number = cleaned_data.get('confirm_account_number')
            if account_number and confirm_account_number and account_number != confirm_account_number:
                self.add_error('confirm_account_number', 'Account numbers do not match.')
        return cleaned_data


class LoginForm(AuthenticationForm):
    username = forms.CharField(max_length=254, widget=forms.TextInput(attrs={'class': 'form-control'}))
    password = forms.CharField(label="Password", widget=forms.PasswordInput(attrs={'class': 'form-control'}))

class EmployeeForm(forms.ModelForm):
    class Meta:
        model = Employee
        fields = ['employee_code', 'name', 'father_name', 'basic', 'transport', 'canteen', 'pf', 'esic', 'advance']

class ExcelUploadForm(forms.Form):
    file = forms.FileField()

class EmployeeSearchForm(forms.Form):
    employee_code_or_name = forms.CharField(label='Employee Code or Name', max_length=100)


class TaskForm(forms.ModelForm):
    class Meta:
        model = Task
        fields = ['title']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Add new task'})
        }


class PaymentForm(forms.ModelForm):
    payment_date = forms.DateField(widget=forms.SelectDateWidget)
    class Meta:
        model = Payment
        fields = ['company_name', 'amount_received', 'payment_date', 'account_of_own_company', 'payment_against_bill']


class PurchaseItemForm(forms.ModelForm):
    date_of_purchase = forms.DateField(widget=forms.SelectDateWidget)

    class Meta:
        model = PurchaseItem
        fields = [
            'organization_code', 'organization_name', 'gst_number', 'bill_number',
            'purchased_item', 'category', 'hsn_code', 'date_of_purchase',
            'per_unit_cost', 'units_bought', 'cgst_rate', 'sgst_rate', 'igst_rate'
        ]
# Adding Vendor forms
class VendorInformationForm(forms.ModelForm):
    class Meta:
        model = VendorInformation
        fields = [
            'vendor_id', 'firm_code', 'vendor_name', 'vendor_address', 'vendor_gst_number', 'vendor_account_number',
            'vendor_ifsc_code', 'vendor_contact_person_name', 'vendor_contact_person_number'
        ]


# Adding company name to the main list
class CompanyForm(forms.ModelForm):
    class Meta:
        model = Company
        fields = ['company_code', 'company_name', 'company_address', 'company_gst_number', 'company_account_number',
                  'company_ifsc_code', 'company_contact_person_name', 'company_contact_person_number']


class AddCompanyForm(forms.Form):
    company_code = forms.CharField(max_length=4)
    company_name = forms.CharField(max_length=100)
    company_address = forms.CharField(widget=forms.Textarea)
    company_gst_number = forms.CharField(max_length=20)
    company_account_number = forms.CharField(max_length=20)
    company_ifsc_code = forms.CharField(max_length=11)
    company_contact_person_name = forms.CharField(max_length=100)
    company_contact_person_number = forms.CharField(max_length=10)

    def clean_company_gst_number(self):
        gst_number = self.cleaned_data.get('company_gst_number')
        if gst_number and not re.match(r'\d{2}[A-Z]{5}\d{4}[A-Z]{1}[A-Z\d]{1}[Z]{1}[A-Z\d]{1}', gst_number):
            raise forms.ValidationError("Invalid GST number format.")
        return gst_number

    def clean_company_ifsc_code(self):
        ifsc_code = self.cleaned_data.get('company_ifsc_code')
        if ifsc_code and not re.match(r'^[A-Za-z]{4}\d{7}$', ifsc_code):
            raise forms.ValidationError("Invalid IFSC code format.")
        return ifsc_code
