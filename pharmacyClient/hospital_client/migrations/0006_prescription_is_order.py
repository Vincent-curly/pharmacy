# Generated by Django 3.1.6 on 2021-02-19 15:50

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('hospital_client', '0005_auto_20210218_1424'),
    ]

    operations = [
        migrations.AddField(
            model_name='prescription',
            name='is_order',
            field=models.IntegerField(default=0, verbose_name='是否生成订单 0 未生成,n 第n次生成订单'),
        ),
    ]