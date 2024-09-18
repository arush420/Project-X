from django.shortcuts import render, get_object_or_404, redirect
from .models import Employee, Salary
from datetime import datetime


def employee_list(request):
    employees = Employee.objects.all()
    return render(request, 'employees/employee_list.html', {'employees': employees})


def generate_salary(request):
    employees = Employee.objects.all()
    if request.method == 'POST':
        month = datetime.now()
        for employee in employees:
            days_worked = int(request.POST.get(f'days_worked_{employee.id}', 0))
            total_salary = (employee.basic / 30) * days_worked + employee.transport - employee.canteen
            advance_deducted = employee.advance
            final_salary = total_salary - advance_deducted

            Salary.objects.create(
                employee=employee,
                month=month,
                days_worked=days_worked,
                total_salary=total_salary,
                advance_deducted=advance_deducted,
                final_salary=final_salary
            )
            employee.advance = 0
            employee.save()

        return redirect('salary_list')

    return render(request, 'employees/generate_salary.html', {'employees': employees})


def home(request):
    return render(request, 'employees/home.html')