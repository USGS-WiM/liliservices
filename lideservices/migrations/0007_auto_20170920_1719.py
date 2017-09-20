# -*- coding: utf-8 -*-
# Generated by Django 1.11.2 on 2017-09-20 17:19
from __future__ import unicode_literals

import datetime
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('lideservices', '0006_auto_20170824_2149'),
    ]

    operations = [
        migrations.CreateModel(
            name='ExtractionMethod',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_date', models.DateField(blank=True, db_index=True, default=datetime.date.today, null=True)),
                ('modified_date', models.DateField(auto_now=True, null=True)),
                ('name', models.CharField(max_length=128, unique=True)),
                ('created_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='extractionmethod_creator', to=settings.AUTH_USER_MODEL)),
                ('modified_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='extractionmethod_modifier', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'db_table': 'lide_extractionmethod',
            },
        ),
        migrations.RemoveField(
            model_name='analysisbatch',
            name='some_field',
        ),
        migrations.AddField(
            model_name='analysisbatch',
            name='analysis_batch_description',
            field=models.CharField(blank=True, max_length=128, null=True),
        ),
        migrations.AddField(
            model_name='analysisbatch',
            name='analysis_batch_notes',
            field=models.CharField(blank=True, max_length=128, null=True),
        ),
        migrations.AddField(
            model_name='extraction',
            name='extraction_date',
            field=models.DateField(blank=True, db_index=True, default=datetime.date.today, null=True),
        ),
        migrations.AddField(
            model_name='inhibition',
            name='inhibition_date',
            field=models.DateField(blank=True, db_index=True, default=datetime.date.today, null=True),
        ),
        migrations.AddField(
            model_name='inhibition',
            name='inhibition_number',
            field=models.IntegerField(default=1, unique=True),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='reversetranscription',
            name='rt_date',
            field=models.DateField(blank=True, db_index=True, default=datetime.date.today, null=True),
        ),
        migrations.AddField(
            model_name='reversetranscription',
            name='rt_number',
            field=models.IntegerField(default=1, unique=True),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='target',
            name='name',
            field=models.CharField(default='', max_length=128, unique=True),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='inhibition',
            name='extraction',
            field=models.ManyToManyField(related_name='inhibitions', through='lideservices.ExtractionInhibition', to='lideservices.Extraction'),
        ),
        migrations.AlterField(
            model_name='reversetranscription',
            name='extraction',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='reverse_transcriptions', to='lideservices.Extraction'),
        ),
        migrations.AddField(
            model_name='extraction',
            name='extraction_method',
            field=models.OneToOneField(default='', on_delete=django.db.models.deletion.CASCADE, related_name='extractions', to='lideservices.ExtractionMethod'),
            preserve_default=False,
        ),
    ]