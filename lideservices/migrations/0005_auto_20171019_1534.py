# -*- coding: utf-8 -*-
# Generated by Django 1.11.2 on 2017-10-19 15:34
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('lideservices', '0004_auto_20171019_1530'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='control',
            name='created_by',
        ),
        migrations.RemoveField(
            model_name='control',
            name='extraction',
        ),
        migrations.RemoveField(
            model_name='control',
            name='modified_by',
        ),
        migrations.RemoveField(
            model_name='control',
            name='target',
        ),
        migrations.RemoveField(
            model_name='control',
            name='type',
        ),
        migrations.AddField(
            model_name='target',
            name='control_type',
            field=models.ForeignKey(default='', on_delete=django.db.models.deletion.CASCADE, related_name='targets', to='lideservices.ControlType'),
            preserve_default=False,
        ),
        migrations.DeleteModel(
            name='Control',
        ),
    ]
