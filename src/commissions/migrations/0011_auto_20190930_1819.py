# Generated by Django 2.2.5 on 2019-09-30 18:19

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('commissions', '0010_commission_organization_dependant'),
    ]

    operations = [
        migrations.AlterField(
            model_name='commission',
            name='organization_dependant',
            field=models.CharField(choices=[('bde', 'BDE'), ('bds', 'BDS')], default='bde', help_text="L'organisation à laquelle appartiens la commission", max_length=100),
        ),
    ]
