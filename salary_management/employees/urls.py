from django.urls import path
from . import views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('employee_list/', views.EmployeeListView.as_view(), name='employee_list'),
    path('', views.register_view, name='register'),  # Register page as the landing page
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('dashboard/', views.dashboard_view, name='register'),
    path('home/', views.home, name='home'),
    path('user-profile/', views.user_profile_detail, name='user_profile_detail'),
    path('admin-dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('manage-permissions/', views.manage_user_permissions, name='manage_user_permissions'),
    path('add_task/', views.add_task, name='add_task'),
    path('complete_task/<int:task_id>/', views.complete_task, name='complete_task'),
    path('delete_task/<int:task_id>/', views.delete_task, name='delete_task'),
    path('add_employee/', views.AddEmployeeAndUploadView.as_view(), name='add_employee_and_upload'),
    path('employee_profile/', views.employee_profile, name='employee_profile'),
    path('generate_salary/', views.GenerateSalaryView.as_view(), name='generate_salary'),
    path('download-template/', views.download_template, name='download_template'),
    path('payment-input/', views.payment_input, name='payment_input'),
    path('purchase-item-input/', views.purchase_item_input, name='purchase_item_input'),
    path('vendor-information-input/', views.vendor_information_input, name='vendor_information_input'),
    path('companies/', views.company_list, name='company_list'),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
