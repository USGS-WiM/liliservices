# -*- coding: utf-8 -*-
# Generated by Django 1.11.2 on 2018-03-13 16:39
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('lideservices', '0009_auto_20180309_1254'),
    ]

    operations = [
        migrations.AlterField(
            model_name='pcrreplicate',
            name='bad_result_flag',
            field=models.BooleanField(default=True),
        ),
    ]
