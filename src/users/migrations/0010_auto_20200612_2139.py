# Generated by Django 3.0.7 on 2020-06-12 19:39

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0009_merge_20200203_1830'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='user',
            options={'permissions': [('view_full_profile', 'Can view a complete profile of other users')], 'verbose_name': 'user', 'verbose_name_plural': 'users'},
        ),
    ]
