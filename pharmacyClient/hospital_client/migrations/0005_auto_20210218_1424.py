# Generated by Django 3.1.6 on 2021-02-18 14:24

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('hospital_client', '0004_auto_20210217_1713'),
    ]

    operations = [
        migrations.RenameModel(
            old_name='User',
            new_name='ClientUser',
        ),
    ]
