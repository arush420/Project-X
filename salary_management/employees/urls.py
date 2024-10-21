from django.urls import path
from . import views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
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
    path('add_employee/', views.AddEmployeeAndUploadView.as_view(), name='add_employee_and_upload'),
    path('employees/delete_multiple/', views.delete_multiple_employees, name='delete_multiple_employees'), # Multi delete
    path('employee/<int:employee_id>/delete/', views.delete_employee, name='delete_employee'),  # Single delete
    # Download template to add bulk employees
    path('download-template/', views.download_template, name='download_template'),
    path('employee_list/', views.EmployeeListView.as_view(), name='employee_list'),
    path('employee_detail/', views.employee_detail, name='employee_detail'),
    path('employee/<int:id>/', views.employee_detail, name='employee_details'),
    path('generate_salary/', views.GenerateSalaryView.as_view(), name='generate_salary'),
    # salary List/ Report and CSV download
    path('salary_list/', views.salary_list, name='salary_list'),
    path('salary/download-csv/', views.download_salary_csv, name='download_salary_csv'),

    # Payment Input
    path('payment-input/', views.payment_input, name='payment_input'),
    path('payment/edit/<int:payment_id>/', views.edit_payment, name='edit_payment'),
    path('payment/delete/<int:payment_id>/', views.delete_payment, name='delete_payment'),
    path('purchase-item-input/', views.purchase_item_input, name='purchase_item_input'),
    path('vendor-information-input/', views.vendor_information_input, name='vendor_information_input'),
    path('companies/', views.company_list, name='company_list'),
    path('companies/delete/<int:company_id>/', views.delete_company, name='delete_company'),
    path('salaries/', views.staff_salary_list, name='staff_salary_list'),
    path('salaries/new/', views.staff_salary_create, name='staff_salary_create'),
    path('salaries/edit/<int:pk>/', views.staff_salary_update, name='staff_salary_update'),
    path('staff-salary/<int:pk>/', views.staff_salary_detail, name='staff_salary_detail'), # Detail view
    path('edit-transaction/<int:pk>/', views.edit_transaction, name='edit_transaction'),
    path('settings/', views.settings_view, name='settings'),  # Add this for the settings page
    path('save-theme-preference/', views.save_theme_preference, name='save_theme_preference'), #added this to save theme preference
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
