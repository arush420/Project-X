from decimal import Decimal
from sqlite3 import IntegrityError

from django.core.exceptions import ValidationError
from django.shortcuts import render, redirect, get_object_or_404
from .models import Employee, Salary, Task, Profile, Payment, PurchaseItem, VendorInformation, MONTH_CHOICES, Company
from django.db.models import Q, Sum
from django.utils import timezone
from .forms import EmployeeForm, TaskForm, ExcelUploadForm, PaymentForm, PurchaseItemForm, VendorInformationForm, \
    CompanyForm, AddCompanyForm, EmployeeSearchForm
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
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm


# Registering a user with unique username validation
def register_view(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            try:
                user = form.save()
                Profile.objects.create(user=user)  # Create a profile for the user
                login(request, user)
                return redirect('home')  # Redirect to home page after registration
            except IntegrityError:
                form.add_error('username', 'Username already exists. Please try another.')
    else:
        form = UserCreationForm()

    return render(request, 'employees/register.html', {'form': form})


# Logging in a user
def login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect('employees:home')  # Redirect to home page after login
    else:
        form = AuthenticationForm()

    return render(request, 'employees/login.html', {'form': form})


def logout_view(request):
    logout(request)
    return redirect('login')

# Dashboard (can be customized for both admin and user dashboards)
def dashboard_view(request):
    return render(request, 'employees/dashboard.html')

# Profile Detail View (show data entered during registration)
def user_profile_detail(request):
    profile = get_object_or_404(Profile, user=request.user)
    return render(request, 'employees/user_profile_detail.html', {'profile': profile})

#creating a custom admin dashboard
def admin_dashboard(request):
    total_employees = Employee.objects.count()
    total_salary = Salary.objects.aggregate(Sum('net_salary'))['net_salary__sum']
    recent_salaries = Salary.objects.order_by('-date_generated')[:10]
    context = {
        'total_employees': total_employees,
        'total_salary': total_salary,
        'recent_salaries': recent_salaries
    }
    return render(request, 'admin_dashboard.html', context)


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


class EmployeeListView(ListView):
    model = Employee
    template_name = 'employees/employee_list.html'
    context_object_name = 'employees'

    def get_queryset(self):
        search_query = self.request.GET.get('search', '')
        return Employee.objects.filter(
            Q(employee_code__icontains=search_query) | Q(name__icontains=search_query)
        ) if search_query else Employee.objects.all()


def employee_detail(request, employee_code):
    employee = get_object_or_404(Employee, employee_code=employee_code)
    return render(request, 'employee_detail.html', {'employee': employee})


def handle_file_upload(file):
    df = pd.read_excel(file)
    for _, row in df.iterrows():
        if Employee.objects.filter(employee_code=row['employee_code']).exists():
            continue
        Employee.objects.create(
            employee_code=row['employee_code'],
            name=row['name'],
            father_name=row['father_name'],
            basic=row['basic'],
            transport=row['transport'],
            canteen=row['canteen'],
            pf=row['pf'],
            esic=row['esic'],
            advance=row['advance']
        )


import pandas as pd
from decimal import Decimal
from django.core.exceptions import ValidationError

def handle_file_upload(file):
    try:
        df = pd.read_excel(file)

        # Required columns in the uploaded Excel file
        required_columns = ['employee_code', 'name', 'father_name', 'basic', 'transport', 'canteen', 'pf', 'esic', 'advance']

        # Check if all required columns are present in the file
        for col in required_columns:
            if col not in df.columns:
                raise ValidationError(f"Missing required column: {col}")

        # Iterate through the rows and save employees
        for _, row in df.iterrows():
            # Validate and convert data before saving
            try:
                employee_code = str(row['employee_code']).strip()
                name = str(row['name']).strip()
                father_name = str(row['father_name']).strip()
                basic = Decimal(row['basic'])
                transport = Decimal(row.get('transport', 0))
                canteen = Decimal(row.get('canteen', 0))
                pf = Decimal(row.get('pf', 0))
                esic = Decimal(row.get('esic', 0))
                advance = Decimal(row.get('advance', 0))

                # Skip if employee already exists
                if Employee.objects.filter(employee_code=employee_code).exists():
                    continue

                # Create a new employee object
                Employee.objects.create(
                    employee_code=employee_code,
                    name=name,
                    father_name=father_name,
                    basic=basic,
                    transport=transport,
                    canteen=canteen,
                    pf=pf,
                    esic=esic,
                    advance=advance
                )
            except Exception as e:
                print(f"Error processing row: {row}. Error: {e}")
                continue

    except Exception as e:
        raise ValidationError(f"Error processing file: {e}")


class AddEmployeeAndUploadView(View):
    def get(self, request):
        return render(request, 'employees/add_employee.html', {
            'add_employee_form': EmployeeForm(),
            'upload_form': ExcelUploadForm(),
        })

    def post(self, request):
        if 'add_employee_form' in request.POST:
            form = EmployeeForm(request.POST)
            if form.is_valid():
                form.save()
                messages.success(request, 'Employee added successfully!')
                return redirect('employees:employee_list')
            else:
                messages.error(request, 'Failed to add employee. Please check the form.')

        elif 'upload_form' in request.FILES:
            form = ExcelUploadForm(request.POST, request.FILES)
            if form.is_valid():
                try:
                    handle_file_upload(request.FILES['file'])
                    messages.success(request, 'Employees uploaded successfully!')
                except ValidationError as e:
                    messages.error(request, f"File upload failed: {e}")
                return redirect('employees:employee_list')

        return self.get(request)



class GenerateSalaryView(View):
    def get(self, request):
        return render(request, 'employees/generate_salary.html', {
            'employees': Employee.objects.all(),
            'months': range(1, 13),
            'current_year': timezone.now().year
        })

    def post(self, request):
        month, year, days_in_month = self.get_salary_params(request)
        if not month or not year or not days_in_month:
            return self.render_error(request, 'Please provide all inputs.')

        employees = Employee.objects.all()
        salary_data, total_net_salary = self.calculate_salaries(request, employees, int(days_in_month), int(month),
                                                                int(year))

        return render(request, 'employees/salary_report.html', {
            'salary_data': salary_data,
            'total_net_salary': total_net_salary,
            'month': month,
            'year': year
        })

    def get_salary_params(self, request):
        return request.POST.get('month'), request.POST.get('year'), request.POST.get('days_in_month')

    def calculate_salaries(self, request, employees, days_in_month, month, year):
        salary_data, total_net_salary = [], Decimal(0)
        for employee in employees:
            days_worked = int(request.POST.get(f'days_worked_{employee.id}', 0))
            advance = Decimal(request.POST.get(f'advance_{employee.id}', 0))

            gross_salary, net_salary = self.calculate_salary(employee, days_worked, days_in_month)
            net_salary -= advance

            Salary.objects.update_or_create(
                employee=employee, month=month, year=year,
                defaults={'gross_salary': gross_salary, 'net_salary': net_salary, 'advance': advance}
            )

            salary_data.append({
                'employee_code': employee.employee_code,
                'name': employee.name,
                'gross_salary': gross_salary,
                'net_salary': net_salary,
            })

            total_net_salary += net_salary
        return salary_data, total_net_salary

    def calculate_salary(self, employee, days_worked, days_in_month):
        basic, transport, canteen = employee.basic, employee.transport, employee.canteen
        gross_salary = (basic + transport) / days_in_month * days_worked
        pf = employee.pf / 100 * basic
        esic = employee.esic / 100 * basic
        net_salary = gross_salary - (canteen + pf + esic)
        return round(gross_salary, 2), round(net_salary, 2)


def download_template(request):
    data = {
        'employee_code': ['E001', 'E002'], 'name': ['John Doe', 'Jane Doe'],
        'father_name': ['Father1', 'Father2'], 'basic': [0, 0], 'transport': [0, 0],
        'canteen': [0, 0], 'pf': [0, 0], 'esic': [0, 0], 'advance': [0, 0]
    }
    df = pd.DataFrame(data)
    response = HttpResponse(content_type='application/ms-excel')
    response['Content-Disposition'] = 'attachment; filename="employee_template.xlsx"'
    df.to_excel(response, index=False)
    return response


def employee_profile(request):
    form = EmployeeSearchForm()
    employee = None
    salaries = None

    if request.method == 'GET':
        query = request.GET.get('employee_code_or_name')
        if query:
            # Search for employee by code or name
            employee = Employee.objects.filter(employee_code__iexact=query).first() or Employee.objects.filter(name__iexact=query).first()

            if employee:
                # Get all salary records for the employee
                salaries = Salary.objects.filter(employee=employee).order_by('-month')

    context = {
        'form': form,
        'employee': employee,
        'salaries': salaries
    }
    return render(request, 'employees/employee_profile.html', context)


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
    selected_company = None

    if request.method == 'POST':
        # Handle company selection
        if 'company' in request.POST and request.POST['company']:
            selected_company_id = request.POST['company']
            selected_company = get_object_or_404(Company, id=selected_company_id)
            company_form = CompanyForm(instance=selected_company)

        # Handle adding a new company
        elif 'add_company' in request.POST:
            add_company_form = AddCompanyForm(request.POST)
            if add_company_form.is_valid():
                # Manually create a new company instance
                new_company = Company.objects.create(
                    company_code=add_company_form.cleaned_data['company_code'],
                    company_name=add_company_form.cleaned_data['company_name'],
                    company_address=add_company_form.cleaned_data['company_address'],
                    company_gst_number=add_company_form.cleaned_data['company_gst_number'],
                    company_account_number=add_company_form.cleaned_data['company_account_number'],
                    company_ifsc_code=add_company_form.cleaned_data['company_ifsc_code'],
                    company_contact_person_name=add_company_form.cleaned_data['company_contact_person_name'],
                    company_contact_person_number=add_company_form.cleaned_data['company_contact_person_number'],
                )
                messages.success(request, "Company added successfully!")
                return redirect('employees:company_list')  # Corrected redirect

        # Handle updating an existing company
        elif 'update_company' in request.POST:
            selected_company_id = request.POST['selected_company_id']
            selected_company = get_object_or_404(Company, id=selected_company_id)
            company_form = CompanyForm(request.POST, instance=selected_company)
            if company_form.is_valid():
                company_form.save()
                messages.success(request, "Company details updated successfully!")
                return redirect('employees:company_list')  # Corrected redirect

    context = {
        'companies': companies,
        'company_form': company_form,
        'add_company_form': add_company_form,
        'selected_company': selected_company,
    }
    return render(request, 'employees/company_list.html', context)