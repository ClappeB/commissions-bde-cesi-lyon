# Generated by Django 2.2.5 on 2019-09-24 16:22

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('commissions', '0007_auto_20190924_1616'),
    ]

    operations = [
        migrations.AlterField(
            model_name='commission',
            name='name',
            field=models.CharField(max_length=50),
        ),
    ]