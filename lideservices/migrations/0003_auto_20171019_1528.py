# -*- coding: utf-8 -*-
# Generated by Django 1.11.2 on 2017-10-19 15:28
from __future__ import unicode_literals

import datetime
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('lideservices', '0002_auto_20171019_1523'),
    ]

    operations = [
        migrations.CreateModel(
            name='Unit',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_date', models.DateField(blank=True, db_index=True, default=datetime.date.today, null=True)),
                ('modified_date', models.DateField(auto_now=True, null=True)),
                ('name', models.CharField(max_length=128, unique=True)),
                ('description', models.TextField(blank=True)),
                ('created_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='unit_creator', to=settings.AUTH_USER_MODEL)),
                ('modified_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='unit_modifier', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'db_table': 'lide_units',
            },
        ),
        migrations.RemoveField(
            model_name='unittype',
            name='created_by',
        ),
        migrations.RemoveField(
            model_name='unittype',
            name='modified_by',
        ),
        migrations.AlterField(
            model_name='pcrreplicate',
            name='concentration_unit',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='pcr_replicates', to='lideservices.Unit'),
        ),
        migrations.AlterField(
            model_name='sample',
            name='meter_reading_unit',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='samples_meter_units', to='lideservices.Unit'),
        ),
        migrations.AlterField(
            model_name='sample',
            name='total_volume_sampled_unit_initial',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='samples_tvs_units', to='lideservices.Unit'),
        ),
        migrations.DeleteModel(
            name='UnitType',
        ),
    ]
