# Generated by Django 3.1.7 on 2021-03-12 15:00

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('salary', '0003_auto_20210305_2015'),
    ]

    operations = [
        migrations.AlterField(
            model_name='salary',
            name='basic_da',
            field=models.FloatField(),
        ),
        migrations.AlterField(
            model_name='salary',
            name='conveyance',
            field=models.FloatField(),
        ),
        migrations.AlterField(
            model_name='salary',
            name='esic',
            field=models.FloatField(),
        ),
        migrations.AlterField(
            model_name='salary',
            name='hra',
            field=models.FloatField(),
        ),
        migrations.AlterField(
            model_name='salary',
            name='monthly_salary',
            field=models.FloatField(),
        ),
        migrations.AlterField(
            model_name='salary',
            name='net_salary',
            field=models.FloatField(),
        ),
        migrations.AlterField(
            model_name='salary',
            name='pf',
            field=models.FloatField(),
        ),
        migrations.AlterField(
            model_name='salary',
            name='ppa',
            field=models.FloatField(),
        ),
        migrations.AlterField(
            model_name='salary',
            name='professional_tax',
            field=models.FloatField(),
        ),
    ]