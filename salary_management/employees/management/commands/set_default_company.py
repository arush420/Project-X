from django.core.management.base import BaseCommand
from employees.models import Profile, Company

class Command(BaseCommand):
    help = "Sets Yoko as the default company for profiles with no company set."

    def handle(self, *args, **kwargs):
        yoko_company, created = Company.objects.get_or_create(company_name="Yoko")
        updated_profiles = Profile.objects.filter(company__isnull=True).update(company=yoko_company)
        self.stdout.write(self.style.SUCCESS(f'Successfully set Yoko as the default company for {updated_profiles} profiles'))
