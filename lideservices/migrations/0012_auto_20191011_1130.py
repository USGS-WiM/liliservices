# Generated by Django 2.2 on 2019-10-11 11:30

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('lideservices', '0011_historicalreporttype_historicalstatus_reporttype_status'),
    ]

    operations = [
        migrations.AlterField(
            model_name='historicalreportfile',
            name='report_status',
            field=models.ForeignKey(blank=True, db_constraint=False, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='+', to='lideservices.Status'),
        ),
        migrations.AlterField(
            model_name='historicalreportfile',
            name='report_type',
            field=models.ForeignKey(blank=True, db_constraint=False, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='+', to='lideservices.ReportType'),
        ),
        migrations.AlterField(
            model_name='reportfile',
            name='report_status',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='reportfiles', to='lideservices.Status'),
        ),
        migrations.AlterField(
            model_name='reportfile',
            name='report_type',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='reportfiles', to='lideservices.ReportType'),
        ),
    ]
