from django.urls import path
from . import views
from django.conf import settings
from django.conf.urls.static import static

from .views import ReportView, EmployeeUpdateView, employee_detail

urlpatterns = [
    path('', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('forgot_password/', views.forgot_password, name='forgot_password'),
    # path('dashboard/', views.dashboard_view, name='dashboard'),
    path('register/', views.register_view, name='register'),
    path('home/', views.home, name='home'),
    path('user-profile/', views.user_profile_detail, name='user_profile_detail'),
    path('admin_dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('manage-permissions/', views.manage_user_permissions, name='manage_user_permissions'),
    path('superuser-dashboard/', views.superuser_view, name='superuser_dashboard'),
    path('read-write-dashboard/', views.read_write_view, name='read_write_dashboard'),
    path('read-only-dashboard/', views.read_only_view, name='read_only_dashboard'),
    path('add_task/', views.add_task, name='add_task'),
    path('complete_task/<int:task_id>/', views.complete_task, name='complete_task'),
    path('delete_task/<int:task_id>/', views.delete_task, name='delete_task'),
    path('transfer_task/<int:task_id>/', views.transfer_task, name='transfer_task'),
    path('add_employee/', views.AddEmployeeAndUploadView.as_view(), name='add_employee_and_upload'),
    path('employees/delete_multiple/', views.delete_multiple_employees, name='delete_multiple_employees'), # Multi delete
    path('employee/<int:employee_id>/delete/', views.delete_employee, name='delete_employee'),  # Single delete

    # Download template to add bulk employees
    path('employee_list/', views.EmployeeListView.as_view(), name='employee_list'),
    path('<int:pk>/edit/', EmployeeUpdateView.as_view(), name='edit_employee'),
    path('<int:id>/', employee_detail, name='employee_detail'),
    path('employee_detail/', views.employee_detail, name='employee_detail'),
    path('employee/<int:id>/', views.employee_detail, name='employee_details'),

    # Aadhar and bank account verification
    path('verify/', views.verify_employee, name='verify_employee'),
    path('verify/<uuid:pk>/', views.verification_detail, name='verification_detail'),

    # salary List/ Report and CSV download
    path('generate_salary/', views.GenerateSalaryView.as_view(), name='generate_salary'),
    path('salary_list/', views.salary_list, name='salary_list'),
    path('salary/download-csv/', views.download_salary_csv, name='download_salary_csv'),

    # Payment Input
    path('payment-input/', views.payment_input, name='payment_input'),
    path('payment/edit/<int:payment_id>/', views.edit_payment, name='edit_payment'),
    path('payment/delete/<int:payment_id>/', views.delete_payment, name='delete_payment'),

    # Vendor inputs and Purchase details
    path('vendor-information-input/', views.vendor_information_input, name='vendor_information_input'),
    path('vendor-information/update/<int:pk>/', views.vendor_information_update, name='vendor_information_update'),
    path('vendor-information/delete/<int:pk>/', views.vendor_information_delete, name='vendor_information_delete'),
    path('purchase-item-input/', views.purchase_item_input, name='purchase_item_input'),
    path('purchase/<str:bill_number>/', views.purchase_bill_detail, name='purchase_bill_detail'),

    # Companies form
    path('companies/', views.company_list, name='company_list'),
    path('companies/add/', views.company_add, name='company_add'),
    path('companies/<int:company_id>/update/', views.company_update, name='company_update'),
    path('companies/<int:company_id>/delete/', views.delete_company, name='delete_company'),
    path('companies/<int:company_id>/detail/', views.company_detail, name='company_detail'),


    # Site form
    path('site/', views.site_list, name='site_list'),
    path('site/add/', views.site_add, name='site_add'),
    path('site/<int:site_id>/update/', views.site_update, name='site_update'),
    path('site/<int:site_id>/delete/', views.delete_site, name='delete_site'),
    path('site/<int:site_id>/detail/', views.site_detail, name='site_detail'),
    path('site/<int:site_id>/employees/', views.manage_site_employee, name='manage_site_employees'),
    path('site/<int:site_id>/download-template/', views.download_template, name='download_template'),
    path('site/<int:site_id>/duplicate_rules/', views.duplicate_site_rules, name='duplicate_site_rules'),


    # advance and attendance upload form
    path('upload/', views.employees_upload_details, name='employees_upload_details'),
    path('sample-download/<int:site_id>/<int:month>/<int:year>/', views.sample_download, name='sample_download'),

    path('salaries/', views.staff_salary_list, name='staff_salary_list'),
    path('salaries/new/', views.staff_salary_create, name='staff_salary_create'),
    path('salaries/edit/<int:pk>/', views.staff_salary_update, name='staff_salary_update'),
    path('staff-salary/<int:pk>/', views.staff_salary_detail, name='staff_salary_detail'), # Detail view
    path('edit-transaction/<int:pk>/', views.edit_transaction, name='edit_transaction'),
    path('settings/', views.settings_view, name='settings'),  # Add this for the settings page
    path('save-theme-preference/', views.save_theme_preference, name='save_theme_preference'), #added this to save theme preference

    # E-invoice
    path('e-invoices/', views.e_invoice_list, name='e_invoice_list'),  # List all e-invoices
    path('e-invoices/create/', views.e_invoice_create, name='e_invoice_create'),  # Create a new e-invoice
    path('e-invoices/<int:pk>/update/', views.e_invoice_update, name='e_invoice_update'),  # Update e-invoice
    path('e-invoices/<int:pk>/detail/', views.e_invoice_detail, name='e_invoice_detail'),  # View e-invoice details
    path('e-invoices/<int:pk>/delete/', views.e_invoice_delete, name='e_invoice_delete'),  # Delete e-invoice

    # Report
    path('generate/', ReportView.as_view(), name='generate_report'),

    # Bill Template Management
    path('bill-templates/', views.bill_template_list, name='bill_template_list'),
    path('bill-templates/create/', views.bill_template_create, name='bill_template_create'),
    path('bill-templates/<int:pk>/update/', views.bill_template_update, name='bill_template_update'),
    path('bill-templates/<int:pk>/detail/', views.bill_template_detail, name='bill_template_detail'),
    path('bill-templates/<int:pk>/delete/', views.bill_template_delete, name='bill_template_delete'),

    # Service Bill Management
    path('service-bills/', views.service_bill_list, name='service_bill_list'),
    path('service-bills/create/', views.service_bill_create, name='service_bill_create'),
    path('service-bills/<int:pk>/update/', views.service_bill_update, name='service_bill_update'),
    path('service-bills/<int:pk>/detail/', views.service_bill_detail, name='service_bill_detail'),
    path('service-bills/<int:pk>/delete/', views.service_bill_delete, name='service_bill_delete'),
    path('service-bills/<int:pk>/print/', views.service_bill_print, name='service_bill_print'),
    
    # API endpoints
    path('api/vendor/<int:vendor_id>/', views.get_vendor_details, name='get_vendor_details'),
    
    # Tabular Purchase Management
    path('purchase-tabular/', views.purchase_tabular_list, name='purchase_tabular_list'),
    path('purchase-tabular/create/', views.purchase_tabular_create, name='purchase_tabular_create'),
    path('purchase-tabular/<int:purchase_id>/', views.purchase_tabular_detail, name='purchase_tabular_detail'),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
