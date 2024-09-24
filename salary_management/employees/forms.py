from django import forms
from .models import Employee, Task

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