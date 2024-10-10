from decimal import Decimal
from sqlite3 import IntegrityError
from django.core.exceptions import ValidationError
from django.shortcuts import render, redirect, get_object_or_404
from django.db.models import Q, Sum
from django.utils import timezone
from django.http import HttpResponse
from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required, user_passes_test
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth import login, logout
from django.contrib.auth.models import Group, User
from django.core.exceptions import PermissionDenied
from django.db import IntegrityError
from django.db import transaction
import pandas as pd
from django.views import View
from django.views.generic import ListView

# Import your models and forms
from .models import Employee, Salary, Task, Profile, Payment, PurchaseItem, VendorInformation, Company
from .forms import (EmployeeForm, TaskForm, ExcelUploadForm, PaymentForm, PurchaseItemForm, VendorInformationForm,
                    CompanyForm, AddCompanyForm, EmployeeSearchForm, CustomUserCreationForm)

def get_user_role_flags(user):
    """
    Helper function to check user role flags.
    Returns a dictionary with boolean flags for `is_superuser`, `is_read_write`, and `is_read_only`.
    """
    is_superuser = user.is_superuser
    is_read_write = user.groups.filter(name='Read and Write').exists()
    is_read_only = user.groups.filter(name='Read Only').exists()

    return {
        'is_superuser': is_superuser,
        'is_read_write': is_read_write,
        'is_read_only': is_read_only
    }

@login_required
def superuser_view(request):
    role_flags = get_user_role_flags(request.user)

    if not role_flags['is_superuser']:
        raise PermissionDenied  # Restrict access to non-superusers

    return render(request, 'employees/home.html', role_flags)

@login_required
def read_write_view(request):
    role_flags = get_user_role_flags(request.user)

    if not role_flags['is_read_write']:
        raise PermissionDenied  # Restrict access to non-read-write users

    return render(request, 'employees/read_write_dashboard.html', role_flags)

@login_required
def read_only_view(request):
    role_flags = get_user_role_flags(request.user)

    if not role_flags['is_read_only']:
        raise PermissionDenied  # Restrict access to non-read-only users

    return render(request, 'employees/read_only_dashboard.html', role_flags)


@login_required
def manage_user_permissions(request):
    if not request.user.is_superuser:
        return redirect('employees:home')  # Only superuser can access this view

    if request.method == 'POST':
        user_id = request.POST.get('user_id')
        group_name = request.POST.get('group_name')

        try:
            user = User.objects.get(id=user_id)
            group = Group.objects.get(name=group_name)
        except User.DoesNotExist:
            messages.error(request, "User not found.")
            return redirect('employees:manage_user_permissions')
        except Group.DoesNotExist:
            messages.error(request, "Group not found.")
            return redirect('employees:manage_user_permissions')

        # Option to grant/revoke superuser status
        if request.POST.get('superuser_status') == 'on':
            user.is_superuser = True
            user.is_staff = True
        else:
            user.is_superuser = False
            user.is_staff = False

        user.save()  # Save user status changes

        # Update user's groups
        try:
            user.groups.clear()  # Remove from all groups
            user.groups.add(group)  # Assign the new group
        except Exception as e:
            messages.error(request, f"An error occurred: {e}")
            return redirect('employees:manage_user_permissions')

        messages.success(request, f"Permissions updated for {user.username}")
        return redirect('employees:manage_user_permissions')

    users = User.objects.all()
    groups = Group.objects.all()
    context = {'users': users, 'groups': groups}
    return render(request, 'employees/manage_permissions.html', context)


# Registering a user with unique username validation
def register_view(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            try:
                user = form.save()

                # Profile creation and assigning group based on user type
                user_type = form.cleaned_data['user_type']
                company = form.cleaned_data.get('company_name', None)
                profile = Profile.objects.create(user=user, user_type=user_type, company_name=company)

                if user_type == 'Owner':
                    profile.organisation_name = form.cleaned_data['organisation_name']
                    profile.organisation_address = form.cleaned_data['organisation_address']
                    profile.contact_number = form.cleaned_data['contact_number']
                    profile.account_number = form.cleaned_data['account_number']
                    profile.ifsc_code = form.cleaned_data['ifsc_code']
                    profile.gst_number = form.cleaned_data['gst_number']
                    profile.save()

                    # Add default owner permissions (or custom group)
                    owner_group = Group.objects.get(name='Owner')
                    user.groups.add(owner_group)
                elif user_type == 'Manager':
                    manager_group = Group.objects.get(name='Manager')
                    user.groups.add(manager_group)
                else:
                    employee_group = Group.objects.get(name='Employee')
                    user.groups.add(employee_group)

                login(request, user)
                return redirect('login')
            except IntegrityError:
                form.add_error('username', 'Username already exists. Please try another.')
    else:
        form = CustomUserCreationForm()

    return render(request, 'employees/register.html', {'form': form})

# Logging in a user
def login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST or None)
        if form.is_valid():
            user = form.get_user()
            login(request, user)

            # Use role flags to decide the redirect
            role_flags = get_user_role_flags(user)

            if role_flags['is_superuser']:
                return redirect('employees:superuser_dashboard')
            elif role_flags['is_read_write']:
                return redirect('employees:read_write_dashboard')
            elif role_flags['is_read_only']:
                return redirect('employees:read_only_dashboard')
            else:
                return redirect('employees:home')  # Default fallback

    else:
        form = AuthenticationForm()

    return render(request, 'employees/login.html', {'form': form})


def logout_view(request):
    logout(request)
    return redirect('employees:login')


def user_profile_detail(request):
    profile = request.user.profile  # Assuming a OneToOne relationship with User
    context = {
        'profile': profile,
        'is_superuser': request.user.groups.filter(name='Superuser').exists(),
        'is_read_write': request.user.groups.filter(name='Read-Write').exists(),
        'is_read_only': request.user.groups.filter(name='Read-Only').exists(),
    }
    return render(request, 'user_profile_detail.html', context)


# Admin Dashboard
def admin_dashboard(request):
    # Total employees, total salary, and data for chart
    total_employees = Employee.objects.count()
    total_salary = Salary.objects.aggregate(Sum('net_salary'))['net_salary__sum']

    months = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October',
              'November', 'December']

    salary_data = [...]  # Salary data per month
    employees_data = [...]  # Employees count per month
    purchases_data = [...]  # Purchases amount per month

    recent_salaries = Salary.objects.order_by('-date_generated')[:10]  # Latest 10 salaries

    context = {
        'total_employees': total_employees,
        'total_salary': total_salary,
        'recent_salaries': recent_salaries,
        'months': months,
        'salary_data': salary_data,
        'employees_data': employees_data,
        'purchases_data': purchases_data
    }

    return render(request, 'employees/admin_dashboard.html', context)


# Home page with tasks
def home(request):
    total_employees = Employee.objects.count()
    tasks = Task.objects.all()
    if request.method == 'POST':
        form = TaskForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('employees:home')
    else:
        form = TaskForm()

    context = {
        'total_employees': total_employees,
        'tasks': tasks,
        'form': form
    }
    return render(request, 'employees/home.html', context)


def add_task(request):
    if request.method == 'POST':
        title = request.POST.get('title')
        Task.objects.create(title=title)
    return redirect('employees:home')

def complete_task(request, task_id):
    task = get_object_or_404(Task, id=task_id)
    task.completed = not task.completed
    task.save()
    return redirect('employees:home')

def delete_task(request, task_id):
    task = get_object_or_404(Task, id=task_id)
    task.delete()
    return redirect('employees:home')


class EmployeeListView(ListView):
    model = Employee
    template_name = 'employee_list.html'
    context_object_name = 'employees'
    paginate_by = 10 # number of employees shown on each page

    def get_queryset(self):
        search_query = self.request.GET.get('search', '')
        queryset = Employee.objects.all()

        if search_query:
            queryset = queryset.filter(
                Q(employee_code__icontains=search_query) |
                Q(name__icontains=search_query)
            )
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search_query'] = self.request.GET.get('search', '')
        return context

def employee_detail(request, id):
    employee = get_object_or_404(Employee, id=id)
    return render(request, 'employee_details.html', {'employee': employee})


def handle_file_upload(file):
    errors = []
    try:
        df = pd.read_excel(file)

        required_columns = ['employee_code', 'name', 'father_name', 'basic', 'transport', 'canteen', 'pf', 'esic', 'advance']
        for col in required_columns:
            if col not in df.columns:
                raise ValidationError(f"Missing required column: {col}")

        for _, row in df.iterrows():
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

                if Employee.objects.filter(employee_code=employee_code).exists():
                    continue

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
                errors.append(f"Error processing row: {row}. Error: {e}")
                continue
    except Exception as e:
        raise ValidationError(f"Error processing file: {e}")

    if errors:
        raise ValidationError(errors)


def handle_form_submission(request, form_class, redirect_url, template_name, context={}):
    if request.method == 'POST':
        form = form_class(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Form submitted successfully!')
            return redirect(redirect_url)
        else:
            messages.error(request, 'Please check the form for errors.')
    else:
        form = form_class()

    context['form'] = form
    return render(request, template_name, context)


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
                    messages.error(request, f"File upload failed: {', '.join(e.messages)}")
                return redirect('employees:employee_list')

        return self.get(request)


class GenerateSalaryView(View):
    @transaction.atomic
    def post(self, request):
        month, year, days_in_month = self.get_salary_params(request)
        if not month or not year or not days_in_month:
            messages.error(request, 'Please provide all inputs.')
            return redirect('employees:generate_salary')

        employees = Employee.objects.all()
        salary_data, total_net_salary = self.calculate_salaries(request, employees, int(days_in_month), int(month), int(year))

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

            # Update or create salary record
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
        if days_worked == 0 or days_in_month == 0:
            return Decimal(0), Decimal(0)

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


def employee_detail(request):
    form = EmployeeSearchForm()
    employee = None
    salaries = None

    if request.method == 'GET':
        query = request.GET.get('employee_code_or_name')
        if query:
            employee = Employee.objects.filter(employee_code__iexact=query).first() or Employee.objects.filter(name__iexact=query).first()

            if employee:
                salaries = Salary.objects.filter(employee=employee).order_by('-month')

    context = {
        'form': form,
        'employee': employee,
        'salaries': salaries
    }
    return render(request, 'employees/employee_detail.html', context)


def salary_list(request):
    month = request.GET.get('month')
    year = request.GET.get('year')

    salaries = Salary.objects.select_related('employee').all()

    if month:
        salaries = salaries.filter(month=month)
    if year:
        salaries = salaries.filter(year=year)

    context = {
        'salaries': salaries,
        'month': month,
        'year': year,
    }
    return render(request, 'employees/salary_list.html', context)


def payment_input(request):
    payments = Payment.objects.all()
    return handle_form_submission(request, PaymentForm, 'employees:payment_input', 'employees/payment_input.html', {'payments': payments})


def purchase_item_input(request):
    purchases = PurchaseItem.objects.all()
    return handle_form_submission(request, PurchaseItemForm, 'employees:purchase_item_input', 'employees/purchase_item_input.html', {'purchases': purchases})


def vendor_information_input(request):
    if request.method == 'POST':
        form = VendorInformationForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('employees:vendor_information_input')
    else:
        form = VendorInformationForm()

    vendor_information = VendorInformation.objects.all()

    return render(request, 'employees/vendor_information_input.html', {'form': form, 'vendor_information': vendor_information})


def company_list(request):
    companies = Company.objects.all()
    company_form = CompanyForm()
    add_company_form = AddCompanyForm()
    selected_company = None

    if request.method == 'POST':
        if 'company' in request.POST and request.POST['company']:
            selected_company_id = request.POST['company']
            selected_company = get_object_or_404(Company, id=selected_company_id)
            company_form = CompanyForm(instance=selected_company)

        elif 'add_company' in request.POST:
            add_company_form = AddCompanyForm(request.POST)
            if add_company_form.is_valid():
                Company.objects.create(
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
                return redirect('employees:company_list')

        elif 'update_company' in request.POST:
            selected_company_id = request.POST['selected_company_id']
            selected_company = get_object_or_404(Company, id=selected_company_id)
            company_form = CompanyForm(request.POST, instance=selected_company)
            if company_form.is_valid():
                company_form.save()
                messages.success(request, "Company details updated successfully!")
                return redirect('employees:company_list')

    context = {
        'companies': companies,
        'company_form': company_form,
        'add_company_form': add_company_form,
        'selected_company': selected_company,
    }
    return render(request, 'employees/company_list.html', context)
