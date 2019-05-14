# Generated by Django 2.2 on 2019-05-14 14:06

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('lideservices', '0006_auto_20190502_2031'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='finalsamplemeanconcentration',
            options={'ordering': ['sample', 'id']},
        ),
        migrations.RemoveField(
            model_name='analysisbatch',
            name='samples',
        ),
        migrations.AlterField(
            model_name='aliquot',
            name='freezer_location',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='aliquots', to='lideservices.FreezerLocation'),
        ),
        migrations.AlterField(
            model_name='filtertype',
            name='matrix',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='filtertypes', to='lideservices.Matrix'),
        ),
        migrations.AlterField(
            model_name='finalconcentratedsamplevolume',
            name='concentration_type',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='finalconcentratedsamplevolumes', to='lideservices.ConcentrationType'),
        ),
        migrations.AlterField(
            model_name='finalconcentratedsamplevolume',
            name='sample',
            field=models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='finalconcentratedsamplevolume', to='lideservices.Sample'),
        ),
        migrations.AlterField(
            model_name='finalsamplemeanconcentration',
            name='sample',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='finalsamplemeanconcentrations', to='lideservices.Sample'),
        ),
        migrations.AlterField(
            model_name='finalsamplemeanconcentration',
            name='target',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='finalsamplemeanconcentrations', to='lideservices.Target'),
        ),
        migrations.AlterField(
            model_name='sample',
            name='analysisbatches',
            field=models.ManyToManyField(related_name='samples', through='lideservices.SampleAnalysisBatch', to='lideservices.AnalysisBatch'),
        ),
        migrations.AlterField(
            model_name='sample',
            name='meter_reading_unit',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.PROTECT, related_name='samplesmeterunits', to='lideservices.Unit'),
        ),
        migrations.AlterField(
            model_name='sample',
            name='total_volume_sampled_unit_initial',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.PROTECT, related_name='samplestvsunits', to='lideservices.Unit'),
        ),
        migrations.AlterField(
            model_name='sampleextraction',
            name='inhibition_dna',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='sampleextractionsdna', to='lideservices.Inhibition'),
        ),
        migrations.AlterField(
            model_name='sampleextraction',
            name='inhibition_rna',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='sampleextractionsrna', to='lideservices.Inhibition'),
        ),
    ]
