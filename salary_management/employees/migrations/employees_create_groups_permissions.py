# employees/migrations/employees_create_groups_permissions.py

from django.db import migrations

def create_groups_and_permissions(apps, schema_editor):
    Group = apps.get_model('auth', 'Group')
    Permission = apps.get_model('auth', 'Permission')
    ContentType = apps.get_model('contenttypes', 'ContentType')
    Salary = apps.get_model('employees', 'Salary')

    # Get or create the group
    admin_group, _ = Group.objects.get_or_create(name='Admin')

    # Get the permission
    content_type = ContentType.objects.get_for_model(Salary)
    can_generate_payroll = Permission.objects.get(codename='can_generate_payroll', content_type=content_type)

    # Assign permission to the group
    admin_group.permissions.add(can_generate_payroll)

class Migration(migrations.Migration):
    dependencies = [
        ('employees', '0011_auto_20241001_2013'),  # Replace with your actual migration filename
    ]

    operations = [
        migrations.RunPython(create_groups_and_permissions),
    ]
