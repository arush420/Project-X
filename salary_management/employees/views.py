from django.shortcuts import render, redirect, get_object_or_404
from .models import Employee, Salary, Task, Profile
from django.db.models import Q
from django.utils import timezone
from .forms import EmployeeForm, TaskForm, ExcelUploadForm, PaymentForm
from django.views import View
from django.views.generic import ListView
from django.urls import reverse_lazy
import pandas as pd


class EmployeeListView(ListView):
    model = Employee
    template_name = 'employees/employee_list.html'
    context_object_name = 'employees'

    def get_queryset(self):
        search_query = self.request.GET.get('search', '')
        if search_query:
            return Employee.objects.filter(
                Q(employee_code__icontains=search_query) | Q(name__icontains=search_query)
            )
        return Employee.objects.all()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search_query'] = self.request.GET.get('search', '')
        return context


class GenerateSalaryView(View):
    template_name = 'employees/generate_salary.html'


    def get(self, request):
        return self.render_salary_form()

    def post(self, request):
        month, year, days_in_month = self.get_salary_params(request)

        if not month or not year or not days_in_month:
            return self.render_error('Please provide all inputs: month, year, and days in the month.')

        try:
            month, year, days_in_month = int(month), int(year), int(days_in_month)
        except ValueError:
            return self.render_error('Invalid input for month, year, or days in month.')

        employees = Employee.objects.all()
        salary_data, total_net_salary = self.calculate_salaries(request, employees, days_in_month, month, year)

        return render(request, 'employees/salary_report.html', {
            'salary_data': salary_data,
            'total_net_salary': f'{total_net_salary:.2f}',
            'month': month,
            'year': year
        })

    def get_salary_params(self, request):
        """Helper function to extract and validate POST parameters."""
        month = request.POST.get('month')
        year = request.POST.get('year')
        days_in_month = request.POST.get('days_in_month')
        return month, year, days_in_month

    def render_salary_form(self, error=None):
        """Helper method to render the salary form with employees and months."""
        employees = Employee.objects.all()
        current_year = timezone.now().year
        months = range(1, 13)
        context = {
            'employees': employees,
            'current_year': current_year,
            'months': months,
        }
        if error:
            context['error'] = error
        return render(self.request, self.template_name, context)

    def render_error(self, error_message):
        """Helper method to render an error message."""
        return self.render_salary_form(error=error_message)

    def calculate_salaries(self, request, employees, days_in_month, month, year):
        salary_data = []
        total_net_salary = 0

        for employee in employees:
            days_worked = request.POST.get(f'days_worked_{employee.id}', 0)
            try:
                days_worked = int(days_worked)
            except ValueError:
                days_worked = 0

            gross_salary, net_salary = self.calculate_salary(employee, days_worked, days_in_month)

            Salary.objects.update_or_create(
                employee=employee, month=month, year=year,
                defaults={
                    'gross_salary': gross_salary,
                    'net_salary': net_salary,
                    'date_generated': timezone.now()
                }
            )

            salary_data.append({
                'employee_code': employee.employee_code,
                'name': employee.name,
                'gross_salary': f'{gross_salary:.2f}',
                'net_salary': f'{net_salary:.2f}',
            })

            total_net_salary += net_salary

        return salary_data, total_net_salary


    def calculate_salary(self, employee, days_worked, days_in_month):
        if days_in_month <= 0:
            raise ValueError("Days in month must be greater than 0.")
        if days_worked > days_in_month:
            days_worked = days_in_month # Cap days worked to days in month
            print("Number of days work exceed working days in month. Hence days worked = working days ")

        basic, transport, canteen = employee.basic, employee.transport, employee.canteen
        pf_percentage, esic_percentage = employee.pf, employee.esic

        # Calculate gross salary based on days worked
        gross_salary = ((basic + transport) / days_in_month) * days_worked

        # Calculate PF and ESIC amounts
        pf_amount = (pf_percentage / 100) * basic
        esic_amount = (esic_percentage / 100) * basic

        # Calculate net salary by subtracting deductions
        net_salary = gross_salary - (canteen + pf_amount + esic_amount)

        return round(gross_salary, 2), round(net_salary, 2)


def home(request):
    total_employees = Employee.objects.count()  # Fetch the count of employees
    tasks = Task.objects.all()

    if request.method == 'POST':
        form = TaskForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('home')
    else:
        form = TaskForm()

    context = {
        'total_employees': total_employees,
        'tasks': tasks,
        'form': form
    }

    return render(request, 'employees/home.html', context)  # Pass the entire context

def add_task(request):
    if request.method == 'POST':
        title = request.POST.get('title')
        Task.objects.create(title=title)
    return redirect('home')  # Redirect back to home after task is added

def complete_task(request, task_id):
    task = get_object_or_404(Task, id=task_id)
    task.completed = not task.completed  # Toggle the completion status
    task.save()
    return redirect('home')

def delete_task(request, task_id):
    task = get_object_or_404(Task, id=task_id)
    task.delete()
    return redirect('home')

def add_employee(request):
    if request.method == 'POST':
        form = EmployeeForm(request.POST)
        if form.is_valid():
            form.save()  # Save the new employee to the database
            return redirect('employees:employee_list')  # Redirect to employee list after successful addition
    else:
        form = EmployeeForm()

    return render(request, 'employees/add_employee.html', {'form': form})


def handle_uploaded_file(f):
    # Use Pandas to read the uploaded Excel file
    df = pd.read_excel(f, engine='openpyxl')

    # Perform predefined operations on the DataFrame (df)
    # For example, summing up a specific column or filtering rows
    # Example operation: Calculate the sum of a 'Salary' column
    if 'Salary' in df.columns:
        total_salary = df['Salary'].sum()
    else:
        total_salary = None

    # Perform other operations as needed
    return total_salary


def upload_excel(request):
    if request.method == 'POST':
        form = ExcelUploadForm(request.POST, request.FILES)
        if form.is_valid():
            total_salary = handle_uploaded_file(request.FILES['excel_file'])
            return render(request, 'upload_success.html', {'total_salary': total_salary})
    else:
        form = ExcelUploadForm()
    return render(request, 'employees/upload_excel.html', {'form': form})


def profile_detail(request):
    # Assuming there's only one profile; if there are many, you can modify the logic.
    profile = get_object_or_404(Profile, id=1)  # Retrieve the profile with id=1 (modify as needed)
    return render(request, 'profile_detail.html', {'profile': profile})


def payment_input(request):
    if request.method == 'POST':
        form = PaymentForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('payment_success')  # Redirect to a success page or somewhere else
    else:
        form = PaymentForm()

    return render(request, 'payment_input.html', {'form': form})

def payment_success(request):
    return render(request, 'payment_success.html')