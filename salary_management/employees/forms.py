from django import forms
from .models import Employee, Task, Payment

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