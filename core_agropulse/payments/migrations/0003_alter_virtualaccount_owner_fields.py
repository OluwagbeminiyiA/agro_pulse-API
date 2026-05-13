import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("payments", "0002_transfer_virtualaccount_virtualaccounttransaction_and_more"),
    ]

    operations = [
        migrations.AlterField(
            model_name="virtualaccount",
            name="farmer",
            field=models.OneToOneField(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="virtual_account",
                to="accounts.farmerprofile",
            ),
        ),
        migrations.AlterField(
            model_name="virtualaccount",
            name="transporter",
            field=models.OneToOneField(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="virtual_account",
                to="accounts.transporterprofile",
            ),
        ),
    ]
