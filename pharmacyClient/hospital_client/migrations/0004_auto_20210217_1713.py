# Generated by Django 3.1.6 on 2021-02-17 17:13

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('hospital_client', '0003_auto_20210217_1642'),
    ]

    operations = [
        migrations.AlterField(
            model_name='presdetails',
            name='sum_dose',
            field=models.CharField(default='0.00', max_length=10, verbose_name='处方总剂量'),
        ),
    ]
