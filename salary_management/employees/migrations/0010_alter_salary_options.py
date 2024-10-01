# Generated by Django 5.1.1 on 2024-10-01 14:41

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('employees', '0009_alter_company_company_code'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='salary',
            options={'ordering': ['-year', '-month'], 'permissions': [('can_generate_payroll', 'Can generate payroll'), ('can_modify_salary', 'Can modify salary records'), ('can_view_confidential_data', 'Can view confidential data')]},
        ),
    ]
