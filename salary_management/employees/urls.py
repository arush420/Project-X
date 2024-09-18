from django.urls import path
from . import views

urlpatterns = [
    path('', views.employee_list, name='employee_list'),  # Empty string for the default list view
    path('generate_salary/', views.generate_salary, name='generate_salary'),  # URL for generating salary
]
