from django.shortcuts import render, get_object_or_404, redirect
from .models import Employee, Salary
from datetime import datetime
from .forms import EmployeeForm
from django.db.models import Q  # For complex queries (like searching multiple fields)


def employee_list(request):
    search_query = request.GET.get('search', '')  # Get the search term from the request

    # Filter the employees based on the search query (searching in both employee_code and name)
    if search_query:
        employees = Employee.objects.filter(
            Q(employee_code__icontains=search_query) | Q(name__icontains=search_query)
        )
    else:
        employees = Employee.objects.all()  # If no search query, return all employees

    return render(request, 'employees/employee_list.html', {'employees': employees, 'search_query': search_query})


def generate_salary(request):
    if request.method == 'POST':
        days_in_month = request.POST.get('days_in_month')

        if not days_in_month:
            return render(request, 'employees/generate_salary.html', {
                'error': 'Please enter the number of days in the month.'
            })

        try:
            days_in_month = int(days_in_month)
        except ValueError:
            return render(request, 'employees/generate_salary.html', {
                'error': 'Invalid input for number of days in the month.'
            })

        employees = Employee.objects.all()
        salary_data = []
        total_net_salary = 0

        for employee in employees:
            days_worked = request.POST.get(f'days_worked_{employee.id}')

            if not days_worked:
                days_worked = 0
            else:
                try:
                    days_worked = int(days_worked)
                except ValueError:
                    days_worked = 0

            basic = employee.basic
            transport = employee.transport
            canteen = employee.canteen
            pf_percentage = employee.pf
            esic_percentage = employee.esic

            gross_salary = ((basic + transport) / days_in_month) * days_worked
            pf_amount = (pf_percentage / 100) * basic
            esic_amount = (esic_percentage / 100) * basic
            net_salary = gross_salary - (canteen + pf_amount + esic_amount)

            gross_salary = round(gross_salary, 2)
            net_salary = round(net_salary, 2)

            salary_data.append({
                'employee_code': employee.employee_code,
                'name': employee.name,
                'gross_salary': f'{gross_salary:.2f}',
                'net_salary': f'{net_salary:.2f}',
            })

            total_net_salary += net_salary

        return render(request, 'employees/salary_report.html', {
            'salary_data': salary_data,
            'total_net_salary': f'{total_net_salary:.2f}'
        })

    employees = Employee.objects.all()
    return render(request, 'employees/generate_salary.html', {'employees': employees})
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
