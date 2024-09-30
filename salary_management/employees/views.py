from django.shortcuts import render, redirect, get_object_or_404
from .models import Employee, Salary, Task, Profile, Payment, PurchaseItem, VendorInformation, MONTH_CHOICES, Company
from django.db.models import Q
from django.utils import timezone
from .forms import EmployeeForm, TaskForm, ExcelUploadForm, PaymentForm, PurchaseItemForm, VendorInformationForm, \
    CompanyForm, AddCompanyForm
from django.views import View
from django.views.generic import ListView
from django.urls import reverse_lazy
import pandas as pd
from django.core.files.storage import FileSystemStorage
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth import login, logout
from django.http import HttpResponseRedirect, HttpResponse
from django.urls import reverse
from django.contrib import messages
import csv


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


def employee_detail(request, employee_code):
    employee = get_object_or_404(Employee, employee_code=employee_code)
    return render(request, 'employee_detail.html', {'employee': employee})

def employee_search(request):
    if request.method == "POST":
        employee_code = request.POST.get('employee_code')
        return HttpResponseRedirect(reverse('employees:employee_detail', args=[employee_code]))
    return render(request, 'employees/employee_search.html')


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
    tasks = Task.objects.all() #this ensures tasks are retrived from the database
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
            excel_file = request.FILES['file']

            # Load the Excel file using pandas
            try:
                df = pd.read_excel(excel_file)

                # Iterate over the rows and create Employee objects
                for _, row in df.iterrows():
                    Employee.objects.create(
                        employee_code=row['employee_code'],
                        name=row['name'],
                        designation=row['designation'],
                        salary=row['salary'],
                        department=row['department'],
                    )
                messages.success(request, 'Employees added successfully!')
                return redirect('employees:employee_list')
            except Exception as e:
                messages.error(request, f'Error processing file: {e}')
    else:
        form = ExcelUploadForm()

    return render(request, 'employees/upload_excel.html', {'form': form})


def profile_detail(request):
    # Assuming there's only one profile; if there are many, you can modify the logic.
    profile = get_object_or_404(Employee, employee_code="001")  # Retrieve the profile with id=1 (modify as needed) 
    return render(request, 'employees/profile_detail.html', {'profile': profile})


def payment_input(request):
    if request.method == 'POST':
        form = PaymentForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('employees:payment_input')  # Redirect to a success page or somewhere else
    else:
        form = PaymentForm()

    payments = Payment.objects.all()  # Fetch all payment records

    return render(request, 'employees/payment_input.html', {'form': form, 'payments': payments})

#Registering a user
def register_view(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('dashboard')
    else:
        initial_data = {'username':'', 'passowrd1':'', 'password2':''}
        form = UserCreationForm(initial=initial_data)
    return render(request, 'employees/register.html', {'form': form})



def login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect('dashboard')
    else:
        initial_data = {'username': '', 'passowrd': ''}
        form = AuthenticationForm(initial=initial_data)
    return render(request, 'employees/login.html', {'form': form})

def dashboard_view(request):
    return render(request, 'employees/dashboard.html')

def logout_view(request):
    logout(request)
    return redirect('login')


def purchase_item_input(request):
    if request.method == 'POST':
        form = PurchaseItemForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('employees:purchase_item_input')  # Redirect after saving the form
    else:
        form = PurchaseItemForm()

    # Retrieve all purchases from the database
    purchases = PurchaseItem.objects.all()

    return render(request, 'employees/purchase_item_input.html', {'form': form, 'purchases': purchases})


def vendor_information_input(request):
    if request.method == 'POST':
        form = VendorInformationForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('employees:vendor_information_input')  # Redirect after saving the form
    else:
        form = VendorInformationForm()

    # Retrieve all vendor information from the database
    vendor_information = VendorInformation.objects.all()

    return render(request, 'employees/vendor_information_input.html', {'form': form, 'vendor_information': vendor_information})


def company_list(request):
    companies = Company.objects.all()
    company_form = CompanyForm()
    add_company_form = AddCompanyForm()

    if request.method == 'POST':
        if 'add_company' in request.POST:
            add_company_form = AddCompanyForm(request.POST)
            if add_company_form.is_valid():
                new_company_name = add_company_form.cleaned_data['new_company_name']
                Company.objects.create(name=new_company_name)
                return redirect('company_list')
        else:
            company_form = CompanyForm(request.POST)
            if company_form.is_valid():
                company_form.save()
                return redirect('company_list')

    context = {
        'companies': companies,
        'company_form': company_form,
        'add_company_form': add_company_form,
    }
    return render(request, 'employees/company_list.html', context)


def salary_list(request):
    month = request.GET.get('month')
    year = request.GET.get('year')

    # Start with all salaries
    salaries = Salary.objects.select_related('employee').all()

    # Apply filters if month and year are provided
    if month:
        salaries = salaries.filter(month=month)
    if year:
        salaries = salaries.filter(year=year)

    context = {
        'salaries': salaries,
        'month': month,
        'year': year,
        'month_choices': MONTH_CHOICES,  # Pass the MONTH_CHOICES to the template
    }

    return render(request, 'employees/salary_list.html', context)

# to download salary report
def download_salary_csv(request):
    month = request.GET.get('month')
    year = request.GET.get('year')

    # Start with all salaries
    salaries = Salary.objects.select_related('employee').all()

    # Apply filters if month and year are provided
    if month:
        salaries = salaries.filter(month=month)
    if year:
        salaries = salaries.filter(year=year)

    # Create the HttpResponse object with CSV header
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="salaries.csv"'

    writer = csv.writer(response)
    # Write header row
    writer.writerow(['Employee Name', 'Month', 'Year', 'Gross Salary', 'Net Salary', 'Date Generated'])

    # Write data rows
    for salary in salaries:
        writer.writerow([
            salary.employee.name,
            salary.get_month_display(),
            salary.year,
            salary.gross_salary,
            salary.net_salary,
            salary.date_generated
        ])

    return response