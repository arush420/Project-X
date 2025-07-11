import os
import pandas as pd
from django.core.management.base import BaseCommand
from faker import Faker
from salary_management.employees.models import Site
from salary_management.employees.forms import EmployeeForm

class Command(BaseCommand):
    help = 'Creates a sample employee Excel file with 10 dummy employees.'

    def handle(self, *args, **options):
        fake = Faker()
        form = EmployeeForm()
        columns = list(form.fields.keys())
        
        # Exclude fields that are auto-generated or handled by the system
        excluded_fields = ['site'] 
        columns = [col for col in columns if col not in excluded_fields]
        
        data = []
        for _ in range(10):
            employee_data = {
                'employee_code': fake.unique.random_number(digits=5),
                'name': fake.name(),
                'father_name': fake.name_male(),
                'mother_name': fake.name_female(),
                'gender': fake.random_element(elements=('Male', 'Female')),
                'dob': fake.date_of_birth(minimum_age=18, maximum_age=60).strftime('%Y-%m-%d'),
                'marital_status': fake.random_element(elements=('Married', 'Unmarried')),
                'spouse_name': fake.name(),
                'mobile': fake.phone_number(),
                'email': fake.email(),
                'address': fake.address(),
                'district': fake.city(),
                'state': fake.state(),
                'pincode': fake.zipcode(),
                'pf_no': fake.random_number(digits=10),
                'esi_no': fake.random_number(digits=10),
                'uan': fake.random_number(digits=12),
                'pan': fake.random_uppercase_letter() * 5 + fake.random_number(digits=4) + fake.random_uppercase_letter(),
                'department': fake.job(),
                'designation': fake.job(),
                'doj': fake.date_between(start_date='-5y', end_date='today').strftime('%Y-%m-%d'),
                'doe': '',
                'pay_mode': 'bank',
                'employer_account': fake.bban(),
                'employee_account': fake.bban(),
                'ifsc': fake.swift(),
                'kyc_status': 'Verified',
                'handicap': False,
                'remarks': fake.text(max_nb_chars=50),
                'basic': fake.random_int(min=15000, max=50000),
                'sr_allowance': fake.random_int(min=1000, max=5000),
                'da': fake.random_int(min=1000, max=5000),
                'hra': fake.random_int(min=1000, max=5000),
                'travel_allowance': fake.random_int(min=500, max=2000),
                'medical': fake.random_int(min=500, max=2000),
                'conveyance': fake.random_int(min=500, max=2000),
                'wash_allowance': fake.random_int(min=100, max=500),
                'efficiency': fake.random_int(min=100, max=500),
                'other_payable': fake.random_int(min=100, max=500),
                'employee_status': 'working',
                'performance_color': 'green',
            }
            data.append(employee_data)
        
        df = pd.DataFrame(data, columns=columns)
        
        # Ensure the directory exists
        output_dir = 'salary_management/static/sample'
        os.makedirs(output_dir, exist_ok=True)
        
        output_path = os.path.join(output_dir, 'sample_employee_data_10.xlsx')
        df.to_excel(output_path, index=False, sheet_name='EmployeeTemplate')
        
        self.stdout.write(self.style.SUCCESS(f'Successfully created sample employee file at {output_path}')) 