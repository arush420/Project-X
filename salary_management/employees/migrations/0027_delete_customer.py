# Generated by Django 5.1.3 on 2024-11-07 04:10

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('employees', '0026_customer'),
    ]

    operations = [
        migrations.DeleteModel(
            name='Customer',
        ),
    ]