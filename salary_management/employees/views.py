from django.shortcuts import render, get_object_or_404, redirect
from .models import Employee, Salary
from datetime import datetime
from .forms import EmployeeForm


def employee_list(request):
    employees = Employee.objects.all()
    return render(request, 'employees/employee_list.html', {'employees': employees})


def generate_salary(request):
    if request.method == 'POST':
        # Get the number of days worked and number of days in the month from the form
        days_worked = int(request.POST.get('days_worked'))
        days_in_month = int(request.POST.get('days_in_month'))

        employees = Employee.objects.all()
        salary_data = []

        for employee in employees:
            basic = employee.basic
            transport = employee.transport
            canteen = employee.canteen
            pf_percentage = employee.pf  # Assume `pf` is the percentage (e.g., 12 for 12%)
            esic_percentage = employee.esic  # Assume `esic` is the percentage (e.g., 1 for 1%)

            # Gross Salary Calculation: ((basic + transport) / days_in_month) * days_worked
            gross_salary = ((basic + transport) / days_in_month) * days_worked

            # PF and ESIC calculation
            pf_amount = (pf_percentage / 100) * basic
            esic_amount = (esic_percentage / 100) * basic

            # Net Salary Calculation: Gross Salary - (canteen + pf + esic)
            net_salary = gross_salary - (canteen + pf_amount + esic_amount)

            salary_data.append({
                'employee_code': employee.employee_code,
                'name': employee.name,
                'gross_salary': gross_salary,
                'net_salary': net_salary
            })

        return render(request, 'employees/salary_report.html', {'salary_data': salary_data})

    return render(request, 'employees/generate_salary.html')  # Display the form initially

def home(request):
    return render(request, 'employees/home.html')


def add_employee(request):
    if request.method == 'POST':
        form = EmployeeForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('employee_list')  # Redirect to the employee list after saving
    else:
        form = EmployeeForm()
    return render(request, 'employees/add_employee.html', {'form': form})
