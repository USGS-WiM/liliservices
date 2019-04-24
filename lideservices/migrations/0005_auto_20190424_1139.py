# Generated by Django 2.2 on 2019-04-24 11:39

import django.core.validators
from django.db import migrations
import lideservices.models


class Migration(migrations.Migration):

    dependencies = [
        ('lideservices', '0004_historicalaliquot_historicalanalysisbatch_historicalanalysisbatchtemplate_historicalconcentrationtyp'),
    ]

    operations = [
        migrations.AddField(
            model_name='historicalinhibition',
            name='cq_value',
            field=lideservices.models.NullableNonnegativeDecimalField2010(blank=True, decimal_places=10, max_digits=20, null=True, validators=[django.core.validators.MinValueValidator(0)]),
        ),
        migrations.AddField(
            model_name='inhibition',
            name='cq_value',
            field=lideservices.models.NullableNonnegativeDecimalField2010(blank=True, decimal_places=10, max_digits=20, null=True, validators=[django.core.validators.MinValueValidator(0)]),
        ),
    ]
