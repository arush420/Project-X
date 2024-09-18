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
        days_worked = request.POST.get('days_worked')
        days_in_month = request.POST.get('days_in_month')

        # Ensure values are provided and convert them to integers
        if not days_worked or not days_in_month:
            # If input is missing, render the form again with an error message
            return render(request, 'employees/generate_salary.html', {
                'error': 'Please enter both days worked and number of days in the month.'
            })

        try:
            days_worked = int(days_worked)
            days_in_month = int(days_in_month)
        except ValueError:
            # Handle case where the inputs are not valid integers
            return render(request, 'employees/generate_salary.html', {
                'error': 'Invalid input. Please enter valid numbers for days worked and days in the month.'
            })

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

            # Round the gross and net salary to 2 decimal places
            gross_salary = round(gross_salary, 2)
            net_salary = round(net_salary, 2)

            salary_data.append({
                'employee_code': employee.employee_code,
                'name': employee.name,
                'gross_salary': f'{gross_salary:.2f}',  # Format with 2 decimal places
                'net_salary': f'{net_salary:.2f}',  # Format with 2 decimal places
            })

        return render(request, 'employees/salary_report.html', {'salary_data': salary_data})

    # Render the form when the page is first loaded or if there's an error
    return render(request, 'employees/generate_salary.html')

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
