# Generated by Django 5.1.3 on 2024-11-07 01:12

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('employees', '0024_alter_salaryrule_basic_rate_type_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='EInvoice',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('site', models.CharField(max_length=100)),
                ('department', models.BooleanField(default=False)),
                ('month', models.CharField(max_length=20)),
                ('invoice_no', models.CharField(max_length=50)),
                ('date', models.DateField()),
                ('type', models.CharField(max_length=50)),
                ('category', models.CharField(max_length=50)),
                ('service', models.CharField(max_length=100)),
                ('po_number', models.CharField(blank=True, max_length=50, null=True)),
                ('buyer', models.CharField(blank=True, max_length=100, null=True)),
                ('address', models.TextField(blank=True, null=True)),
                ('gstin', models.CharField(blank=True, max_length=15, null=True)),
                ('contact_person', models.CharField(blank=True, max_length=100, null=True)),
                ('mobile', models.CharField(blank=True, max_length=15, null=True)),
                ('state', models.CharField(blank=True, max_length=50, null=True)),
                ('city', models.CharField(blank=True, max_length=50, null=True)),
                ('pincode', models.CharField(blank=True, max_length=10, null=True)),
                ('taxable', models.DecimalField(decimal_places=2, default=0.0, max_digits=10)),
                ('igst', models.DecimalField(decimal_places=2, default=0.0, max_digits=10)),
                ('cgst', models.DecimalField(decimal_places=2, default=0.0, max_digits=10)),
                ('sgst', models.DecimalField(decimal_places=2, default=0.0, max_digits=10)),
                ('cess', models.DecimalField(decimal_places=2, default=0.0, max_digits=10)),
                ('st_cess', models.DecimalField(decimal_places=2, default=0.0, max_digits=10)),
                ('cess_non_adv', models.DecimalField(decimal_places=2, default=0.0, max_digits=10)),
                ('total', models.DecimalField(decimal_places=2, default=0.0, max_digits=10)),
                ('bill_amount', models.DecimalField(decimal_places=2, default=0.0, max_digits=10)),
                ('deduction_narration_1', models.CharField(blank=True, max_length=255, null=True)),
                ('deduction_amount_1', models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True)),
                ('deduction_narration_2', models.CharField(blank=True, max_length=255, null=True)),
                ('deduction_amount_2', models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True)),
                ('cancelled', models.BooleanField(default=False)),
                ('print_proprietor_name', models.BooleanField(default=False)),
            ],
        ),
    ]
