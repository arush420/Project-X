from django.db import models

class Employee(models.Model):
    employee_code = models.CharField(max_length=20, unique=True)
    name = models.CharField(max_length=100)
    father_name = models.CharField(max_length=100)
    basic = models.DecimalField(max_digits=10, decimal_places=2)
    transport = models.DecimalField(max_digits=10, decimal_places=2)
    canteen = models.DecimalField(max_digits=10, decimal_places=2)
    pf = models.DecimalField(max_digits=10, decimal_places=2)
    esic = models.DecimalField(max_digits=10, decimal_places=2)
    advance = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    def __str__(self):
        return self.name

class Salary(models.Model):
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE)
    month = models.DateField()
    days_worked = models.IntegerField()
    total_salary = models.DecimalField(max_digits=10, decimal_places=2)
    advance_deducted = models.DecimalField(max_digits=10, decimal_places=2)
    final_salary = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"Salary for {self.employee.name} - {self.month.strftime('%B, %Y')}"
