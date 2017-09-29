# -*- coding: utf-8 -*-
# Generated by Django 1.11.2 on 2017-09-29 14:15
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion
import enumchoicefield.fields
import lideservices.models


class Migration(migrations.Migration):

    dependencies = [
        ('lideservices', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='extraction',
            name='extraction_batch',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='extractions', to='lideservices.ExtractionBatch'),
        ),
        migrations.AlterField(
            model_name='inhibitionbatch',
            name='type',
            field=enumchoicefield.fields.EnumChoiceField(enum_class=lideservices.models.NucleicAcidType, max_length=3),
        ),
        migrations.AlterField(
            model_name='target',
            name='type',
            field=enumchoicefield.fields.EnumChoiceField(enum_class=lideservices.models.NucleicAcidType, max_length=3),
        ),
    ]
