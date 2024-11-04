from decimal import Decimal
from sqlite3 import IntegrityError
from sys import prefix

from django.core.exceptions import ValidationError, PermissionDenied
from django.shortcuts import render, redirect, get_object_or_404
from django.db.models import Q, Sum
from django.utils import timezone
from django.http import HttpResponse, JsonResponse
from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required, user_passes_test
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.models import Group, User
from django.db import IntegrityError, transaction
import pandas as pd
from django.views import View
from django.views.generic import ListView
from datetime import datetime
from django.views.decorators.csrf import csrf_exempt
import json
import csv

from openpyxl.utils.datetime import days_to_time

# Import your models and forms
from .models import (Employee, Salary, Task, Profile, Payment, PurchaseItem, VendorInformation, Company,
                     StaffSalary, AdvanceTransaction, SalaryRule)
from .forms import (EmployeeForm, TaskForm, ExcelUploadForm, PaymentForm, PurchaseItemForm, VendorInformationForm,
                    CompanyForm, AddCompanyForm, EmployeeSearchForm, CustomUserCreationForm, StaffSalaryForm,
                    AdvanceTransactionForm, ProfileEditForm, LoginForm, SalaryRuleFormSet)


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

@login_required
@csrf_exempt
def save_theme_preference(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        theme = data.get('theme', 'light')

        # Update the user's profile
        user_profile = request.user.userprofile
        user_profile.theme_preference = theme
        user_profile.save()

        return JsonResponse({'success': True})
    return JsonResponse({'success': False}, status=400)

@login_required
def settings_view(request):
    return render(request, 'employees/settings.html')

# views.py
@login_required
def staff_salary_detail(request, pk):
    salary = get_object_or_404(StaffSalary, pk=pk)

    if request.method == 'POST':
        form = AdvanceTransactionForm(request.POST)
        if form.is_valid():
            new_transaction = form.save(commit=False)
            new_transaction.staff_salary = salary
            new_transaction.save()
            return redirect('employees:staff_salary_detail', pk=pk)
    else:
        form = AdvanceTransactionForm()

    transactions = salary.transactions.all().order_by('-date')

    return render(request, 'employees/staff_salary_detail.html', {
        'salary': salary,
        'transactions': transactions,
        'form': form,
    })


@login_required
def edit_transaction(request, pk):
    transaction = get_object_or_404(AdvanceTransaction, pk=pk)
    salary = transaction.staff_salary

    if request.method == 'POST':
        form = AdvanceTransactionForm(request.POST, instance=transaction)
        if form.is_valid():
            form.save()
            return redirect('employees:staff_salary_detail', pk=salary.pk)
    else:
        form = AdvanceTransactionForm(instance=transaction)

    return render(request, 'employees/edit_transaction.html', {
        'form': form,
        'salary': salary,
        'transaction': transaction,
    })


# Registering a user with unique username validation
def register_view(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            try:
                user = form.save()

                # Profile creation and assigning group based on user type
                profile = Profile.objects.create(
                    user=user,
                    user_type=form.cleaned_data['user_type'],
                    company=form.cleaned_data.get('company_name', None)
                )

                if profile.user_type == 'Owner':
                    # Assign Owner-specific fields directly to profile
                    profile.organisation_name = form.cleaned_data.get('organisation_name', "")
                    profile.organisation_address = form.cleaned_data.get('organisation_address', "")
                    profile.contact_number = form.cleaned_data.get('contact_number', "")
                    profile.account_number = form.cleaned_data.get('account_number', "")
                    profile.ifsc_code = form.cleaned_data.get('ifsc_code', "")
                    profile.gst_number = form.cleaned_data.get('gst_number', "")
                    profile.save()

                    # Add owner group permissions
                    owner_group = Group.objects.get(name='Owner')
                    user.groups.add(owner_group)

                elif profile.user_type == 'Manager':
                    manager_group = Group.objects.get(name='Manager')
                    user.groups.add(manager_group)
                else:
                    employee_group = Group.objects.get(name='Employee')
                    user.groups.add(employee_group)

                login(request, user)
                messages.success(request, "Registration successful! You are now logged in.")
                return redirect('employees:home')

            except IntegrityError:
                form.add_error('username', 'Username already exists. Please try another.')
                messages.error(request, 'Username already exists. Please try again.')
    else:
        form = CustomUserCreationForm()

    return render(request, 'employees/register.html', {'form': form})



# Logging in a user
def login_view(request):
    if request.method == 'POST':
        form = LoginForm(request, data=request.POST)
        if form.is_valid():
            company = form.cleaned_data.get('company_name')
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')

            # Authenticate the user
            user = authenticate(request, username=username, password=password)

            if user is not None:
                # Verify that the user belongs to the selected company
                if user.profile.company == company:
                    login(request, user)
                    return redirect('employees:home')
                else:
                    # Show error if user is not associated with the selected company
                    form.add_error(None, "This account is not associated with the selected company.")
            else:
                # Show generic error for failed authentication
                form.add_error(None, "Invalid username or password.")
    else:
        form = LoginForm()

    return render(request, 'employees/login.html', {'form': form})

def logout_view(request):
    logout(request)
    return redirect('employees:login')

@login_required
def user_profile_detail(request):
    user = request.user
    try:
        profile = user.profile  # Get the user's profile
    except Profile.DoesNotExist:
        profile = Profile.objects.create(user=user) # If profile does not exist, create a new one for the user


    # Handle the form submission for editing the profile
    if request.method == 'POST':
        # If it's a POST request, process the form and update the profile
        form = ProfileEditForm(request.POST, instance=profile)  # Bind the form with POST data
        if form.is_valid():
            form.save() # Save the updated profile information
            messages.success(request, "Profile updated successfully!")
            return redirect('user_profile_detail')  # Refresh page after successful update
    else:
        # If it's a GET request, display the form with the current profile data
        form = ProfileEditForm(instance=profile)  # Pre-fill form with current profile data

    context = {
        'profile': profile,
        'form': form,
        'is_superuser': user.groups.filter(name='Superuser').exists(),
        'is_read_write': user.groups.filter(name='Read and Write').exists(),
        'is_read_only': user.groups.filter(name='Read Only').exists(),
    }
    return render(request, 'employees/user_profile_detail.html', context)



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
    tasks = Task.objects.filter(user=request.user)
    users = User.objects.all() # Get all users for the transfer dropdown

    if request.method == 'POST':
        form = TaskForm(request.POST)
        if form.is_valid():
            task = form.save(commit=False)
            task.user = request.user # Assign the task to the current user
            form.save()
            return redirect('employees:home')
    else:
        form = TaskForm()

    context = {
        'total_employees': total_employees,
        'tasks': tasks,
        'users': users, # PAss users for the transfer dropdown
        'form': form
    }
    return render(request, 'employees/home.html', context)


def add_task(request):
    if request.method == 'POST':
        title = request.POST.get('title')
        Task.objects.create(title=title, user=request.user) #Associated task with logged-in user
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

def transfer_task(request, task_id):
    task = get_object_or_404(Task, id=task_id)
    if request.method == 'POST':
        new_user_id = request.POST.get('user')
        new_user = get_object_or_404(User, id=new_user_id)
        task.user = new_user
        task.save()
        messages.success(request, f'Task transferred to {new_user.username}.')
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

        # Pagination logic
        page = self.request.GET.get('page', 1)
        paginator = Paginator(self.get_queryset(), self.paginate_by)

        try:
            employees = paginator.page(page)
        except PageNotAnInteger:
            employees = paginator.page(1)
        except EmptyPage:
            employees = paginator.page(paginator.num_pages)

        context['employees'] = employees
        return context

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search_query'] = self.request.GET.get('search', '')
        return context

def employee_detail(request, id):
    employee = get_object_or_404(Employee, id=id)
    return render(request, 'employee_details.html', {'employee': employee})


class AddEmployeeAndUploadView(View):
    def get(self, request):
        return render(request, 'employees/add_employee.html', {
            'add_employee_form': EmployeeForm(),
            'upload_form': ExcelUploadForm(),
        })

    def post(self, request):
        if request.POST.get('submit_type') == 'add_employee':
            form = EmployeeForm(request.POST)
            if form.is_valid():
                form.save()
                messages.success(request, 'Employee added successfully!')
                return redirect('employees:employee_list')  # Redirect to employee list view or appropriate URL
            else:
                messages.error(request, 'Failed to add employee. Please check the form.')
            return render(request, 'employees/add_employee.html', {'add_employee_form': form, 'upload_form': ExcelUploadForm()})

        elif request.POST.get('submit_type') == 'upload_employees':
            form = ExcelUploadForm(request.POST, request.FILES)
            if form.is_valid():
                try:
                    handle_file_upload(request.FILES['file'])
                    messages.success(request, 'Employees uploaded successfully!')
                except ValidationError as e:
                    messages.error(request, f"File upload failed: {', '.join(e.messages)}")
                return redirect('employees:employee_list')

        return self.get(request)

def download_template(request):
    # Define columns for the template
    columns = [
        'employee_code', 'name', 'father_name', 'mother_name', 'gender', 'dob', 'marital_status', 'spouse_name',
        'mobile', 'email', 'address', 'district', 'state', 'pincode',
        'pf_no', 'esi_no', 'uan', 'pan', 'company', 'department', 'designation', 'doj', 'doe',
        'pay_mode', 'employer_account', 'employee_account', 'ifsc', 'kyc_status', 'handicap', 'remarks',
        'basic', 'transport', 'canteen', 'pf_contribution', 'esic_contribution', 'advance'
    ]

    # Create an empty DataFrame with the specified columns
    df = pd.DataFrame(columns=columns)

    # Create a response object for downloading the Excel file
    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = 'attachment; filename=employee_upload_template.xlsx'

    # Write the empty DataFrame to Excel and serve as a download
    with pd.ExcelWriter(response, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='EmployeeTemplate')

    return response


def handle_file_upload(file):
    # Example for handling Excel file upload
    try:
        df = pd.read_excel(file)
        # Process dataframe to add employees; adjust column names as per your Excel structure
        for index, row in df.iterrows():
            Employee.objects.create(
                employee_code=row['Employee Code'],
                name=row['Name'],
                # Map other fields from the DataFrame row to Employee fields
            )
    except Exception as e:
        raise ValidationError(f"Error processing file: {e}")


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
                # Basic validation for each row
                employee_code = str(row['employee_code']).strip()
                name = str(row['name']).strip()
                father_name = str(row['father_name']).strip()

                basic = Decimal(row['basic']) if pd.notnull(row['basic']) else Decimal('0.00')
                transport = Decimal(row.get('transport', 0))
                canteen = Decimal(row.get('canteen', 0))
                pf = Decimal(row.get('pf', 0))
                esic = Decimal(row.get('esic', 0))
                advance = Decimal(row.get('advance', 0))

                if Employee.objects.filter(employee_code=employee_code).exists():
                    errors.append(f"Employee with code {employee_code} already exists.")
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
            except ValueError as ve:
                errors.append(f"Invalid value in row: {row}. Error: {ve}")
            except Exception as e:
                errors.append(f"Error processing row: {row}. Error: {e}")
                continue
    except Exception as e:
        raise ValidationError(f"Error processing file: {e}")

    if errors:
        raise ValidationError(errors)


class GenerateSalaryView(PermissionRequiredMixin, View):
    permission_required = 'employees.can_generate_payroll'

    @transaction.atomic
    def post(self, request):
        month, year, days_in_month = self.get_salary_params(request)
        if not month or not year or not days_in_month:
            messages.error(request, 'Please provide all inputs.')
            return redirect('employees:generate_salary')

        employees = Employee.objects.all().select_related()  # Efficiently fetch related data
        salary_data, total_gross_salary, total_pf, total_esic, total_canteen, total_advance, total_net_salary = self.calculate_salaries(
            request, employees, int(days_in_month), int(month), int(year)
        )

        messages.success(request, 'Salary generated successfully!')
        return render(request, 'employees/salary_report.html', {
            'salary_data': salary_data,
            'total_gross_salary': total_gross_salary,
            'total_pf': total_pf,
            'total_esic': total_esic,
            'total_canteen': total_canteen,
            'total_advance': total_advance,
            'total_net_salary': total_net_salary,
            'month': month,
            'year': year
        })

    def get_salary_params(self, request):
        month = request.POST.get('month')
        year = request.POST.get
        days_in_month =request.POST.get('days_in_month')

        if not month or not year or not days_in_month:
            return None, None, None # This will trigger an error message
        return month, year, days_in_month

    def calculate_salaries(self, request, employees, days_in_month, month, year):
        salary_data = []
        total_gross_salary = total_pf = total_esic = total_canteen = total_advance = total_net_salary = Decimal(0.00)

        for employee in employees:
            try:
                days_worked = int(request.POST.get(f'days_worked_{employee.id}', 0))
                advance = Decimal(request.POST.get(f'advance_{employee.id}', 0))

                # calculate gross salary, net salary, pf, esic, and canteen
                gross_salary, net_salary, pf, esic, canteen = self.calculate_salary(employee, days_worked, days_in_month)
                net_salary -= advance

                # Update or create salary record
                Salary.objects.update_or_create(
                    employee=employee, month=month, year=year,
                    defaults={'gross_salary': gross_salary, 'net_salary': net_salary, 'advance': advance}
                )

                # Append salary data for each employee
                salary_data.append({
                    'employee_code': employee.employee_code,
                    'name': employee.name,
                    'gross_salary': gross_salary,
                    'pf': pf,
                    'esic': esic,
                    'canteen': canteen,
                    'advance': advance,
                    'net_salary': net_salary
                })

                # Calculate totals for each column
                total_gross_salary += gross_salary
                total_pf += pf
                total_esic += esic
                total_canteen += canteen
                total_advance += advance
                total_net_salary += net_salary
            except Exception as e:
                # Log the error for debugging
                print(f"Error calculating salary for {employee.name}:e")
                messages.error(request, f"Error calculating salary for {employee.name}.")
        return salary_data, total_gross_salary, total_pf, total_esic, total_canteen, total_advance, total_net_salary




def employee_detail(request):
    form = EmployeeSearchForm()
    employee = None
    salaries = None
    not_found = False # Flag to indicate if no record was found

    if request.method == 'GET':
        query = request.GET.get('employee_code_or_name')
        if query:
            employee = Employee.objects.filter(employee_code__iexact=query).first() or Employee.objects.filter(name__iexact=query).first()

            if employee:
                salaries = Salary.objects.filter(employee=employee).order_by('-month')
            else:
                not_found = True # Set the flag if no employee was found

    context = {
        'form': form,
        'employee': employee,
        'salaries': salaries,
        'not_found': not_found # pass the flag to the template
    }
    return render(request, 'employees/employee_detail.html', context)

@login_required
@user_passes_test(lambda u: u.is_superuser)
def delete_employee(request, employee_id):
    employee = get_object_or_404(Employee, id=employee_id)

    if request.method == 'POST':  # Confirm the deletion with a POST request
        employee.delete()
        messages.success(request, f'Employee {employee.name} has been successfully deleted.')
        return redirect('employees:employee_list')  # Redirect to employee list after deletion
    return render(request, 'employees/employee_confirm_delete.html', {'employee': employee})


@login_required
@user_passes_test(lambda u: u.is_superuser)
def delete_multiple_employees(request):
    if request.method == 'POST':
        employee_ids = request.POST.getlist('employee_ids')  # Get list of selected employee IDs
        if employee_ids:
            employees = Employee.objects.filter(id__in=employee_ids)
            employees_deleted = employees.count()
            employees.delete()
            messages.success(request, f'{employees_deleted} employee(s) successfully deleted.')
        else:
            messages.warning(request, 'No employees selected for deletion.')

    return redirect('employees:employee_list')


def salary_list(request):
    # Get the selected month and year from the request
    month = request.GET.get('month', '') # Default to ''(empty) for "All"
    year = request.GET.get('year', '')

    # Filter salaries based on month and year
    salaries = Salary.objects.all()

    if month:
        salaries = salaries.filter(month=month)
    if year:
        salaries = salaries.filter(year=year)

    # Calculate total number of unique employees
    total_employees = salaries.values('employee_id').distinct().count()

    # Calculate totals for each column
    totals = salaries.aggregate(
        total_basic_salary=Sum('basic_salary'),
        total_transport=Sum('transport'),
        total_canteen=Sum('canteen'),
        total_pf=Sum('pf'),
        total_esic=Sum('esic'),
        total_advance=Sum('advance_deduction'),
        total_gross_salary=Sum('gross_salary'),
        total_net_salary=Sum('net_salary')
    )

    # Provide the necessary context to the template
    month_choices = [
        (1, 'January'), (2, 'February'), (3, 'March'), (4, 'April'),
        (5, 'May'), (6, 'June'), (7, 'July'), (8, 'August'),
        (9, 'September'), (10, 'October'), (11, 'November'), (12, 'December')
    ]

    context = {
        'salaries': salaries,
        'month_choices' : month_choices,
        'month': month,
        'year': year,
        'total_employees': total_employees,
        'totals': totals
    }
    return render(request, 'employees/salary_list.html', context)

# Download Salary List as CSV
def download_salary_csv(request):
    # Get the selected month and year from query parameters
    month = request.GET.get('month', '')
    year = request.GET.get('year', '')

    # Filter salaries based on month and year
    salaries = Salary.objects.all()
    if year:
        salaries = salaries.filter(year=year)
    if month:
        salaries = salaries.filter(month=month)

    # Create the HttpResponse object with the appropriate CSV header.
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="salaries_{month}_{year}.csv"'

    # Create a CSV writer
    writer = csv.writer(response)
    # Write the header row
    writer.writerow([
        'Employee Name', 'Month', 'Year', 'Basic Salary', 'Transport', 'Canteen', 'PF', 'ESIC', 'Advance Deduction', 'Gross Salary', 'Net Salary' ])

    # Write the data rows
    for salary in salaries:
        writer.writerow([
            salary.employee.name,
            salary.get_month_display(),
            salary.year,
            f"{salary.basic_salary:.2f}",
            f"{salary.transport:.2f}",
            f"{salary.canteen:.2f}",
            f"{salary.pf:.2f}",
            f"{salary.esic:.2f}",
            f"{salary.advance_deduction:.2f}",
            f"{salary.gross_salary:.2f}",
            f"{salary.net_salary:.2f}",
        ])

    return response


# Handle form submission for adding and editing
def handle_form_submission(request, form_class, redirect_url, template_name, context, instance=None):
    if request.method == 'POST':
        form = form_class(request.POST, instance=instance)  # Use instance if editing
        if form.is_valid():
            form.save()
            if instance:
                messages.success(request, "Payment details updated successfully!")
            else:
                messages.success(request, "Payment entry added successfully!")
            return redirect(redirect_url)
    else:
        form = form_class(instance=instance)  # Populate the form with instance if editing

    context['form'] = form
    return render(request, template_name, context)

# Handle payment input and listing payments
def payment_input(request):
    payments = Payment.objects.all()
    context = {'payments': payments}
    return handle_form_submission(request, PaymentForm, 'employees:payment_input', 'employees/payment_input.html', context)

# Handle payment edit
def edit_payment(request, payment_id):
    payment = get_object_or_404(Payment, id=payment_id)
    payments = Payment.objects.all()
    context = {'payments': payments}
    return handle_form_submission(request, PaymentForm, 'employees:payment_input', 'employees/payment_input.html', context, instance=payment)

# Handle payment delete
def delete_payment(request, payment_id):
    payment = get_object_or_404(Payment, id=payment_id)
    payment.delete()
    messages.success(request, "Payment entry deleted successfully!")
    return redirect('employees:payment_input')


# Purchase information
def purchase_item_input(request):
    purchases = PurchaseItem.objects.all()
    return handle_form_submission(request, PurchaseItemForm, 'employees:purchase_item_input', 'employees/purchase_item_input.html', {'purchases': purchases})

# Vendor information and profile
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
    query = request.GET.get('q', '')
    companies = Company.objects.filter(company_name__icontains=query) if query else Company.objects.all()
    context = {
        'companies': companies,
        'query': query,
    }
    return render(request, 'employees/company_list.html', context)

def company_add(request):
    if request.method == 'POST':
        company_form = CompanyForm(request.POST)
        salary_rule_formset = SalaryRuleFormSet(request.POST, instance=company_form.instance)

        if company_form.is_valid() and salary_rule_formset.is_valid():
            company_form.save()
            salary_rule_formset.instance = company
            salary_rule_formset.save()
            messages.success(request, "Company added successfully!")
            return redirect('employees:company_list')
    else:
        company_form = CompanyForm()
        salary_rule_formset = SalaryRuleFormSet()

    return render(request, 'employees/company_add_update.html', {
        'company_form': company_form,
        'salary_rule_formset': salary_rule_formset,
        'is_update': False,
    })


def company_update(request, company_id):
    company = get_object_or_404(Company, id=company_id)
    if request.method == 'POST':
        company_form = CompanyForm(request.POST, instance=company)
        salary_rule_formset = SalaryRuleFormSet(request.POST, instance=company)

        if company_form.is_valid() and salary_rule_formset.is_valid():
            company_form.save()
            salary_rule_formset.save()
            messages.success(request, "Company and salary rules updated successfully!")
            return redirect('employees:company_list')
    else:
        company_form = CompanyForm(instance=company)
        salary_rule_formset = SalaryRuleFormSet(instance=company)

    return render(request, 'employees/company_add_update.html', {
        'company_form': company_form,
        'salary_rule_formset': salary_rule_formset,
        'is_update': True,
    })

def delete_company(request, company_id):
    company = get_object_or_404(Company, id=company_id)
    company.delete()
    messages.success(request, "Company deleted successfully!")
    return redirect('employees:company_list')


# Staff Salary view
def staff_salary_list(request):
    salaries = StaffSalary.objects.all()
    return render(request, 'employees/staff_salary_list.html', {'salaries': salaries})

def staff_salary_create(request):
    if request.method == 'POST':
        form = StaffSalaryForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('employees:staff_salary_list')
    else:
        form = StaffSalaryForm()
    return render(request, 'employees/staff_salary_form.html', {'form': form})

def staff_salary_update(request, pk):
    salary = StaffSalary.objects.get(pk=pk)
    if request.method == 'POST':
        form = StaffSalaryForm(request.POST, instance=salary)
        if form.is_valid():
            form.save()
            return redirect('employees:staff_salary_list')
    else:
        form = StaffSalaryForm(instance=salary)
    return render(request, 'employees/staff_salary_form.html', {'form': form})