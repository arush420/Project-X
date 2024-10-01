from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from employees.models import Salary

class Command(BaseCommand):
    help = 'Create groups and assign permissions'

    def handle(self, *args, **kwargs):
        # Get or create the group
        admin_group, created = Group.objects.get_or_create(name='Admin')

        # Get the permission
        content_type = ContentType.objects.get_for_model(Salary)
        can_generate_payroll = Permission.objects.get(codename='can_generate_payroll', content_type=content_type)

        # Assign permission to the group
        admin_group.permissions.add(can_generate_payroll)

        self.stdout.write(self.style.SUCCESS('Successfully created groups and assigned permissions'))
