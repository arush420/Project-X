from django.urls import path
from .views import ( EmployeeListView, GenerateSalaryView, add_employee, home,
    login_view, logout_view, register_view )
from . import views
from django.conf import settings
from django.conf.urls.static import static


urlpatterns = [
    path('', EmployeeListView.as_view(), name='employee_list'),
    path('add_task/', views.add_task, name='add_task'),
    path('complete_task/<int:task_id>/', views.complete_task, name='complete_task'),
    path('delete_task/<int:task_id>/', views.delete_task, name='delete_task'),
    path('generate_salary/', GenerateSalaryView.as_view(), name='generate_salary'),
    path('add_employee/', add_employee, name='add_employee'),
    path('upload-excel/', views.upload_excel, name='upload_excel'),
    path('profile/', views.profile_detail, name='profile_detail'),
    path('payment-input/', views.payment_input, name='payment_input'),
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('purchase-item-input/', views.purchase_item_input, name='purchase_item_input'),
    path('vendor-information-input/', views.vendor_information_input, name='vendor_information_input'),
    path('employees/<str:employee_code>/', views.employee_detail, name='employee_detail'),
    path('employee/search/', views.employee_search, name='employee_search'),
    path('companies/', views.company_list, name='company_list'),
    path('salary/list/', views.salary_list, name='salary_list'),
    path('salary/download-csv/', views.download_salary_csv, name='download_salary_csv'),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
