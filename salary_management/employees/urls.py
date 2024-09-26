from django.urls import path
from .views import EmployeeListView, GenerateSalaryView, add_employee, home, login_view, logout_view, register_view
from . import views
urlpatterns = [
    path('', EmployeeListView.as_view(), name='employee_list'),  # Correct name for the employee list
    path('add_task/', views.add_task, name='add_task'),  # to add task
    path('complete_task/<int:task_id>/', views.complete_task, name='complete_task'),
    path('delete_task/<int:task_id>/', views.delete_task, name='delete_task'),
    path('generate_salary/', GenerateSalaryView.as_view(), name='generate_salary'),
    path('add_employee/', add_employee, name='add_employee'),
    path('upload-excel/', views.upload_excel, name='upload_excel'),
    path('profile/', views.profile_detail, name='profile_detail'),
    path('payment-input/', views.payment_input, name='payment_input'),
    path('payment-success/', views.payment_success, name='payment_success'),
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('dashboard/', views.dashboard_view, name='dashboard'),
]
