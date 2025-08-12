from decimal import Decimal
import decimal
from sqlite3 import IntegrityError
from sys import prefix

from django.contrib.sites import requests
from django.core.paginator import Paginator


from django.forms import modelformset_factory
from django.views.generic.edit import UpdateView
from django.core.exceptions import ValidationError, PermissionDenied
from django.shortcuts import render, redirect, get_object_or_404
from django.db.models import Q, Sum
from django.urls import reverse_lazy, reverse
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
import logging
from django.utils.timezone import now
from openpyxl import Workbook
from openpyxl.utils.datetime import days_to_time
from .models import (
    Employee, Salary, Task, Profile, Payment, PurchaseItem, VendorInformation, 
    Company, StaffSalary, AdvanceTransaction, SalaryRule, SalaryOtherField, 
    SalaryTotals, VerificationRequest, EInvoice, EInvoiceLineItem, BillTemplate, 
    ServiceBill, ServiceBillItem, Purchase, PurchaseLineItem, Site, 
    EmployeesAttendance, CompanyAdvanceTransaction, Arrear, MONTH_CHOICES
)
from .forms import EmployeeForm, TaskForm, ExcelUploadForm, PaymentForm, PurchaseItemForm, VendorInformationForm, CompanyForm, AddCompanyForm, EmployeeSearchForm, CustomUserCreationForm, StaffSalaryForm, AdvanceTransactionForm, ProfileEditForm, LoginForm, SalaryRuleFormSet, SalaryOtherFieldFormSet, UploadForm, ReportForm, VerificationRequestForm, EInvoiceForm, EInvoiceLineItemFormSet, BillTemplateForm, ServiceBillForm, ServiceBillItemForm, ServiceBillItemFormSet, PurchaseForm, PurchaseLineItemFormSet, PurchaseItemFormSet, SiteForm
from django.views.generic import TemplateView

# Get an instance of a logger
logger = logging.getLogger(__name__)

# Import your models and forms

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

def forgot_password(request):
    password_info = None
    if request.method == 'POST':
        username = request.POST.get('username')
        try:
            user = User.objects.get(username=username)
            # This is insecure. In a real application, implement a secure password reset.
            new_password = username  # Set the new password to the username
            user.set_password(new_password)
            user.save()
            password_info = f"Password for {username} has been reset to: {new_password}"
            messages.success(request, password_info)
        except User.DoesNotExist:
            messages.error(request, "User not found.")
    return render(request, 'employees/forgot_password.html')

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

# Theme prefecrence of user
def update_theme_preference(request):
    if request.method == 'POST':
        theme = request.POST.get('theme', 'light')
        if hasattr(request.user, 'userprofile'):
            request.user.userprofile.theme_preference = theme
            request.user.userprofile.save()
        return JsonResponse({'status': 'success'})
    return JsonResponse({'status': 'error'})


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

# To do List
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
    template_name = 'employees/employee_list.html'
    context_object_name = 'employees'
    paginate_by = 10

    def get_queryset(self):
        queryset = super().get_queryset()
        site_id = self.request.GET.get('site')
        search_query = self.request.GET.get('search', '')

        if site_id:
            queryset = queryset.filter(site_id=site_id)
        
        if search_query:
            queryset = queryset.filter(
                Q(employee_code__icontains=search_query) | Q(name__icontains=search_query)
            )
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['sites'] = Site.objects.all()
        context['selected_site_id'] = self.request.GET.get('site')
        context['search_query'] = self.request.GET.get('search', '')
        return context

def employee_detail(request, id):
    employee = get_object_or_404(Employee, id=id)
    return render(request, 'employee_details.html', {'employee': employee})

class EmployeeUpdateView(UpdateView):
    model = Employee
    form_class = EmployeeForm
    template_name = 'employees/employee_edit.html'
    context_object_name = 'employee'

    def get_success_url(self):
        return reverse_lazy('employees:employee_list')  # Redirect to employee list a

class AddEmployeeAndUploadView(View):
    def get(self, request):
        sites = Site.objects.all()
        recent_employees = Employee.objects.order_by('-doj')[:5]
        return render(request, 'employees/add_employee.html', {
            'add_employee_form': EmployeeForm(),
            'upload_form': ExcelUploadForm(),
            'sites': sites,
            'recent_employees': recent_employees
        })

    def post(self, request):
        if request.POST.get('submit_type') == 'add_employee':
            form = EmployeeForm(request.POST)
            if form.is_valid():
                form.save()
                messages.success(request, 'Employee added successfully!')
                return redirect('employees:employee_list')
            else:
                error_list = []
                for field, errors in form.errors.items():
                    error_list.append(f"<strong>{field}:</strong> {', '.join(errors)}")
                error_string = "; ".join(error_list)
                messages.error(request, f'Failed to add employee. Please check the form. Details: {error_string}')
            
            sites = Site.objects.all()
            return render(request, 'employees/add_employee.html', {
                'add_employee_form': form,
                'upload_form': ExcelUploadForm(),
                'sites': sites
            })

        elif request.POST.get('submit_type') == 'upload_employees':
            form = ExcelUploadForm(request.POST, request.FILES)
            if form.is_valid():
                site_id = request.POST.get('site')
                if not site_id:
                    messages.error(request, 'Please select a site.')
                    return redirect('employees:add_employee')
                
                try:
                    site = Site.objects.get(id=site_id)
                    handle_file_upload(request.FILES['file'], site)
                    messages.success(request, 'Employees uploaded successfully!')
                except Site.DoesNotExist:
                    messages.error(request, 'Invalid site selected.')
                except ValidationError as e:
                    messages.error(request, f"File upload failed: {e}")
                return redirect('employees:employee_list')
        return self.get(request)

def handle_file_upload(file, site):
    errors = []
    try:
        df = pd.read_excel(file)
        required_columns = ['employee_code', 'name', 'father_name', 'basic']
        missing_cols = [col for col in required_columns if col not in df.columns]
        if missing_cols:
            raise ValidationError(f"Missing required columns: {', '.join(missing_cols)}")

        for idx, row in df.iterrows():
            try:
                # Handle required fields
                employee_code = str(row['employee_code']).strip() if pd.notna(row['employee_code']) else ''
                name = str(row['name']).strip() if pd.notna(row['name']) else ''
                father_name = str(row['father_name']).strip() if pd.notna(row['father_name']) else ''
                
                if not employee_code or not name:
                    errors.append(f"Row {idx+2}: Employee code and name are required.")
                    continue

                if Employee.objects.filter(employee_code=employee_code).exists():
                    errors.append(f"Row {idx+2}: Employee with code {employee_code} already exists.")
                    continue

                # Helper function to safely convert to Decimal
                def safe_decimal(value, default='0.00'):
                    if pd.isna(value) or value == '' or value is None:
                        return Decimal(default)
                    try:
                        # Convert to string first to handle various number formats
                        return Decimal(str(value).strip())
                    except (ValueError, TypeError, decimal.InvalidOperation):
                        return Decimal(default)

                # Create employee with all available fields
                employee_data = {
                    'site': site,
                    'employee_code': employee_code,
                    'name': name,
                    'father_name': father_name,
                    'basic': safe_decimal(row.get('basic', 0)),
                    'transport': safe_decimal(row.get('transport', 0)),
                    'canteen': safe_decimal(row.get('canteen', 0)),
                    'sr_allowance': safe_decimal(row.get('sr_allowance', 0)),
                    'da': safe_decimal(row.get('da', 0)),
                    'hra': safe_decimal(row.get('hra', 0)),
                    'medical': safe_decimal(row.get('medical', 0)),
                    'conveyance': safe_decimal(row.get('conveyance', 0)),
                    'wash_allowance': safe_decimal(row.get('wash_allowance', 0)),
                    'efficiency': safe_decimal(row.get('efficiency', 0)),
                    'other_payable': safe_decimal(row.get('other_payable', 0)),
                }

                # Handle string fields
                string_fields = ['pf_no', 'esi_no', 'uan', 'account_number', 'ifsc', 'mobile', 'email', 'address']
                for field in string_fields:
                    if field in row and pd.notna(row[field]):
                        employee_data[field] = str(row[field]).strip()

                # Handle date fields
                if 'date_of_joining' in row and pd.notna(row['date_of_joining']):
                    try:
                        employee_data['date_of_joining'] = pd.to_datetime(row['date_of_joining']).date()
                    except:
                        pass

                Employee.objects.create(**employee_data)
                
            except Exception as e:
                errors.append(f"Row {idx+2}: Error - {str(e)}")
                continue

    except Exception as e:
        raise ValidationError(f"Error processing file: {str(e)}")
    
    if errors:
        # Join all errors and raise as a single message
        error_message = "; ".join(errors[:5])  # Show first 5 errors
        if len(errors) > 5:
            error_message += f" ... and {len(errors) - 5} more errors."
        raise ValidationError(error_message)


class GenerateSalaryView(PermissionRequiredMixin, View):
    permission_required = 'employees.can_generate_payroll'
    template_name = 'employees/generate_salary.html'

    def get(self, request, *args, **kwargs):
        site_id = request.GET.get('site')
        sites = Site.objects.all()
        employees = Employee.objects.filter(site_id=site_id) if site_id else Employee.objects.none()
        
        context = {
            'sites': sites,
            'selected_site_id': site_id,
            'employees': employees,
            'months': [(i, datetime(2000, i, 1).strftime('%B')) for i in range(1, 13)],
            'current_year': now().year
        }
        return render(request, self.template_name, context)

    @transaction.atomic
    def post(self, request, *args, **kwargs):
        site_id = request.POST.get('site')
        if not site_id:
            messages.error(request, 'Please select a site.')
            return redirect('employees:generate_salary')
        
        site = get_object_or_404(Site, id=site_id)
        month, year, days_in_month = self.get_salary_params(request)
        if not all([month, year, days_in_month]):
            messages.error(request, 'Please provide all inputs.')
            return redirect(f"{reverse('employees:generate_salary')}?site={site_id}")

        employees = Employee.objects.filter(site=site)
        salary_data, totals = self.calculate_salaries(request, employees, int(days_in_month), int(month), int(year))

        SalaryTotals.objects.update_or_create(
            month=month, year=year,
            defaults={
                'total_gross_salary': totals['total_gross_salary'],
                'total_pf': totals['total_pf'],
                'total_esic': totals['total_esic'],
                'total_canteen': totals['total_canteen'],
                'total_advance': totals['total_advance'],
                'total_net_salary': totals['total_net_salary'],
            }
        )

        messages.success(request, 'Salary generated successfully!')
        return render(request, 'employees/salary_report.html', {
            'salary_data': salary_data,
            'totals': totals,
            'month': month,
            'year': year,
            'site': site
        })
    
    def get_salary_params(self, request):
        month = request.POST.get('month')
        year = request.POST.get('year')
        days_in_month = request.POST.get('days_in_month')

        if not month or not year or not days_in_month:
            return None, None, None
        return month, year, days_in_month

    def calculate_salaries(self, request, employees, days_in_month, month, year):
        salary_data = []
        totals = {
            'total_gross_salary': Decimal(0),
            'total_pf': Decimal(0),
            'total_esic': Decimal(0),
            'total_canteen': Decimal(0),
            'total_advance': Decimal(0),
            'total_net_salary': Decimal(0)
        }

        for employee in employees:
            try:
                days_worked = int(request.POST.get(f'days_worked_{employee.id}', 0))
                advance = Decimal(request.POST.get(f'advance_{employee.id}', 0))
                gross_salary, net_salary, pf, esic, canteen = self.calculate_salary(employee, days_worked, days_in_month)
                net_salary -= advance

                Salary.objects.update_or_create(
                    employee=employee, month=month, year=year,
                    defaults={
                        'gross_salary': gross_salary,
                        'net_salary': net_salary,
                        'advance_deduction': advance,
                        'pf': pf,
                        'esic': esic,
                        'canteen': canteen
                    }
                )

                salary_data.append({
                    'employee_code': employee.employee_code,
                    'name': employee.name,
                    'gross_salary': gross_salary,
                    'pf': pf,
                    'esic': esic,
                    'canteen': canteen,
                    'advance_deduction': advance,
                    'net_salary': net_salary
                })

                totals['total_gross_salary'] += gross_salary
                totals['total_pf'] += pf
                totals['total_esic'] += esic
                totals['total_canteen'] += canteen
                totals['total_advance'] += advance
                totals['total_net_salary'] += net_salary

            except Exception as e:
                logger.error(f"Error calculating salary for {employee.name}: {e}")
                messages.error(request, f"Error calculating salary for {employee.name}. Please check the input values.")

        return salary_data, totals
    
    def calculate_salary(self, employee, days_worked, days_in_month):
        # Ensure all values are treated as Decimal, defaulting to 0
        basic = Decimal(employee.basic or 0)
        transport = Decimal(employee.transport or 0)
        canteen = Decimal(employee.canteen or 0)

        # Example calculation logic
        basic_salary = basic / days_in_month * days_worked
        transport_allowance = transport / days_in_month * days_worked
        canteen_deduction = canteen / days_in_month * days_worked
        
        gross_salary = basic_salary + transport_allowance - canteen_deduction
        pf = gross_salary * Decimal('0.12')
        esic = gross_salary * Decimal('0.0075')
        net_salary = gross_salary - (pf + esic)
        
        return gross_salary, net_salary, pf, esic, canteen_deduction

def download_salary_report(request, month, year):
    salaries = Salary.objects.filter(month=month, year=year)
    wb = Workbook()
    ws = wb.active
    ws.title = f"Salary Report {month}-{year}"

    headers = ['Employee Code', 'Name', 'Gross Salary', 'Net Salary', 'PF', 'ESIC', 'Advance Deduction']
    ws.append(headers)

    for salary in salaries:
        ws.append([
            salary.employee.employee_code,
            salary.employee.name,
            salary.gross_salary,
            salary.net_salary,
            salary.pf,
            salary.esic,
            salary.advance
        ])

    response = HttpResponse(content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    response['Content-Disposition'] = f'attachment; filename="salary_report_{month}_{year}.xlsx"'
    wb.save(response)
    return response


def download_template(request, site_id):
    """
    Generates and serves a downloadable Excel template for bulk employee uploads,
    including all fields from the Employee model and a pre-filled site column.
    """
    site = get_object_or_404(Site, id=site_id)
    
    # Get all field names from the Employee model
    columns = [f.name for f in Employee._meta.get_fields() if not f.is_relation]
    
    # Create a sample row with the site name
    sample_data = {col: '' for col in columns}
    sample_data['site'] = site.site_name
    
    df = pd.DataFrame([sample_data], columns=columns)
    
    response = HttpResponse(
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = f'attachment; filename=employee_upload_template_{site.site_code}.xlsx'
    with pd.ExcelWriter(response, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='EmployeeTemplate')
    return response


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


# Aadhar verification and bank account verification
API_KEY = "Enter your API KEY here"

def verify_employee(request):
    if request.method == 'POST':
        form = VerificationRequestForm(request.POST)
        if form.is_valid():
            verification = form.save(commit=False)
            api_response = {}
            status = 'pending'
            score = None
            message = ''

            headers = {
                'Authorization': f'Bearer {API_KEY}',
                'Content-Type': 'application/json'
            }

            if verification.verification_type == 'aadhaar':
                response = requests.post(
                    'https://api.surepass.io/v1/aadhaar/okyc',
                    json={
                        'aadhaar_number': verification.aadhaar_number,
                        'name': verification.full_name,
                        'dob': verification.date_of_birth.strftime('%d-%m-%Y'),
                        'mobile': verification.mobile_number
                    },
                    headers=headers
                )
            elif verification.verification_type == 'bank_account':
                response = requests.post(
                    'https://api.surepass.io/v1/bank-verification',
                    json={
                        'bank_account_number': verification.bank_account_number,
                        'ifsc': verification.bank_ifsc_code
                    },
                    headers=headers
                )

            if response.status_code == 200:
                api_response = response.json()
                status = 'verified' if api_response.get('verified') else 'failed'
                score = api_response.get('score')
                message = api_response.get('message', 'Verification completed')
            else:
                status = 'failed'
                message = f"API Error: {response.status_code}"

            verification.status = status
            verification.verification_response = api_response
            verification.verification_score = score
            verification.verification_message = message
            if status == 'verified':
                verification.verified_at = now()
            verification.save()
            return redirect('verification_detail', pk=verification.pk)
    else:
        form = VerificationRequestForm()
    return render(request, 'employees/verify_employee.html', {'form': form})

def verification_detail(request, pk):
    verification = get_object_or_404(VerificationRequest, pk=pk)
    return render(request, 'verification_detail.html', {'verification': verification})

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
    # Get the selected month, year, and site from the request
    month = request.GET.get('month', '')
    year = request.GET.get('year', '')
    site_id = request.GET.get('site', '')

    # Filter salaries based on month, year, and site
    salaries = Salary.objects.all()
    if site_id:
        salaries = salaries.filter(employee__site_id=site_id)
    if month:
        salaries = salaries.filter(month=month)
    if year:
        salaries = salaries.filter(year=year)

    # Calculate total number of unique employees for the filtered salaries
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
    sites = Site.objects.all()

    context = {
        'salaries': salaries,
        'sites': sites,
        'month_choices' : month_choices,
        'month': month,
        'year': year,
        'selected_site_id': site_id,
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
    # Handle form submission
    if request.method == 'POST':
        form = PaymentForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('employees:payment_input')
    else:
        form = PaymentForm()

    # Initialize the queryset for filtering
    payments = Payment.objects.all()

    # Apply filters based on GET parameters
    company_name = request.GET.get('company_name', '').strip()
    payment_status = request.GET.get('payment_status', '').strip()
    from_date = request.GET.get('from_date')
    to_date = request.GET.get('to_date')

    # Debugging log to see what filters are applied
    print("Filter parameters:", company_name, payment_status, from_date, to_date)

    # Apply filters if the parameters are present
    if company_name:
        payments = payments.filter(company_name__icontains=company_name)
    if payment_status:
        payments = payments.filter(payment_status=payment_status)

    # Filter by date range if dates are provided
    if from_date and to_date:
        try:
            from_date_obj = datetime.strptime(from_date, "%Y-%m-%d").date()
            to_date_obj = datetime.strptime(to_date, "%Y-%m-%d").date()
            payments = payments.filter(payment_date__range=(from_date_obj, to_date_obj))
        except ValueError:
            print("Invalid date format")  # Handle date format issues gracefully

    # Render the template with the form and filtered payments
    return render(request, 'employees/payment_input.html', {
        'form': form,
        'payments': payments
    })

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

# Update View
def vendor_information_update(request, pk):
    vendor = get_object_or_404(VendorInformation, pk=pk)
    if request.method == 'POST':
        form = VendorInformationForm(request.POST, instance=vendor)
        if form.is_valid():
            form.save()
            return redirect('employees:vendor_information_input')  # Redirect to view all vendors after update
        else:
            print("Form errors:", form.errors)  # Debug statement to print form errors
    else:
        form = VendorInformationForm(instance=vendor)
    return render(request, 'employees/vendor_information_update.html', {'form': form, 'vendor': vendor})

# Delete View
def vendor_information_delete(request, pk):
    vendor = get_object_or_404(VendorInformation, pk=pk)
    if request.method == 'POST':
        vendor.delete()
        return redirect('employees:vendor_information_input')
    return render(request, 'employees/vendor_information_delete.html', {'vendor': vendor})


def purchase_item_input(request):
    # Use the already defined PurchaseItemFormSet from forms.py
    from .forms import PurchaseItemFormSet

    # ✅ Get selected vendor ID
    selected_vendor_id = request.GET.get('vendor_id')
    selected_vendor = None

    # ✅ Try to get selected vendor
    if selected_vendor_id:
        try:
            selected_vendor = VendorInformation.objects.get(id=selected_vendor_id)
        except VendorInformation.DoesNotExist:
            selected_vendor = None

    # ✅ Handle POST
    if request.method == "POST":
        formset = PurchaseItemFormSet(request.POST)
        if formset.is_valid():
            instances = formset.save(commit=False)
            for instance in instances:
                if selected_vendor:
                    instance.order_for = selected_vendor
                instance.save()
            formset.save_m2m()
            messages.success(request, "Purchase items saved successfully.")
            return redirect(f"{reverse('employees:purchase_item_input')}?vendor_id={selected_vendor_id or ''}")
        else:
            # Show detailed error messages
            error_messages = []
            for i, form in enumerate(formset):
                if form.errors:
                    for field, errors in form.errors.items():
                        for error in errors:
                            error_messages.append(f"Form {i+1}, {field}: {error}")
            if formset.non_form_errors():
                error_messages.extend(formset.non_form_errors())
            
            error_msg = "Form validation errors: " + "; ".join(error_messages) if error_messages else "Unknown form error"
            messages.error(request, error_msg)
    else:
        formset = PurchaseItemFormSet(queryset=PurchaseItem.objects.none())

    # ✅ Filter purchases
    purchases = PurchaseItem.objects.all().order_by('-bill_number')
    if selected_vendor:
        purchases = purchases.filter(order_for=selected_vendor)

    paginator = Paginator(purchases, 10)
    page_number = request.GET.get('page')
    purchases = paginator.get_page(page_number)

    vendors = VendorInformation.objects.all()

    context = {
        'formset': formset,
        'purchases': purchases,
        'vendors': vendors,
        'selected_vendor_id': selected_vendor_id,
    }

    return render(request, 'employees/purchase_item_input.html', context)



def purchase_bill_detail(request, bill_number):
    purchases = PurchaseItem.objects.filter(bill_number=bill_number)
    if not purchases.exists():
        return redirect('employees:purchase_item_input')

    context = {
        'bill_number': bill_number,
        'purchases': purchases,
    }
    return render(request, 'employees/purchase_bill_detail.html', context)

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
        # Salary rules/other fields are now managed at Site level, not Company

        if company_form.is_valid():
            company = company_form.save()

            messages.success(request, "Company added successfully!")
            return redirect('employees:company_list')

    else:
        company_form = CompanyForm()

    return render(request, 'employees/company_add_update.html', {
        'company_form': company_form,
        'is_update': False,
    })

def company_detail(request, company_id):
    # Fetch company and related data
    company = get_object_or_404(Company, id=company_id)
    # Salary rules are defined per Site now. Show sites under this company if applicable.
    salary_rules = SalaryRule.objects.none()
    salary_other_fields = SalaryOtherField.objects.none()

    return render(request, 'employees/company_detail.html', {
        'company': company,
        'salary_rules': salary_rules,
        'salary_other_fields': salary_other_fields,
    })

def company_update(request, company_id):
    company = get_object_or_404(Company, id=company_id)

    if request.method == 'POST':
        company_form = CompanyForm(request.POST, instance=company)

        if company_form.is_valid():
            company_form.save()

            messages.success(request, "Company updated successfully!")
            return redirect('employees:company_list')
    else:
        company_form = CompanyForm(instance=company)

    return render(request, 'employees/company_add_update.html', {
        'company_form': company_form,
        'is_update': True,
    })

def delete_company(request, company_id):
    company = get_object_or_404(Company, id=company_id)
    company.delete()
    messages.success(request, "Company deleted successfully!")
    return redirect('employees:company_list')


def site_list(request):
    query = request.GET.get('q', '')
    sites = Site.objects.filter(site_name__icontains=query) if query else Site.objects.all()
    context = {
        'sites': sites,
        'query': query,
    }
    return render(request, 'employees/site_list.html', context)

def site_add(request):
    if request.method == 'POST':
        form = SiteForm(request.POST)
        salary_rule_formset = SalaryRuleFormSet(request.POST, queryset=SalaryRule.objects.none())
        salary_other_field_formset = SalaryOtherFieldFormSet(request.POST, queryset=SalaryOtherField.objects.none())

        if form.is_valid() and salary_rule_formset.is_valid() and salary_other_field_formset.is_valid():
            site = form.save()
            for rule_form in salary_rule_formset:
                if not rule_form.has_changed():
                    continue
                salary_rule = rule_form.save(commit=False)
                salary_rule.site = site
                salary_rule.save()

            for other_form in salary_other_field_formset:
                if not other_form.has_changed():
                    continue
                salary_other = other_form.save(commit=False)
                salary_other.site = site
                salary_other.save()

            messages.success(request, "Site added successfully!")
            return redirect('employees:site_list')
        else:
            # Debug: Print form errors
            print("Form validation errors:", form.errors, salary_rule_formset.errors, salary_other_field_formset.errors)
            messages.error(request, "Form validation failed. Please review the errors.")
    else:
        form = SiteForm()
        salary_rule_formset = SalaryRuleFormSet(queryset=SalaryRule.objects.none())
        salary_other_field_formset = SalaryOtherFieldFormSet(queryset=SalaryOtherField.objects.none())

    return render(request, 'employees/site_form.html', {
        'form': form,
        'salary_rule_formset': salary_rule_formset,
        'salary_other_field_formset': salary_other_field_formset,
    })

def site_detail(request, site_id):
    site = get_object_or_404(Site, id=site_id)
    return render(request, 'employees/site_detail.html', {
        'site': site,
    })

def site_update(request, site_id):
    site = get_object_or_404(Site, id=site_id)
    if request.method == 'POST':
        form = SiteForm(request.POST, instance=site)
        salary_rule_formset = SalaryRuleFormSet(request.POST, queryset=SalaryRule.objects.filter(site=site))
        salary_other_field_formset = SalaryOtherFieldFormSet(request.POST, queryset=SalaryOtherField.objects.filter(site=site))

        if form.is_valid() and salary_rule_formset.is_valid() and salary_other_field_formset.is_valid():
            site = form.save()
            for rule_form in salary_rule_formset:
                salary_rule = rule_form.save(commit=False)
                salary_rule.site = site
                salary_rule.save()

            for other_form in salary_other_field_formset:
                salary_other = other_form.save(commit=False)
                salary_other.site = site
                salary_other.save()

            messages.success(request, "Site updated successfully!")
            return redirect('employees:site_list')
        else:
            # Debug: Print form errors
            print("Form validation errors:", form.errors, salary_rule_formset.errors, salary_other_field_formset.errors)
            messages.error(request, "Form validation failed. Please review the errors.")
    else:
        form = SiteForm(instance=site)
        salary_rule_formset = SalaryRuleFormSet(queryset=SalaryRule.objects.filter(site=site))
        salary_other_field_formset = SalaryOtherFieldFormSet(queryset=SalaryOtherField.objects.filter(site=site))

    return render(request, 'employees/site_form.html', {
        'form': form,
        'salary_rule_formset': salary_rule_formset,
        'salary_other_field_formset': salary_other_field_formset,
    })

def delete_site(request, site_id):
    site = get_object_or_404(Site, id=site_id)
    site.delete()
    messages.success(request, "Site deleted successfully!")
    return redirect('employees:site_list')


# Upload view for attendance, advance, and arrears files
def sample_download(request, site_id, month, year):
    """
    Generates a sample Excel template with data from the previous month.
    """
    try:
        site = Site.objects.get(id=site_id)
    except Site.DoesNotExist:
        return HttpResponse("Site not found.", status=404)

    # Calculate previous month and year
    prev_month = month - 1
    prev_year = year
    if prev_month == 0:
        prev_month = 12
        prev_year = year - 1

    # Get all employees for the site
    employees = Employee.objects.filter(site=site)
    
    # Get previous month's data
    previous_attendance = EmployeesAttendance.objects.filter(
        employee__site=site, month=prev_month, year=prev_year
    ).values('employee__employee_code', 'days_worked')
    
    previous_advances = CompanyAdvanceTransaction.objects.filter(
        site=site, month=prev_month, year=prev_year
    ).values('employee_id', 'amount')

    previous_arrears = Arrear.objects.filter(
        site=site, month=prev_month, year=prev_year
    ).values('employee_id', 'basic_salary_arrears') # Assuming this is the main arrears field

    # Create DataFrames
    attendance_df = pd.DataFrame(list(previous_attendance)).rename(columns={'employee__employee_code': 'employee_code', 'days_worked': 'last_month_days_worked'})
    advances_df = pd.DataFrame(list(previous_advances)).rename(columns={'employee_id': 'employee_code', 'amount': 'last_month_advance'})
    arrears_df = pd.DataFrame(list(previous_arrears)).rename(columns={'employee_id': 'employee_code', 'basic_salary_arrears': 'last_month_arrears'})

    # Employee data
    employee_data = employees.values('employee_code', 'name')
    df = pd.DataFrame(list(employee_data))

    # Merge with previous month's data
    if not attendance_df.empty:
        df = pd.merge(df, attendance_df, on='employee_code', how='left')
    if not advances_df.empty:
        df = pd.merge(df, advances_df, on='employee_code', how='left')
    if not arrears_df.empty:
        df = pd.merge(df, arrears_df, on='employee_code', how='left')
    
    # Add columns for new data
    df['days_worked'] = ''
    df['advance_amount'] = ''
    df['arrears_amount'] = ''

    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = f'attachment; filename="monthly_data_{site.site_name}_{month}_{year}.xlsx"'

    with pd.ExcelWriter(response, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='MonthlyData')
        
    return response

def employees_upload_details(request):
    sites = Site.objects.all()
    months = MONTH_CHOICES

    if request.method == 'POST':
        form_type = request.POST.get('form_type')
        site_id = request.POST.get('site')  # Changed from site_id to site to match form
        month = request.POST.get('month')
        year = request.POST.get('year')
        
        # Validate required fields
        if not all([site_id, month, year]):
            messages.error(request, "Please select site, month and year")
            return redirect('employees:employees_upload_details')
            
        try:
            month = int(month)
            year = int(year)
        except (TypeError, ValueError):
            messages.error(request, "Invalid month or year value")
            return redirect('employees:employees_upload_details')
            
        employee_code = request.POST.get('employee_code')

        try:
            site = Site.objects.get(id=site_id)

            if form_type == 'bulk_upload':
                upload_file = request.FILES.get('upload_file')
                upload_type = request.POST.get('upload_type')
                
                df = pd.read_excel(upload_file)
                errors = []
                
                for index, row in df.iterrows():
                    emp_code = row.get('employee_code')
                    if not emp_code:
                        continue

                    emp = Employee.objects.filter(employee_code=str(emp_code), site=site).first()
                    if not emp:
                        errors.append(f"Row {index + 2}: Employee '{emp_code}' not found in site '{site.site_name}'.")
                        continue

                    # Update attendance if present
                    if upload_type == 'attendance' and 'days_worked' in df.columns and pd.notna(row.get('days_worked')):
                        days_worked = int(row['days_worked'])
                        EmployeesAttendance.objects.update_or_create(
                            employee=emp, year=year, month=month,
                            defaults={'days_worked': days_worked}
                        )
                    
                    # Update advance if present
                    elif upload_type == 'advance' and 'advance_amount' in df.columns and pd.notna(row.get('advance_amount')):
                        try:
                            advance = Decimal(str(row['advance_amount']))
                            CompanyAdvanceTransaction.objects.update_or_create(
                                site=site, employee_id=emp_code, month=month, year=year,
                                defaults={'amount': advance}
                            )
                        except (ValueError, decimal.InvalidOperation) as e:
                            errors.append(f"Row {index + 2}: Invalid advance amount '{row.get('advance_amount')}' for employee '{emp_code}'.")

                    # Update arrears if present
                    elif upload_type == 'arrears' and 'arrears_amount' in df.columns and pd.notna(row.get('arrears_amount')):
                        arrears = Decimal(row['arrears_amount'])
                        Arrear.objects.update_or_create(
                            site=site, employee_id=emp_code, month=month, year=year,
                            defaults={'basic_salary_arrears': arrears}
                        )

                if errors:
                    messages.error(request, "Upload failed with errors: " + "; ".join(errors))
                else:
                    messages.success(request, "Monthly data uploaded successfully!")

            elif form_type == 'attendance':
                employee_codes = request.POST.getlist('employee_code[]')
                days_worked_list = request.POST.getlist('days_worked[]')
                success_count = 0
                
                for emp_code, days in zip(employee_codes, days_worked_list):
                    try:
                        emp = Employee.objects.get(employee_code=emp_code, site=site)
                        days_worked = int(days)
                        EmployeesAttendance.objects.update_or_create(
                            employee=emp, year=year, month=month,
                            defaults={'days_worked': days_worked}
                        )
                        success_count += 1
                    except Employee.DoesNotExist:
                        messages.error(request, f"Employee {emp_code} not found")
                    except ValueError:
                        messages.error(request, f"Invalid days worked value for employee {emp_code}")
                
                if success_count > 0:
                    messages.success(request, f"Attendance saved for {success_count} employees")

            elif form_type == 'advance':
                employee_codes = request.POST.getlist('employee_code[]')
                advance_amounts = request.POST.getlist('advance_amount[]')
                success_count = 0
                
                for emp_code, amount in zip(employee_codes, advance_amounts):
                    try:
                        emp = Employee.objects.get(employee_code=emp_code, site=site)
                        advance_amount = Decimal(amount)
                        CompanyAdvanceTransaction.objects.update_or_create(
                            site=site, employee_id=emp_code, month=month, year=year,
                            defaults={'amount': advance_amount}
                        )
                        success_count += 1
                    except Employee.DoesNotExist:
                        messages.error(request, f"Employee {emp_code} not found")
                    except (ValueError, decimal.InvalidOperation):
                        messages.error(request, f"Invalid advance amount for employee {emp_code}")
                
                if success_count > 0:
                    messages.success(request, f"Advance saved for {success_count} employees")

            elif form_type == 'arrear':
                employee_codes = request.POST.getlist('employee_code[]')
                arrear_amounts = request.POST.getlist('arrear_amount[]')
                success_count = 0
                
                for emp_code, amount in zip(employee_codes, arrear_amounts):
                    try:
                        emp = Employee.objects.get(employee_code=emp_code, site=site)
                        arrear_amount = Decimal(amount)
                        Arrear.objects.update_or_create(
                            site=site, employee_id=emp_code, month=month, year=year,
                            defaults={'basic_salary_arrears': arrear_amount}
                        )
                        success_count += 1
                    except Employee.DoesNotExist:
                        messages.error(request, f"Employee {emp_code} not found")
                    except (ValueError, decimal.InvalidOperation):
                        messages.error(request, f"Invalid arrear amount for employee {emp_code}")
                
                if success_count > 0:
                    messages.success(request, f"Arrear saved for {success_count} employees")

        except Site.DoesNotExist:
            messages.error(request, "Selected site not found")
        except Employee.DoesNotExist:
            messages.error(request, f"Employee with code {employee_code} not found in selected site")
        except Exception as e:
            messages.error(request, f"An error occurred: {str(e)}")

        return redirect('employees:employees_upload_details')

    context = {
        'sites': sites,
        'months': months,
    }
    return render(request, 'employees/employees_upload_details.html', context)

@login_required
def search_employee(request):
    site_id = request.GET.get('site_id')
    employee_code = request.GET.get('employee_code')

    if not site_id or not employee_code:
        return JsonResponse({
            'success': False,
            'message': 'Site ID and Employee Code are required'
        })

    try:
        employee = Employee.objects.get(site_id=site_id, employee_code=employee_code)
        return JsonResponse({
            'success': True,
            'employee': {
                'name': employee.name or '',
                'bank_account': employee.employee_account or '',
                'ifsc': employee.ifsc or ''
            }
        })
    except Employee.DoesNotExist:
        return JsonResponse({
            'success': False,
            'message': f'Employee with code {employee_code} not found in selected site'
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Error searching for employee: {str(e)}'
        })



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

# Creating, editing invoice








# Report from all model
class ReportView(View):
    template_name = 'employees/report.html'

    def get(self, request):
        form = ReportForm()
        return render(request, self.template_name, {'form': form})

    def post(self, request):
        form = ReportForm(request.POST)
        if form.is_valid():
            report = form.save(commit=False)
            report_data = report.generate_report_data()

            if not report_data:
                return render(request, self.template_name, {
                    'form': form,
                    'message': 'No data found for the selected criteria.'
                })

            # report_data is already a list of dictionaries
            data_list = report_data

            # Generate a downloadable report as Excel file
            if 'download' in request.POST:
                df = pd.DataFrame(data_list)
                response = HttpResponse(
                    content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
                response['Content-Disposition'] = f'attachment; filename={report.report_type}_report.xlsx'
                with pd.ExcelWriter(response, engine='openpyxl') as writer:
                    df.to_excel(writer, index=False, sheet_name='Report')
                return response

            return render(request, self.template_name, {'form': form, 'report_data': data_list})
        return render(request, self.template_name, {'form': form})

# E-Invoice Views
@login_required
def e_invoice_list(request):
    """List all e-invoices"""
    invoices = EInvoice.objects.all().order_by('-created_at')
    return render(request, 'employees/e_invoice_list.html', {'invoices': invoices})

@login_required
def e_invoice_create(request):
    """Create a new e-invoice with line items"""
    if request.method == 'POST':
        form = EInvoiceForm(request.POST)
        formset = EInvoiceLineItemFormSet(request.POST)
        
        if form.is_valid() and formset.is_valid():
            # Save the invoice first
            invoice = form.save()
            
            # Generate IRN
            invoice.irn = invoice.generate_irn()
            invoice.save()
            
            # Save line items
            for line_form in formset:
                if line_form.cleaned_data and not line_form.cleaned_data.get('DELETE', False):
                    line_item = line_form.save(commit=False)
                    line_item.invoice = invoice
                    line_item.save()
            
            messages.success(request, 'E-Invoice created successfully!')
            return redirect('employees:e_invoice_detail', pk=invoice.pk)
    else:
        form = EInvoiceForm()
        formset = EInvoiceLineItemFormSet(queryset=EInvoiceLineItem.objects.none())
    
    return render(request, 'employees/e_invoice_form.html', {
        'form': form,
        'formset': formset
    })

@login_required
def e_invoice_update(request, pk):
    """Update an existing e-invoice"""
    invoice = get_object_or_404(EInvoice, pk=pk)
    
    if request.method == 'POST':
        form = EInvoiceForm(request.POST, instance=invoice)
        formset = EInvoiceLineItemFormSet(request.POST, queryset=invoice.line_items.all())
        
        if form.is_valid() and formset.is_valid():
            # Save the invoice
            invoice = form.save()
            
            # Save line items
            for line_form in formset:
                if line_form.cleaned_data:
                    if line_form.cleaned_data.get('DELETE', False):
                        if line_form.instance.pk:
                            line_form.instance.delete()
                    else:
                        line_item = line_form.save(commit=False)
                        line_item.invoice = invoice
                        line_item.save()
            
            messages.success(request, 'E-Invoice updated successfully!')
            return redirect('employees:e_invoice_detail', pk=invoice.pk)
    else:
        form = EInvoiceForm(instance=invoice)
        formset = EInvoiceLineItemFormSet(queryset=invoice.line_items.all())
    
    return render(request, 'employees/e_invoice_form.html', {
        'form': form,
        'formset': formset,
        'invoice': invoice
    })

@login_required
def e_invoice_detail(request, pk):
    """View e-invoice details"""
    invoice = get_object_or_404(EInvoice, pk=pk)
    line_items = invoice.line_items.all()
    return render(request, 'employees/e_invoice_detail.html', {
        'invoice': invoice,
        'line_items': line_items
    })

@login_required
def e_invoice_delete(request, pk):
    """Delete an e-invoice"""
    invoice = get_object_or_404(EInvoice, pk=pk)
    if request.method == 'POST':
        invoice.delete()
        messages.success(request, 'E-Invoice deleted successfully!')
        return redirect('employees:e_invoice_list')
    return render(request, 'employees/e_invoice_confirm_delete.html', {'invoice': invoice})


# Bill Template Management Views
@login_required
def bill_template_list(request):
    """List all bill templates for the user's site"""
    user_site = getattr(request.user.profile, 'site', None)
    if user_site:
        templates = BillTemplate.objects.filter(site=user_site)
    else:
        templates = BillTemplate.objects.all()
    
    return render(request, 'employees/bill_template_list.html', {'templates': templates})


@login_required
def bill_template_create(request):
    """Create a new bill template"""
    if request.method == 'POST':
        form = BillTemplateForm(request.POST)
        if form.is_valid():
            template = form.save(commit=False)
            # Set the site to user's site if available
            user_site = getattr(request.user.profile, 'site', None)
            if user_site:
                template.site = user_site
            else:
                # If no user site, require site selection or use first available
                template.site = Site.objects.first()
            template.save()
            messages.success(request, 'Bill template created successfully!')
            return redirect('employees:bill_template_list')
    else:
        form = BillTemplateForm()
    
    return render(request, 'employees/bill_template_form.html', {'form': form})


@login_required
def bill_template_update(request, pk):
    """Update an existing bill template"""
    template = get_object_or_404(BillTemplate, pk=pk)
    
    if request.method == 'POST':
        form = BillTemplateForm(request.POST, instance=template)
        if form.is_valid():
            form.save()
            messages.success(request, 'Bill template updated successfully!')
            return redirect('employees:bill_template_list')
    else:
        form = BillTemplateForm(instance=template)
    
    return render(request, 'employees/bill_template_form.html', {
        'form': form,
        'template': template
    })


@login_required
def bill_template_detail(request, pk):
    """View bill template details"""
    template = get_object_or_404(BillTemplate, pk=pk)
    return render(request, 'employees/bill_template_detail.html', {'template': template})


@login_required
def bill_template_delete(request, pk):
    """Delete a bill template"""
    template = get_object_or_404(BillTemplate, pk=pk)
    if request.method == 'POST':
        template.delete()
        messages.success(request, 'Bill template deleted successfully!')
        return redirect('employees:bill_template_list')
    return render(request, 'employees/bill_template_confirm_delete.html', {'template': template})


# Service Bill Management Views
@login_required
def service_bill_list(request):
    """List all service bills for the user's site"""
    user_site = getattr(request.user.profile, 'site', None)
    if user_site:
        bills = ServiceBill.objects.filter(site=user_site).order_by('-created_at')
    else:
        bills = ServiceBill.objects.all().order_by('-created_at')

    # Add filtering options
    status_filter = request.GET.get('status')
    if status_filter:
        bills = bills.filter(status=status_filter)

    # Calculate statistics
    total_amount = bills.aggregate(total=Sum('total_amount'))['total'] or 0
    sent_count = bills.filter(status='sent').count()
    paid_count = bills.filter(status='paid').count()

    return render(request, 'employees/service_bill_list.html', {
        'bills': bills,
        'status_choices': ServiceBill.STATUS_CHOICES,
        'total_amount': total_amount,
        'sent_count': sent_count,
        'paid_count': paid_count,
    })


@login_required
def service_bill_create(request):
    """Create a new service bill with line items"""
    user_site = getattr(request.user.profile, 'site', None)
    sites = Site.objects.all()
    
    if request.method == 'POST':
        logger.debug(f"POST data received: {request.POST}")
        
        form = ServiceBillForm(request.POST, site=user_site)
        formset = ServiceBillItemFormSet(request.POST)
        
        logger.debug(f"Form is_valid: {form.is_valid()}")
        logger.debug(f"Formset is_valid: {formset.is_valid()}")
        
        if not form.is_valid():
            logger.error(f"Form errors: {form.errors}")
            logger.error(f"Form non-field errors: {form.non_field_errors()}")
        
        if not formset.is_valid():
            logger.error(f"Formset errors: {formset.errors}")
            logger.error(f"Formset non-form errors: {formset.non_form_errors()}")
        
        if form.is_valid() and formset.is_valid():
            try:
                # Save the bill first
                bill = form.save(commit=False)
                if user_site:
                    bill.site = user_site
                else:
                    bill.site = Site.objects.first()
                
                logger.debug(f"About to save bill with site: {bill.site}")
                bill.save()
                logger.debug(f"Bill saved successfully with ID: {bill.pk}")
                
                # Save line items
                items_saved = 0
                for item_form in formset:
                    if item_form.cleaned_data and not item_form.cleaned_data.get('DELETE', False):
                        item = item_form.save(commit=False)
                        item.bill = bill
                        item.save()
                        items_saved += 1
                        logger.debug(f"Saved item: {item.description} - {item.amount}")
                
                logger.debug(f"Total items saved: {items_saved}")
                
                # Recalculate totals
                bill.save()
                logger.debug("Bill totals recalculated")

                # Create EInvoice
                try:
                    EInvoice.objects.create(
                        invoice_number=bill.bill_number,
                        invoice_date=bill.bill_date,
                        invoice_type='B2B',
                        document_type='INV',
                        reverse_charge=False,
                        supplier_gstin=bill.site.company.company_gst_number,
                        supplier_legal_name=bill.site.company.company_name,
                        supplier_address=bill.site.company.company_address,
                        supplier_place_of_supply=bill.site.company.company_address,
                        supplier_state_code=get_state_code(bill.site.company.company_address),
                        buyer_gstin=bill.client_gst_number or '',
                        buyer_legal_name=bill.client_name,
                        buyer_address=bill.client_address,
                        buyer_state_code=get_state_code(bill.client_address),
                        payment_terms=bill.payment_terms,
                        due_date=bill.due_date,
                        reference_document=bill.reference_document,
                        total_taxable_value=bill.taxable_value,
                        total_cgst=bill.cgst_amount,
                        total_sgst=bill.sgst_amount,
                        total_igst=bill.igst_amount,
                        total_tax_amount=bill.cgst_amount + bill.sgst_amount + bill.igst_amount,
                        total_invoice_value=bill.total_amount,
                        status='pending',
                    )
                    logger.debug("EInvoice created successfully")
                except Exception as e:
                    logger.error(f"Error creating EInvoice: {e}")
                    # Don't fail the bill creation if EInvoice fails
                
                messages.success(request, 'Service bill created successfully!')
                return redirect('employees:service_bill_detail', pk=bill.pk)
                
            except Exception as e:
                logger.error(f"Error saving bill: {e}")
                messages.error(request, f'Error creating service bill: {str(e)}')
        else:
            # Collect and display form errors
            error_messages = []
            if not form.is_valid():
                for field, errors in form.errors.items():
                    for error in errors:
                        error_messages.append(f"{field}: {error}")
            
            if not formset.is_valid():
                for i, form_errors in enumerate(formset.errors):
                    if form_errors:
                        for field, errors in form_errors.items():
                            for error in errors:
                                error_messages.append(f"Item {i+1} - {field}: {error}")
                
                if formset.non_form_errors():
                    for error in formset.non_form_errors():
                        error_messages.append(f"Formset error: {error}")
            
            if error_messages:
                messages.error(request, f'Please fix the following errors: {"; ".join(error_messages)}')
            else:
                messages.error(request, 'Please check the form and try again.')
    else:
        form = ServiceBillForm(site=user_site)
        formset = ServiceBillItemFormSet(queryset=ServiceBillItem.objects.none())
    
    return render(request, 'employees/service_bill_form.html', {
        'form': form,
        'formset': formset,
        'sites': sites
    })


@login_required
def service_bill_update(request, pk):
    """Update an existing service bill"""
    bill = get_object_or_404(ServiceBill, pk=pk)
    user_site = getattr(request.user.profile, 'site', None)
    sites = Site.objects.all()
    
    if request.method == 'POST':
        form = ServiceBillForm(request.POST, instance=bill, site=user_site)
        formset = ServiceBillItemFormSet(request.POST, queryset=bill.line_items.all())
        
        if form.is_valid() and formset.is_valid():
            # Save the bill
            bill = form.save()
            
            # Save line items
            for item_form in formset:
                if item_form.cleaned_data:
                    if item_form.cleaned_data.get('DELETE', False):
                        if item_form.instance.pk:
                            item_form.instance.delete()
                    else:
                        item = item_form.save(commit=False)
                        item.bill = bill
                        item.save()
            
            # Recalculate totals
            bill.save()
            
            messages.success(request, 'Service bill updated successfully!')
            return redirect('employees:service_bill_detail', pk=bill.pk)
    else:
        form = ServiceBillForm(instance=bill, site=user_site)
        formset = ServiceBillItemFormSet(queryset=bill.line_items.all())
    
    return render(request, 'employees/service_bill_form.html', {
        'form': form,
        'formset': formset,
        'bill': bill,
        'sites': sites
    })


@login_required
def service_bill_detail(request, pk):
    """View service bill details"""
    bill = get_object_or_404(ServiceBill, pk=pk)
    line_items = bill.line_items.all()
    return render(request, 'employees/service_bill_detail.html', {
        'bill': bill,
        'line_items': line_items
    })


@login_required
def service_bill_delete(request, pk):
    """Delete a service bill"""
    bill = get_object_or_404(ServiceBill, pk=pk)
    if request.method == 'POST':
        bill.delete()
        messages.success(request, 'Service bill deleted successfully!')
        return redirect('employees:service_bill_list')
    return render(request, 'employees/service_bill_confirm_delete.html', {'bill': bill})


@login_required
def service_bill_print(request, pk):
    """Print view for service bill"""
    bill = get_object_or_404(ServiceBill, pk=pk)
    line_items = bill.line_items.all()
    
    context = {
        'bill': bill,
        'line_items': line_items,
        'company': bill.company,
        'template': bill.template
    }
    return render(request, 'employees/service_bill_print.html', context)

def get_state_code(address):
    # Dummy: always return '27' (Maharashtra) for demo
    return '27'

@login_required
def get_vendor_details(request, vendor_id):
    """API endpoint to fetch vendor details by ID"""
    try:
        vendor = VendorInformation.objects.get(id=vendor_id)
        data = {
            'vendor_id': vendor.vendor_id,
            'vendor_name': vendor.vendor_name,
            'vendor_gst_number': vendor.vendor_gst_number,
            'vendor_address': vendor.vendor_address,
            'district': vendor.district,
            'state': vendor.state,
            'pincode': vendor.pincode,
            'vendor_account_number': vendor.vendor_account_number,
            'vendor_ifsc_code': vendor.vendor_ifsc_code,
            'vendor_contact_person_name': vendor.vendor_contact_person_name,
            'vendor_contact_person_number': vendor.vendor_contact_person_number,
        }
        return JsonResponse(data)
    except VendorInformation.DoesNotExist:
        return JsonResponse({'error': 'Vendor not found'}, status=404)

@login_required
def purchase_tabular_create(request):
    """Create purchase with multiple line items in tabular format"""
    if request.method == 'POST':
        purchase_form = PurchaseForm(request.POST, request.FILES)
        formset = PurchaseLineItemFormSet(request.POST, instance=None)
        
        if purchase_form.is_valid() and formset.is_valid():
            try:
                # Save the main purchase record
                purchase = purchase_form.save()
                
                # Save the line items
                formset.instance = purchase
                formset.save()
                
                # Calculate totals
                purchase.calculate_totals()
                
                messages.success(request, f'Purchase {purchase.bill_number} created successfully!')
                return redirect('employees:purchase_tabular_detail', purchase_id=purchase.id)
                
            except Exception as e:
                messages.error(request, f'Error creating purchase: {str(e)}')
        else:
            # Collect form errors
            errors = []
            if not purchase_form.is_valid():
                for field, field_errors in purchase_form.errors.items():
                    for error in field_errors:
                        errors.append(f"{field}: {error}")
            
            if not formset.is_valid():
                for i, form in enumerate(formset.forms):
                    if form.errors:
                        for field, field_errors in form.errors.items():
                            for error in field_errors:
                                errors.append(f"Item {i+1} - {field}: {error}")
            
            if errors:
                messages.error(request, f'Please fix the following errors: {", ".join(errors)}')
    else:
        purchase_form = PurchaseForm()
        formset = PurchaseLineItemFormSet(instance=None)
    
    vendors = VendorInformation.objects.all()
    
    context = {
        'purchase_form': purchase_form,
        'formset': formset,
        'vendors': vendors,
        'title': 'Create Purchase Order',
    }
    
    return render(request, 'employees/purchase_tabular_create.html', context)

@login_required
def purchase_tabular_detail(request, purchase_id):
    """View purchase details"""
    purchase = get_object_or_404(Purchase, id=purchase_id)
    line_items = purchase.line_items.all()
    
    context = {
        'purchase': purchase,
        'line_items': line_items,
        'title': f'Purchase {purchase.bill_number}',
    }
    
    return render(request, 'employees/purchase_tabular_detail.html', context)

@login_required
def purchase_tabular_list(request):
    """List all purchases"""
    purchases = Purchase.objects.all().order_by('-created_at')
    
    context = {
        'purchases': purchases,
        'title': 'Purchase Orders',
    }
    
    return render(request, 'employees/purchase_tabular_list.html', context)


def handle_employee_file_upload(file, site):
    """
    Handles the file upload for employees and associates them with a specific site.
    """
    try:
        df = pd.read_excel(file)
        form = EmployeeForm()
        all_columns = list(form.fields.keys())
        
        # Exclude 'site' as it's provided by the context
        all_columns.remove('site')

        required_columns = ['employee_code', 'name', 'basic']

        missing_cols = [col for col in required_columns if col not in df.columns]
        if missing_cols:
            raise ValidationError(f"Missing required columns in Excel file: {', '.join(missing_cols)}")

        for _, row in df.iterrows():
            employee_code = str(row['employee_code']).strip()
            if Employee.objects.filter(employee_code=employee_code).exists():
                continue

            employee_data = {'site': site}
            for col in all_columns:
                if col in row and pd.notna(row[col]):
                    employee_data[col] = row[col]
            
            Employee.objects.create(**employee_data)

    except Exception as e:
        raise ValidationError(f"Error processing file: {e}")

@login_required
def duplicate_site_rules(request, site_id):
    if request.method == 'POST':
        source_site = get_object_or_404(Site, id=site_id)
        target_site_id = request.POST.get('target_site')
        if not target_site_id:
            messages.error(request, "No target site selected.")
            return redirect('employees:site_detail', site_id=site_id)
        
        target_site = get_object_or_404(Site, id=target_site_id)

        # Duplicate SalaryRule
        for rule in source_site.salary_rules.all():
            rule.pk = None  # This creates a new object
            rule.site = target_site
            rule.save()

        # Duplicate SalaryOtherField
        for field in source_site.salary_other_fields.all():
            field.pk = None # This creates a new object
            field.site = target_site
            field.save()

        messages.success(request, f"Rules from {source_site.site_name} duplicated to {target_site.site_name}.")
        return redirect('employees:site_detail', site_id=target_site_id)
    
    # Redirect if not a POST request
    return redirect('employees:site_list')

@login_required
def manage_site_employee(request, site_id):
    site = get_object_or_404(Site, id=site_id)
    
    if request.method == 'POST':
        # Handles the submission of the 'Add Employee' form
        if 'add_employee' in request.POST:
            add_employee_form = EmployeeForm(request.POST)
            if add_employee_form.is_valid():
                employee = add_employee_form.save(commit=False)
                employee.site = site
                employee.save()
                messages.success(request, 'Employee added successfully!')
                return redirect('employees:manage_site_employees', site_id=site_id)
            else:
                # Iterate through form errors and display them
                for field, errors in add_employee_form.errors.items():
                    for error in errors:
                        messages.error(request, f"{field}: {error}")
                messages.error(request, 'Failed to add employee. Please check the form.')
        
        # Handles the submission of the 'Bulk Upload' form
        elif 'upload_employees' in request.POST:
            upload_form = ExcelUploadForm(request.POST, request.FILES)
            if upload_form.is_valid():
                try:
                    handle_employee_file_upload(request.FILES['file'], site)
                    messages.success(request, 'Employees uploaded successfully!')
                except ValidationError as e:
                    messages.error(request, f"File upload failed: {e}")
                return redirect('employees:manage_site_employees', site_id=site_id)
            else:
                messages.error(request, 'Upload form is not valid.')

    # For GET request or if forms were invalid on POST
    employees = Employee.objects.filter(site=site)
    add_employee_form = EmployeeForm(initial={'site': site})
    upload_form = ExcelUploadForm()

    context = {
        'site': site,
        'employees': employees,
        'add_employee_form': add_employee_form,
        'upload_form': upload_form,
    }
    return render(request, 'employees/site_employees.html', context)

@login_required
def get_employee_data(request):
    site_id = request.GET.get('site_id')
    month = request.GET.get('month')
    year = request.GET.get('year')

    if not all([site_id, month, year]):
        return JsonResponse({'error': 'Missing required parameters'}, status=400)

    try:
        # Fetch all data for the given period
        attendance = EmployeesAttendance.objects.filter(employee__site_id=site_id, month=month, year=year)
        advances = CompanyAdvanceTransaction.objects.filter(site_id=site_id, month=month, year=year)
        arrears = Arrear.objects.filter(site_id=site_id, month=month, year=year)

        # Create dictionaries for quick lookups
        attendance_map = {att.employee.employee_code: att.days_worked for att in attendance}
        advances_map = {adv.employee_id: adv.amount for adv in advances}
        arrears_map = {arr.employee_id: arr.basic_salary_arrears for arr in arrears}

        # Get all employees for the site
        employees = Employee.objects.filter(site_id=site_id)
        
        # Prepare data for JSON response
        employee_data = [
            {
                'employee_code': emp.employee_code,
                'name': emp.name,
                'days_worked': attendance_map.get(emp.employee_code, 0),
                'advance': advances_map.get(emp.employee_code, 0),
                'arrears': arrears_map.get(emp.employee_code, 0),
            }
            for emp in employees
        ]

        return JsonResponse({'employees': employee_data})

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)