from django.urls import path
from .views import ( EmployeeListView, AddEmployeeAndUploadView, GenerateSalaryView, download_template, home,
    login_view, logout_view, register_view, employee_profile, user_profile_detail )
from . import views
from django.conf import settings
from django.conf.urls.static import static


urlpatterns = [
    path('', EmployeeListView.as_view(), name='employee_list'),
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('user-profile/', views.user_profile_detail, name='user_profile_detail'),
    path('admin-dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('add_task/', views.add_task, name='add_task'),
    path('complete_task/<int:task_id>/', views.complete_task, name='complete_task'),
    path('delete_task/<int:task_id>/', views.delete_task, name='delete_task'),
    path('add_employee/', AddEmployeeAndUploadView.as_view(), name='add_employee_and_upload'),
    path('employee_profile/', views.employee_profile, name='employee_profile'),
    path('generate_salary/', GenerateSalaryView.as_view(), name='generate_salary'),
    path('download-template/', download_template, name='download_template'),
    path('payment-input/', views.payment_input, name='payment_input'),
    path('purchase-item-input/', views.purchase_item_input, name='purchase_item_input'),
    path('vendor-information-input/', views.vendor_information_input, name='vendor_information_input'),
    path('companies/', views.company_list, name='company_list'),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
