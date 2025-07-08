from django.db import migrations

def update_purchase_fields(apps, schema_editor):
    Purchase = apps.get_model('employees', 'Purchase')
    for purchase in Purchase.objects.all():
        if not purchase.bill_number:
            purchase.bill_number = '0000'
        if not purchase.po_number:
            purchase.po_number = '0000'
        if not purchase.order_by:
            purchase.order_by = 'NA'
        purchase.save()

class Migration(migrations.Migration):
    dependencies = [
        ('employees', '0047_alter_einvoice_buyer_gstin_and_more'),
    ]

    operations = [
        migrations.RunPython(update_purchase_fields),
    ] 