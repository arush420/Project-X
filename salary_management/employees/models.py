from django.db import models
from django.utils import timezone

class Employee(models.Model):
    employee_code = models.CharField(max_length=10, unique=True)  # Employee code should be unique
    name = models.CharField(max_length=100)
    father_name = models.CharField(max_length=100)
    basic = models.DecimalField(max_digits=10, decimal_places=2)  # Assuming basic salary is stored as currency
    transport = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)  # Added default values for optional fields
    canteen = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    pf = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)  # Added defaults for percentages
    esic = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)
    advance = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)

    def __str__(self):
        return f'{self.name} ({self.employee_code})'

class Salary(models.Model):
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='salaries')  # Added related_name for reverse lookup
    month = models.PositiveSmallIntegerField()  # PositiveSmallIntegerField is better for months (1-12)
    year = models.PositiveIntegerField()  # Used PositiveIntegerField for storing years
    gross_salary = models.DecimalField(max_digits=10, decimal_places=2)
    net_salary = models.DecimalField(max_digits=10, decimal_places=2)
    date_generated = models.DateTimeField(default=timezone.now)

    class Meta:
        unique_together = ('employee', 'month', 'year')  # Ensures that each employee gets only one salary per month/year
        ordering = ['-year', '-month']  # Default ordering by date (newest first)

    def __str__(self):
        return f'{self.employee.name} - {self.get_month_display()}/{self.year}'

    def get_month_display(self):
        """Returns the month name for display purposes."""
        return timezone.datetime(1900, self.month, 1).strftime('%B')  # Converts month number to month name (e.g., 'January')
