# Generated by Django 2.2.6 on 2019-11-07 08:23

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('commissions', '0015_commission_is_organization'),
    ]

    operations = [
        migrations.AlterField(
            model_name='event',
            name='banner',
            field=models.ImageField(blank=True, null=True, upload_to='events/photos'),
        ),
    ]