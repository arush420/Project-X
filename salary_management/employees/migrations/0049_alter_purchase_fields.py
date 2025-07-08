from django.db import migrations, models

class Migration(migrations.Migration):
    dependencies = [
        ('employees', '0048_update_purchase_fields'),
    ]

    operations = [
        migrations.AlterField(
            model_name='purchase',
            name='bill_number',
            field=models.CharField(default='0000', max_length=5, unique=True),
        ),
        migrations.AlterField(
            model_name='purchase',
            name='po_number',
            field=models.CharField(blank=True, default='0000', max_length=5),
        ),
        migrations.AlterField(
            model_name='purchase',
            name='order_by',
            field=models.CharField(blank=True, default='NA', max_length=50),
        ),
        migrations.AlterField(
            model_name='purchase',
            name='payment_by',
            field=models.CharField(blank=True, default='NA', max_length=50),
        ),
        migrations.AlterField(
            model_name='purchase',
            name='payment_mode',
            field=models.CharField(blank=True, choices=[('bank_transfer', 'Bank Transfer'), ('cash', 'Cash'), ('upi', 'UPI')], default='bank_transfer', max_length=20),
        ),
    ] 