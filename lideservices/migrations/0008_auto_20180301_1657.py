# -*- coding: utf-8 -*-
# Generated by Django 1.11.2 on 2018-03-01 16:57
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('lideservices', '0007_auto_20180228_1149'),
    ]

    operations = [
        migrations.RenameField(
            model_name='extractionbatch',
            old_name='reextraction_note',
            new_name='reextraction_notes',
        ),
        migrations.RenameField(
            model_name='pcrreplicatebatch',
            old_name='note',
            new_name='notes',
        ),
        migrations.RenameField(
            model_name='reversetranscription',
            old_name='re_rt_note',
            new_name='re_rt_notes',
        ),
        migrations.AddField(
            model_name='pcrreplicatebatch',
            name='re_pcr',
            field=models.BooleanField(default=False),
        ),
        migrations.RemoveField(
            model_name='pcrreplicate',
            name='re_pcr',
        ),
    ]