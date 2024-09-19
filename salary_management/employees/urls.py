from django.urls import path
from . import views

urlpatterns = [
    path('', views.employee_list, name='employee_list'),
    path('generate_salary/', views.generate_salary, name='generate_salary'),
    path('add_employee/', views.add_employee, name='add_employee'),
]
