# Generated by Django 5.1.3 on 2024-11-13 05:50

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('employees', '0029_rename_esic_employee_esic_contribution_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='employee',
            name='employee_status',
            field=models.CharField(choices=[('working', 'Working'), ('not_working', 'Not Working')], default='working', max_length=15),
        ),
        migrations.AddField(
            model_name='employee',
            name='performance_color',
            field=models.CharField(choices=[('green', 'Green'), ('yellow', 'Yellow'), ('red', 'Red')], default='green', max_length=10),
        ),
        migrations.CreateModel(
            name='Report',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('report_type', models.CharField(choices=[('Salary', 'Salary'), ('Attendance', 'Attendance'), ('Arrear', 'Arrear'), ('Advance', 'Advance'), ('PF', 'PF'), ('ESIC', 'ESIC')], max_length=20)),
                ('from_date', models.DateField()),
                ('to_date', models.DateField()),
                ('company', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='reports', to='employees.company')),
            ],
        ),
    ]