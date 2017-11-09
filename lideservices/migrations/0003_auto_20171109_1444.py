# -*- coding: utf-8 -*-
# Generated by Django 1.11.2 on 2017-11-09 14:44
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('lideservices', '0002_auto_20171108_1555'),
    ]

    operations = [
        migrations.AddField(
            model_name='reversetranscription',
            name='extraction_batch',
            field=models.ForeignKey(default=1, on_delete=django.db.models.deletion.CASCADE, related_name='reversetranscriptions', to='lideservices.ExtractionBatch'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='reversetranscription',
            name='re_rt_note',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AlterUniqueTogether(
            name='reversetranscription',
            unique_together=set([]),
        ),
        migrations.RemoveField(
            model_name='reversetranscription',
            name='analysis_batch',
        ),
        migrations.RemoveField(
            model_name='reversetranscription',
            name='rt_number',
        ),
    ]
