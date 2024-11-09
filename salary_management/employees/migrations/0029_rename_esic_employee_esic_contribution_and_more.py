# Generated by Django 5.1.3 on 2024-11-09 01:35

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('employees', '0028_salaryotherfield_delete_mymodel_and_more'),
    ]

    operations = [
        migrations.RenameField(
            model_name='employee',
            old_name='esic',
            new_name='esic_contribution',
        ),
        migrations.RenameField(
            model_name='employee',
            old_name='pf',
            new_name='pf_contribution',
        ),
        migrations.AddField(
            model_name='employee',
            name='address',
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='employee',
            name='company',
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
        migrations.AddField(
            model_name='employee',
            name='department',
            field=models.CharField(blank=True, max_length=50, null=True),
        ),
        migrations.AddField(
            model_name='employee',
            name='designation',
            field=models.CharField(blank=True, max_length=50, null=True),
        ),
        migrations.AddField(
            model_name='employee',
            name='district',
            field=models.CharField(blank=True, max_length=50, null=True),
        ),
        migrations.AddField(
            model_name='employee',
            name='dob',
            field=models.DateField(blank=True, null=True, verbose_name='Date of Birth'),
        ),
        migrations.AddField(
            model_name='employee',
            name='doe',
            field=models.DateField(blank=True, null=True, verbose_name='Date of Exit'),
        ),
        migrations.AddField(
            model_name='employee',
            name='doj',
            field=models.DateField(blank=True, null=True, verbose_name='Date of Joining'),
        ),
        migrations.AddField(
            model_name='employee',
            name='email',
            field=models.EmailField(blank=True, max_length=254, null=True),
        ),
        migrations.AddField(
            model_name='employee',
            name='employee_account',
            field=models.CharField(blank=True, max_length=50, null=True),
        ),
        migrations.AddField(
            model_name='employee',
            name='employer_account',
            field=models.CharField(blank=True, max_length=50, null=True),
        ),
        migrations.AddField(
            model_name='employee',
            name='esi_no',
            field=models.CharField(blank=True, max_length=20, null=True),
        ),
        migrations.AddField(
            model_name='employee',
            name='gender',
            field=models.CharField(blank=True, choices=[('Male', 'Male'), ('Female', 'Female')], max_length=10),
        ),
        migrations.AddField(
            model_name='employee',
            name='handicap',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='employee',
            name='ifsc',
            field=models.CharField(blank=True, max_length=11, null=True),
        ),
        migrations.AddField(
            model_name='employee',
            name='kyc_status',
            field=models.CharField(blank=True, choices=[('Verified', 'Verified'), ('Pending', 'Pending')], max_length=10),
        ),
        migrations.AddField(
            model_name='employee',
            name='marital_status',
            field=models.CharField(blank=True, choices=[('UnMarried', 'UnMarried'), ('Married', 'Married'), ('Divorced', 'Divorced'), ('Widow/Widower', 'Widow/Widower')], max_length=15),
        ),
        migrations.AddField(
            model_name='employee',
            name='mobile',
            field=models.CharField(blank=True, max_length=15, null=True),
        ),
        migrations.AddField(
            model_name='employee',
            name='mother_name',
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
        migrations.AddField(
            model_name='employee',
            name='pan',
            field=models.CharField(blank=True, max_length=20, null=True),
        ),
        migrations.AddField(
            model_name='employee',
            name='pay_mode',
            field=models.CharField(blank=True, max_length=50, null=True),
        ),
        migrations.AddField(
            model_name='employee',
            name='pf_no',
            field=models.CharField(blank=True, max_length=20, null=True),
        ),
        migrations.AddField(
            model_name='employee',
            name='pincode',
            field=models.CharField(blank=True, max_length=6, null=True),
        ),
        migrations.AddField(
            model_name='employee',
            name='remarks',
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='employee',
            name='spouse_name',
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
        migrations.AddField(
            model_name='employee',
            name='state',
            field=models.CharField(blank=True, max_length=50, null=True),
        ),
        migrations.AddField(
            model_name='employee',
            name='uan',
            field=models.CharField(blank=True, max_length=20, null=True),
        ),
        migrations.CreateModel(
            name='Arrear',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('employee_id', models.CharField(max_length=50)),
                ('month', models.IntegerField()),
                ('year', models.IntegerField()),
                ('basic_salary_arrears', models.DecimalField(decimal_places=2, default=0.0, max_digits=10)),
                ('bonus_arrears', models.DecimalField(decimal_places=2, default=0.0, max_digits=10)),
                ('overtime_arrears', models.DecimalField(decimal_places=2, default=0.0, max_digits=10)),
                ('allowances_arrears', models.DecimalField(decimal_places=2, default=0.0, max_digits=10)),
                ('leave_encashment_arrears', models.DecimalField(decimal_places=2, default=0.0, max_digits=10)),
                ('salary_increment_arrears', models.DecimalField(decimal_places=2, default=0.0, max_digits=10)),
                ('company', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='employees.company')),
            ],
        ),
        migrations.CreateModel(
            name='CompanyAdvanceTransaction',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('employee_id', models.CharField(max_length=50)),
                ('amount', models.DecimalField(decimal_places=2, max_digits=10)),
                ('month', models.IntegerField()),
                ('year', models.IntegerField()),
                ('company', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='employees.company')),
            ],
        ),
        migrations.CreateModel(
            name='EmployeesAttendance',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('year', models.PositiveIntegerField()),
                ('month', models.PositiveIntegerField(choices=[(1, 'January'), (2, 'February'), (3, 'March'), (4, 'April'), (5, 'May'), (6, 'June'), (7, 'July'), (8, 'August'), (9, 'September'), (10, 'October'), (11, 'November'), (12, 'December')])),
                ('days_worked', models.PositiveIntegerField()),
                ('company', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='attendance_records', to='employees.company')),
                ('employee', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='attendance_records', to='employees.employee')),
            ],
            options={
                'verbose_name': 'Employee Attendance',
                'verbose_name_plural': 'Employee Attendance Records',
                'unique_together': {('company', 'employee', 'year', 'month')},
            },
        ),
    ]
