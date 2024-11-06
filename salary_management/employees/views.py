from decimal import Decimal
from datetime import datetime
from django.core.exceptions import ValidationError, PermissionDenied
from django.shortcuts import render, redirect, get_object_or_404
from django.db.models import Q, Sum
from django.utils import timezone
from django.http import HttpResponse, JsonResponse
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.models import Group, User
from django.db import IntegrityError, transaction
from django.views import View
from django.views.generic import ListView
from django.views.decorators.csrf import csrf_exempt
import pandas as pd
import json
import csv

# Import custom models and forms
from .models import (Employee, Salary, Task, Profile, Payment, PurchaseItem, VendorInformation, Company,
                     StaffSalary, AdvanceTransaction, SalaryRule, SalaryOtherField, EInvoice)
from .forms import (EmployeeForm, TaskForm, ExcelUploadForm, PaymentForm, PurchaseItemForm, VendorInformationForm,
                    CompanyForm, AddCompanyForm, EmployeeSearchForm, CustomUserCreationForm, StaffSalaryForm,
                    AdvanceTransactionForm, ProfileEditForm, LoginForm, SalaryRuleFormSet, SalaryOtherFieldFormSet,
                    EInvoiceForm)



def get_user_role_flags(user):
    """Returns a dictionary with boolean flags for user roles."""
    return {
        'is_superuser': user.is_superuser,
        'is_read_write': user.groups.filter(name='Read and Write').exists(),
        'is_read_only': user.groups.filter(name='Read Only').exists()
    }

@login_required
def superuser_view(request):
    if not get_user_role_flags(request.user)['is_superuser']:
        raise PermissionDenied
    return render(request, 'employees/home.html')


@login_required
def read_write_view(request):
    if not get_user_role_flags(request.user)['is_read_write']:
        raise PermissionDenied
    return render(request, 'employees/read_write_dashboard.html')


@login_required
def read_only_view(request):
    if not get_user_role_flags(request.user)['is_read_only']:
        raise PermissionDenied
    return render(request, 'employees/read_only_dashboard.html')


@login_required
def manage_user_permissions(request):
    if not request.user.is_superuser:
        return redirect('employees:home')

    if request.method == 'POST':
        user_id, group_name = request.POST.get('user_id'), request.POST.get('group_name')
        try:
            user = User.objects.get(id=user_id)
            group = Group.objects.get(name=group_name)
        except (User.DoesNotExist, Group.DoesNotExist):
            messages.error(request, "User or Group not found.")
            return redirect('employees:manage_user_permissions')

        user.is_superuser = request.POST.get('superuser_status') == 'on'
        user.is_staff = user.is_superuser
        user.save()
        user.groups.clear()
        user.groups.add(group)

        messages.success(request, f"Permissions updated for {user.username}")
        return redirect('employees:manage_user_permissions')

    return render(request, 'employees/manage_permissions.html', {
        'users': User.objects.all(),
        'groups': Group.objects.all(),
    })


@login_required
@csrf_exempt
def save_theme_preference(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        theme = data.get('theme', 'light')
        profile = request.user.profile
        profile.theme_preference = theme
        profile.save()
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
@login_required
def register_view(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            profile = Profile.objects.create(user=user, user_type=form.cleaned_data['user_type'],
                                             company=form.cleaned_data.get('company_name'))

            if profile.user_type == 'Owner':
                owner_fields = ['organisation_name', 'organisation_address', 'contact_number', 'account_number',
                                'ifsc_code', 'gst_number']
                for field in owner_fields:
                    setattr(profile, field, form.cleaned_data.get(field, ""))
                profile.save()
                user.groups.add(Group.objects.get(name='Owner'))
            else:
                user.groups.add(Group.objects.get(name=profile.user_type))

            login(request, user)
            messages.success(request, "Registration successful! You are now logged in.")
            return redirect('employees:home')
    else:
        form = CustomUserCreationForm()

    return render(request, 'employees/register.html', {'form': form})


# Logging in a user
def login_view(request):
    if request.method == 'POST':
        form = LoginForm(request, data=request.POST)
        if form.is_valid():
            user = authenticate(request, username=form.cleaned_data['username'], password=form.cleaned_data['password'])
            if user and user.profile.company == form.cleaned_data['company_name']:
                login(request, user)
                return redirect('employees:home')
            form.add_error(None, "Invalid credentials or company association.")
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
                return redirect('employees:employee_list')
            else:
                messages.error(request, 'Failed to add employee. Please check the form.')

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

def handle_file_upload(file):
    errors = []
    try:
        df = pd.read_excel(file)
        required_columns = ['employee_code', 'name', 'father_name', 'basic', 'transport', 'canteen', 'pf', 'esic', 'advance']
        if not all(col in df.columns for col in required_columns):
            raise ValidationError("Missing required columns in the upload file.")

        for _, row in df.iterrows():
            try:
                employee_data = {
                    'employee_code': row['employee_code'].strip(),
                    'name': row['name'].strip(),
                    'father_name': row['father_name'].strip(),
                    'basic': Decimal(row.get('basic', 0)),
                    'transport': Decimal(row.get('transport', 0)),
                    'canteen': Decimal(row.get('canteen', 0)),
                    'pf': Decimal(row.get('pf', 0)),
                    'esic': Decimal(row.get('esic', 0)),
                    'advance': Decimal(row.get('advance', 0)),
                }
                if not Employee.objects.filter(employee_code=employee_data['employee_code']).exists():
                    Employee.objects.create(**employee_data)
            except Exception as e:
                errors.append(f"Error processing row {row}: {e}")
    except Exception as e:
        raise ValidationError(f"Error processing file: {e}")

    if errors:
        raise ValidationError(errors)


class GenerateSalaryView(PermissionRequiredMixin, View):
    permission_required = 'employees.can_generate_payroll'

    @transaction.atomic
    def post(self, request):
        month, year, days_in_month = request.POST.get('month'), request.POST.get('year'), request.POST.get(
            'days_in_month')
        if not all([month, year, days_in_month]):
            messages.error(request, 'Please provide all inputs.')
            return redirect('employees:generate_salary')

        employees = Employee.objects.all().select_related()
        salary_data, totals = [], {'total_gross_salary': 0, 'total_pf': 0, 'total_esic': 0, 'total_canteen': 0,
                                   'total_advance': 0, 'total_net_salary': 0}

        for employee in employees:
            try:
                days_worked = int(request.POST.get(f'days_worked_{employee.id}', 0))
                advance = Decimal(request.POST.get(f'advance_{employee.id}', 0))

                gross_salary, net_salary, pf, esic, canteen = self.calculate_salary(employee, days_worked,
                                                                                    days_in_month)
                net_salary -= advance

                Salary.objects.update_or_create(
                    employee=employee, month=month, year=year,
                    defaults={'gross_salary': gross_salary, 'net_salary': net_salary, 'advance': advance}
                )

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

                totals['total_gross_salary'] += gross_salary
                totals['total_pf'] += pf
                totals['total_esic'] += esic
                totals['total_canteen'] += canteen
                totals['total_advance'] += advance
                totals['total_net_salary'] += net_salary
            except Exception as e:
                messages.error(request, f"Error calculating salary for {employee.name}: {e}")

        return render(request, 'employees/salary_report.html', {'salary_data': salary_data, 'totals': totals})


def download_template(request):
    columns = ['employee_code', 'name', 'father_name', 'basic', 'transport', 'canteen', 'pf', 'esic', 'advance']
    df = pd.DataFrame(columns=columns)
    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = 'attachment; filename=employee_upload_template.xlsx'
    df.to_excel(response, index=False)
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
        salary_other_field_formset = SalaryOtherFieldFormSet(request.POST, queryset=SalaryOtherField.objects.none())

        if company_form.is_valid()  and salary_rule_formset.is_valid() and salary_other_field_formset.is_valid():
            company = company_form.save()
            salary_rule_formset.instance = company
            salary_rule_formset.save()

            # Set the instance for each SalaryOtherField entry to the company
            for form in salary_other_field_formset:
                salary_other_field = form.save(commit=False)
                salary_other_field.company = company
                salary_other_field.save()
            messages.success(request, "Company added successfully!")
            return redirect('employees:company_list')
    else:
        company_form = CompanyForm()
        salary_rule_formset = SalaryRuleFormSet()
        salary_other_field_formset = SalaryOtherFieldFormSet(queryset=SalaryOtherField.objects.none())

    return render(request, 'employees/company_add_update.html', {
        'company_form': company_form,
        'salary_rule_formset': salary_rule_formset,
        'salary_other_field_formset': salary_other_field_formset,
        'is_update': False,
    })


def company_update(request, company_id):
    company = get_object_or_404(Company, id=company_id)

    if request.method == 'POST':
        company_form = CompanyForm(request.POST, instance=company)
        salary_rule_formset = SalaryRuleFormSet(request.POST, queryset=company.salary_rules.all())
        salary_other_field_formset = SalaryOtherFieldFormSet(request.POST, queryset=SalaryOtherField.objects.filter(company=company))

        if company_form.is_valid() and salary_rule_formset.is_valid() and salary_other_field_formset.is_valid():
            company_form.save()
            salary_rule_formset.save()

            for form in salary_other_field_formset:
                salary_other_field = form.save(commit=False)
                salary_other_field.company = company
                salary_other_field.save()
            messages.success(request, "Company and salary rules updated successfully!")
            return redirect('employees:company_list')
    else:
        company_form = CompanyForm(instance=company)
        salary_rule_formset = SalaryRuleFormSet(instance=company)
        salary_other_field_formset = SalaryOtherFieldFormSet(queryset=SalaryOtherField.objects.filter(company=company))

    return render(request, 'employees/company_add_update.html', {
        'company_form': company_form,
        'salary_rule_formset': salary_rule_formset,
        'salary_other_field_formset': salary_other_field_formset,
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


# Creating, editing invoice
def e_invoice_list(request):
    invoices = EInvoice.objects.all()
    return render(request, 'employees/e_invoice_list.html', {'invoices': invoices})

def e_invoice_create(request):
    if request.method == 'POST':
        form = EInvoiceForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('e_invoice_list')
    else:
        form = EInvoiceForm()
    return render(request, 'employees/e_invoice_form.html', {'form': form})

# Update existing invoice
def e_invoice_update(request, pk):
    invoice = get_object_or_404(EInvoice, pk=pk)
    if request.method == 'POST':
        form = EInvoiceForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('employees:e_invoice_list')
    else:
        form = EInvoiceForm(instance=invoice)
    return render(request, 'employees/e_invoice_form.html', {'form': form})
