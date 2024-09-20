from django.urls import path
from .views import EmployeeListView, GenerateSalaryView, add_employee

urlpatterns = [
    path('', EmployeeListView.as_view(), name='employee_list'),  # Correct name
    path('generate_salary/', GenerateSalaryView.as_view(), name='generate_salary'),
    path('add_employee/', add_employee, name='add_employee'),
]
