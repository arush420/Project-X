from django import forms
from .models import Employee, Task, Payment, PurchaseItem, VendorInformation, Company
from django.contrib.auth.forms import AuthenticationForm


class EmployeeForm(forms.ModelForm):
    class Meta:
        model = Employee
        fields = ['employee_code', 'name', 'father_name', 'basic', 'transport', 'canteen', 'pf', 'esic', 'advance']


class TaskForm(forms.ModelForm):
    class Meta:
        model = Task
        fields = ['title']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Add new task'})
        }


class ExcelUploadForm(forms.Form):
    excel_file = forms.FileField()


class PaymentForm(forms.ModelForm):
    payment_date = forms.DateField(widget=forms.SelectDateWidget)
    class Meta:
        model = Payment
        fields = ['company_name', 'amount_received', 'payment_date', 'account_of_own_company', 'payment_against_bill']


class LoginForm(AuthenticationForm):
    username = forms.CharField(max_length=254, widget=forms.TextInput(attrs={'class': 'form-control'}))
    password = forms.CharField(label="Password", widget=forms.PasswordInput(attrs={'class': 'form-control'}))


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
        fields = ['name']


class AddCompanyForm(forms.Form):
    new_company_name = forms.CharField(max_length=100)

