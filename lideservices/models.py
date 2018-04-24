from datetime import date
from django.db import models
from django.contrib.auth.models import User
from django.conf import settings
from simple_history.models import HistoricalRecords


# Users will be stored in the core User model instead of a custom model.
# Default fields of the core User model: username, first_name, last_name, email, password, groups, user_permissions,
# is_staff, is_active, is_superuser, last_login, date_joined
# For more information, see: https://docs.djangoproject.com/en/1.11/ref/contrib/auth/#user


######
#
#  Abstract Base Classes
#
######


class HistoryModel(models.Model):
    """
    An abstract base class model to track creation, modification, and data change history.
    """

    created_date = models.DateField(default=date.today, null=True, blank=True, db_index=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, db_index=True,
                                   related_name='%(class)s_creator')
    modified_date = models.DateField(auto_now=True, null=True, blank=True)
    modified_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, db_index=True,
                                    related_name='%(class)s_modifier')
    history = HistoricalRecords()

    class Meta:
        abstract = True
        default_permissions = ('add', 'change', 'delete', 'view')


class NameModel(HistoryModel):
    """
    An abstract base class model for the common name field.
    """

    name = models.CharField(max_length=128, unique=True)

    class Meta:
        abstract = True


######
#
#  Samples
#
######


class Sample(HistoryModel):
    """
    Sample
    """

    sample_type = models.ForeignKey('SampleType', related_name='samples')
    matrix = models.ForeignKey('Matrix', related_name='samples')
    filter_type = models.ForeignKey('FilterType', null=True, related_name='samples')
    study = models.ForeignKey('Study', related_name='samples')
    study_site_name = models.CharField(max_length=128, blank=True)
    collaborator_sample_id = models.CharField(max_length=128, unique=True)
    sampler_name = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, related_name='sampler_name') # TODO: this probably should be free text, holding external (non-staff) names
    sample_notes = models.TextField(blank=True, default='')
    sample_description = models.TextField(blank=True)
    arrival_date = models.DateField(null=True, blank=True)
    arrival_notes = models.TextField(blank=True, default='')
    collection_start_date = models.DateField()
    collection_start_time = models.TimeField(null=True, blank=True)
    collection_end_date = models.DateField(null=True, blank=True)
    collection_end_time = models.TimeField(null=True, blank=True)
    meter_reading_initial = models.FloatField(null=True, blank=True)
    meter_reading_final = models.FloatField(null=True, blank=True)
    meter_reading_unit = models.ForeignKey('Unit', null=True, related_name='samples_meter_units')
    total_volume_sampled_initial = models.FloatField(null=True, blank=True)
    total_volume_sampled_unit_initial = models.ForeignKey('Unit', null=True, related_name='samples_tvs_units')
    total_volume_or_mass_sampled = models.FloatField()
    sample_volume_initial = models.FloatField(null=True, blank=True) # TODO: delete this superfluous field?
    sample_volume_filtered = models.FloatField(null=True, blank=True) # TODO: delete this superfluous field?
    filter_born_on_date = models.DateField(null=True, blank=True)
    filter_flag = models.BooleanField(default=False)
    secondary_concentration_flag = models.BooleanField(default=False)
    elution_notes = models.TextField(blank=True, default='')
    technician_initials = models.CharField(max_length=128, blank=True)
    dissolution_volume = models.FloatField(null=True, blank=True)
    post_dilution_volume = models.FloatField(null=True, blank=True)
    analysisbatches = models.ManyToManyField('AnalysisBatch', through='SampleAnalysisBatch',
                                             related_name='sampleanalysisbatches')
    samplegroups = models.ManyToManyField('SampleGroup', through='SampleSampleGroup', related_name='samples')
    peg_neg = models.ForeignKey('self', null=True, related_name='samples')
    record_type = models.ForeignKey('RecordType', default=1)

    def __str__(self):
        return str(self.id)

    class Meta:
        db_table = "lide_sample"


class Aliquot(HistoryModel):
    """
    Aliquot
    """

    def _concat_ids(self):
        """Returns the concatenated parent ID and child series number of the record"""
        return '%s-%s' % (self.sample, self.aliquot_number)

    aliquot_string = property(_concat_ids)
    sample = models.ForeignKey('Sample', related_name='aliquots')
    freezer_location = models.ForeignKey('FreezerLocation', related_name='aliquot')
    aliquot_number = models.IntegerField()
    frozen = models.BooleanField(default=True)

    def __str__(self):
        return self.aliquot_string

    class Meta:
        db_table = "lide_aliquot"
        unique_together = ("sample", "aliquot_number")


class SampleType(NameModel):
    """
    Sample Type
    """

    code = models.CharField(max_length=128, unique=True)

    def __str__(self):
        return self.name

    class Meta:
        db_table = "lide_sampletype"


class Matrix(NameModel):
    """
    Matrix
    """

    code = models.CharField(max_length=128, unique=True)

    def __str__(self):
        return self.name

    class Meta:
        db_table = "lide_matrix"
        verbose_name_plural = "matrices"


class FilterType(NameModel):
    """
    Filter Type
    """

    matrix = models.ForeignKey('Matrix', related_name='filters')

    def __str__(self):
        return self.name

    class Meta:
        db_table = "lide_filtertype"


class Study(NameModel):
    """
    Study
    """

    description = models.TextField(blank=True)

    def __str__(self):
        return self.name

    class Meta:
        db_table = "lide_study"
        verbose_name_plural = "studies"


class Unit(NameModel):
    """
    Defined units of measurement for data values.
    """

    symbol = models.CharField(max_length=128, unique=True)
    description = models.TextField(blank=True)

    def __str__(self):
        return self.name

    class Meta:
        db_table = "lide_unit"


######
#
#  Freezer Locations
#
######


class FreezerLocation(HistoryModel):
    """
    Freezer Location
    """

    freezer = models.ForeignKey('Freezer', related_name='freezerlocations')
    rack = models.IntegerField()
    box = models.IntegerField()
    row = models.IntegerField()
    spot = models.IntegerField()

    def __str__(self):
        return str(self.id)

    class Meta:
        db_table = "lide_freezer_location"
        unique_together = ("freezer", "rack", "box", "row", "spot")


class Freezer(NameModel):
    """
    Freezer
    """

    racks = models.IntegerField()
    boxes = models.IntegerField()
    rows = models.IntegerField()
    spots = models.IntegerField()

    def __str__(self):
        return str(self.id)

    class Meta:
        db_table = "lide_freezer"


######
#
#  Concentrated Sample Volumes
#
######


class FinalConcentratedSampleVolume(HistoryModel):
    """
    Final Concentrated Sample Volume
    """

    sample = models.OneToOneField('Sample', related_name='final_concentrated_sample_volume')
    concentration_type = models.ForeignKey('ConcentrationType', related_name='final_concentrated_sample_volumes')
    final_concentrated_sample_volume = models.FloatField()
    notes = models.TextField(blank=True, default='')

    def __str__(self):
        return str(self.id)

    class Meta:
        db_table = "lide_finalconcentratedsamplevolume"


class ConcentrationType(NameModel):
    """
    Concentration Type
    """

    def __str__(self):
        return self.name

    class Meta:
        db_table = "lide_concentrationtype"


######
#
#  Sample Groups
#
######


class SampleSampleGroup(HistoryModel):
    """
    Table to allow many-to-many relationship between SampleGroups and Samples.
    """

    sample = models.ForeignKey('Sample')
    samplegroup = models.ForeignKey('SampleGroup')

    def __str__(self):
        return str(self.id)

    class Meta:
        db_table = "lide_samplesamplegroup"
        unique_together = ("sample", "samplegroup")


class SampleGroup(NameModel):
    """
    Terms or keywords used to describe, categorize, or group similar Samples for easier searching and reporting.
    """

    description = models.TextField(blank=True)

    def __str__(self):
        return self.name

    class Meta:
        db_table = "lide_samplegroup"


######
#
#  Analyses
#
######


class SampleAnalysisBatch(HistoryModel):
    """
    Table to allow many-to-many relationship between Samples and Analysis Batches.
    """

    sample = models.ForeignKey('Sample')
    analysis_batch = models.ForeignKey('AnalysisBatch')

    def __str__(self):
        return str(self.id)

    class Meta:
        db_table = "lide_sampleanalysisbatch"
        unique_together = ("sample", "analysis_batch")
        verbose_name_plural = "sampleanalysisbatches"


class AnalysisBatch(NameModel):
    """
    Analysis Batch
    """

    samples = models.ManyToManyField('Sample', through='SampleAnalysisBatch', related_name='sampleanalysisbatches')
    analysis_batch_description = models.CharField(max_length=128, blank=True)
    analysis_batch_notes = models.CharField(max_length=128, blank=True, default='')

    def __str__(self):
        return str(self.id)

    class Meta:
        db_table = "lide_analysisbatch"
        verbose_name_plural = "analysisbatches"


class AnalysisBatchTemplate(NameModel):
    """
    Analysis Batch Template
    """

    target = models.ForeignKey('Target', related_name='analysisbatchtemplates')
    description = models.TextField(blank=True)
    extraction_volume = models.FloatField()
    elution_volume = models.FloatField()

    def __str__(self):
        return self.name

    class Meta:
        db_table = "lide_analysisbatchtemplate"


######
#
#  Extractions
#
######


class ExtractionMethod(NameModel):
    """
    Extraction Method
    """

    def __str__(self):
        return self.name

    class Meta:
        db_table = "lide_extractionmethod"


class ExtractionBatch(HistoryModel):
    """
    Extraction Batch
    """

    def _concat_ids(self):
        """Returns the concatenated parent ID and child series number of the record"""
        return '%s-%s' % (self.analysis_batch, self.extraction_number)

    extraction_string = property(_concat_ids)
    analysis_batch = models.ForeignKey('AnalysisBatch', related_name='extractionbatches')
    extraction_method = models.ForeignKey('ExtractionMethod', related_name='extractionbatches')
    re_extraction = models.ForeignKey('self', null=True, related_name='extractionbatches')
    re_extraction_notes = models.TextField(blank=True, default='')
    extraction_number = models.IntegerField()
    extraction_volume = models.FloatField()
    extraction_date = models.DateField(default=date.today, db_index=True)
    pcr_date = models.DateField(default=date.today, db_index=True)
    qpcr_template_volume = models.FloatField(default=6)
    elution_volume = models.FloatField()
    sample_dilution_factor = models.IntegerField()
    qpcr_reaction_volume = models.FloatField(default=20)
    ext_pos_cq_value = models.FloatField(null=True, blank=True)
    ext_pos_gc_reaction = models.FloatField(null=True, blank=True)
    ext_pos_invalid = models.BooleanField(default=True)

    def __str__(self):
        return self.extraction_string

    class Meta:
        db_table = "lide_extractionbatch"
        unique_together = ("analysis_batch", "extraction_number", "re_extraction")
        verbose_name_plural = "extractionbatches"
        #  TODO: reassess extraction_number assignment logic for cases of re_extraction and re-use of extraction_number


class ReverseTranscription(HistoryModel):
    """
    Reverse Transcription
    """

    extraction_batch = models.ForeignKey('ExtractionBatch', related_name='reversetranscriptions')
    template_volume = models.FloatField()
    reaction_volume = models.FloatField()
    rt_date = models.DateField(default=date.today, null=True, blank=True, db_index=True)
    re_rt = models.ForeignKey('self', null=True, related_name='reversetranscriptions')
    re_rt_notes = models.TextField(blank=True, default='')
    rt_pos_cq_value = models.FloatField(null=True, blank=True)
    rt_pos_gc_reaction = models.FloatField(null=True, blank=True)
    rt_pos_invalid = models.BooleanField(default=True)

    def __str__(self):
        return str(self.id)

    class Meta:
        db_table = "lide_reversetranscription"
        unique_together = ("extraction_batch", "re_rt")


class SampleExtraction(HistoryModel):
    """
    Sample Extraction
    """

    sample = models.ForeignKey('Sample', related_name='sampleextractions')
    extraction_batch = models.ForeignKey('ExtractionBatch', related_name='sampleextractions')
    inhibition_dna = models.ForeignKey('Inhibition', null=True, related_name='sampleextractions_dna')
    inhibition_rna = models.ForeignKey('Inhibition', null=True, related_name='sampleextractions_rna')

    def __str__(self):
        return str(self.id)

    class Meta:
        db_table = "lide_sampleextraction"
        unique_together = ("sample", "extraction_batch")


class PCRReplicateBatch(HistoryModel):
    """
    Polymerase Chain Reaction Replicate Batch
    """

    extraction_batch = models.ForeignKey('ExtractionBatch', related_name='pcrreplicatebatches')
    target = models.ForeignKey('Target', related_name='pcrreplicatebatches')
    replicate_number = models.IntegerField()
    notes = models.TextField(blank=True, default='')
    ext_neg_cq_value = models.FloatField(null=True, blank=True)
    ext_neg_gc_reaction = models.FloatField(null=True, blank=True)
    ext_neg_invalid = models.BooleanField(default=True)
    rt_neg_cq_value = models.FloatField(null=True, blank=True)
    rt_neg_gc_reaction = models.FloatField(null=True, blank=True)
    rt_neg_invalid = models.BooleanField(default=True)
    pcr_neg_cq_value = models.FloatField(null=True, blank=True)
    pcr_neg_gc_reaction = models.FloatField(null=True, blank=True)
    pcr_neg_invalid = models.BooleanField(default=True)
    pcr_pos_cq_value = models.FloatField(null=True, blank=True)
    pcr_pos_gc_reaction = models.FloatField(null=True, blank=True)
    pcr_pos_invalid = models.BooleanField(default=True)
    re_pcr = models.ForeignKey('self', null=True, related_name='pcrreplicatebatches')

    def __str__(self):
        return str(self.id)

    class Meta:
        db_table = "lide_pcrreplicatebatch"
        unique_together = ("extraction_batch", "target", "replicate_number", "re_pcr")
        verbose_name_plural = "pcrreplicatebatches"


class PCRReplicate(HistoryModel):
    """
    Polymerase Chain Reaction Replicate
    """

    def _get_gc_reaction_sci(self):
        sci_val = self.gc_reaction
        if sci_val:
            sci_val = '{0: E}'.format(sci_val)
            sci_val = sci_val.split('E')[0].rstrip('0').rstrip('.') + 'E' + sci_val.split('E')[1]
        return sci_val

    def _get_replicate_concentration_sci(self):
        sci_val = self.replicate_concentration
        if sci_val:
            sci_val = '{0: E}'.format(sci_val)
            sci_val = sci_val.split('E')[0].rstrip('0').rstrip('.') + 'E' + sci_val.split('E')[1]
        return sci_val

    sample_extraction = models.ForeignKey('SampleExtraction', related_name='pcrreplicates')
    pcrreplicate_batch = models.ForeignKey('PCRReplicateBatch', related_name='pcrreplicates')
    cq_value = models.FloatField(null=True, blank=True)
    gc_reaction = models.DecimalField(max_digits=120, decimal_places=100, null=True, blank=True)
    gc_reaction_sci = property(_get_gc_reaction_sci)
    replicate_concentration = models.DecimalField(max_digits=120, decimal_places=100, null=True, blank=True)
    replicate_concentration_sci = property(_get_replicate_concentration_sci)
    concentration_unit = models.ForeignKey('Unit', related_name='pcrreplicates')
    invalid = models.BooleanField(default=True)
    invalid_override = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, related_name='pcrreplicates')

    # override the save method to update enter the correct (and required) concentration unit value
    def save(self, *args, **kwargs):
        self.concentration_unit = self.get_conc_unit(self.sample_extraction.sample.id)
        super(PCRReplicate, self).save(*args, **kwargs)

    # get the concentration_unit
    def get_conc_unit(self, sample_id):
        sample = Sample.objects.get(id=sample_id)
        if sample.matrix in ['forage_sediment_soil', 'solid_manure']:
            conc_unit = Unit.objects.get(name='gram')
        else:
            conc_unit = Unit.objects.get(name='Liter')
        return conc_unit

    # Calculate replicate_concentration
    def calc_rep_conc(self):
        if self.gc_reaction is not None:
            nucleic_acid_type = self.pcrreplicate_batch.target.nucleic_acid_type
            extr = self.sample_extraction
            eb = self.sample_extraction.extraction_batch
            sample = self.sample_extraction.sample
            # TODO: ensure that all necessary values are not null (more than just the following line)
            if None in (eb.qpcr_reaction_volume, eb.qpcr_template_volume, eb.elution_volume, eb.extraction_volume,
                        eb.sample_dilution_factor):
                # escape the whole process and notify user of missing data that is required
                pass
            # first apply the universal expressions
            prelim_value = (self.gc_reaction / eb.qpcr_reaction_volume) * (
                    eb.qpcr_reaction_volume / eb.qpcr_template_volume) * (
                                   eb.elution_volume / eb.extraction_volume) * (
                               eb.sample_dilution_factor)
            if nucleic_acid_type == 'DNA':
                prelim_value = prelim_value * extr.inhibition_dna.dilution_factor
            # apply the RT the expression if applicable
            elif nucleic_acid_type == 'RNA':
                # assume that there can be only one RT per EB, except when there is a re_rt,
                # in which case the 'old' RT is no longer valid and would have a RT ID value in the re_rt field
                # that references the only valid RT;
                # in other words, the re_rt value must be null for the record to be valid
                rt = ReverseTranscription.objects.filter(extraction_batch=eb, re_rt=None)
                dl = extr.inhibition_rna.dilution_factor
                prelim_value = prelim_value * dl * (rt.reaction_volume / rt.template_volume)
            # then apply the final volume-or-mass ratio expression (note: liquid_manure does not use this)
            if sample.matrix in ['forage_sediment_soil', 'water', 'wastewater']:
                fcsv = FinalConcentratedSampleVolume.objects.get(sample=sample.id)
                prelim_value = prelim_value * (
                        fcsv.final_concentrated_sample_volume / sample.total_volume_or_mass_sampled)
            elif sample.matrix == 'air':
                prelim_value = prelim_value * (sample.dissolution_volume / sample.total_volume_or_mass_sampled)
            elif sample.matrix == 'solid_manure':
                prelim_value = prelim_value * (sample.post_dilution_volume / sample.total_volume_or_mass_sampled)
            # finally, apply the unit-cancelling expression
            if sample.matrix in ['air', 'forage_sediment_soil', 'water', 'wastewater']:
                # 1,000 microliters per 1 milliliter
                final_value = prelim_value * 1000
            elif sample.matrix == 'liquid_manure':
                # 1,000,000 microliters per 1 liter
                final_value = prelim_value * 1000000
            else:
                # solid manure
                final_value = prelim_value
            return final_value
        else:
            return None

    def __str__(self):
        return str(self.id)

    class Meta:
        db_table = "lide_pcrreplicate"
        unique_together = ("sample_extraction", "pcrreplicate_batch")


class Result(HistoryModel):
    """
    Result
    """

    def _get_sample_mean_concentration_sci(self):
        sci_val = self.sample_mean_concentration
        if sci_val:
            sci_val = '{0: E}'.format(sci_val)
            sci_val = sci_val.split('E')[0].rstrip('0').rstrip('.') + 'E' + sci_val.split('E')[1]
        return sci_val

    sample_mean_concentration = models.DecimalField(max_digits=120, decimal_places=100, null=True, blank=True)
    sample_mean_concentration_sci = property(_get_sample_mean_concentration_sci)
    sample = models.ForeignKey('Sample', related_name='results')
    target = models.ForeignKey('Target', related_name='results')

    # Determine if all valid replicates for a given sample-target combo are now in the database or not
    def all_sample_target_reps_uploaded(self):
        valid_reps_with_null_cq_value = []
        exts = SampleExtraction.objects.filter(sample=self.sample)
        for ext in exts:
            reps = PCRReplicate.objects.filter(extraction=ext.id, pcrreplicate_batch__target__exact=self.target)
            for rep in reps:
                if rep.cq_value is None and rep.invalid is False:
                    valid_reps_with_null_cq_value.append(rep.id)
        return True if len(valid_reps_with_null_cq_value) == 0 else False

    # Calculate sample mean concentration for all samples whose target replicates are now in the database
    def calc_sample_mean_conc(self):
        reps_count = 0
        pos_gc_reactions = []
        exts = SampleExtraction.objects.filter(sample=self.sample)
        for ext in exts:
            reps = PCRReplicate.objects.filter(extraction=ext.id, pcrreplicate_batch__target__exact=self.target)
            for rep in reps:
                if rep.gc_reaction >= 0 and rep.invalid is False:
                    reps_count = reps_count + 1
                    pos_gc_reactions.append(rep.gc_reaction)
        smc = sum(pos_gc_reactions) / reps_count if reps_count > 0 else 0
        self.sample_mean_concentration = smc
        self.save()

    def __str__(self):
        return str(self.id)

    class Meta:
        db_table = "lide_result"
        unique_together = ("sample", "target")


class StandardCurve(HistoryModel):
    """
    Standard Curve
    """

    r_value = models.FloatField(null=True, blank=True)
    slope = models.FloatField(null=True, blank=True)
    efficiency = models.FloatField(null=True, blank=True)
    pos_ctrl_cq = models.FloatField(null=True, blank=True)
    pos_ctrl_cq_range = models.FloatField(null=True, blank=True)
    # QUESTION: should there be an active or inactive/superseded field?

    def __str__(self):
        return str(self.id)

    class Meta:
        db_table = "lide_standardcurve"


class Inhibition(HistoryModel):
    """
    Inhibition
    """

    sample = models.ForeignKey('Sample', related_name='inhibitions')
    extraction_batch = models.ForeignKey('ExtractionBatch', related_name='inhibitions')
    inhibition_date = models.DateField(default=date.today, db_index=True)
    nucleic_acid_type = models.ForeignKey('NucleicAcidType', default=1)
    dilution_factor = models.IntegerField(null=True, blank=True)

    def __str__(self):
        return str(self.id)

    class Meta:
        db_table = "lide_inhibition"
        unique_together = ("sample", "extraction_batch", "nucleic_acid_type")


class Target(NameModel):
    """
    Target
    """

    code = models.CharField(max_length=128, unique=True)
    nucleic_acid_type = models.ForeignKey('NucleicAcidType', default=1)
    notes = models.TextField(blank=True, default='')

    def __str__(self):
        return self.name

    class Meta:
        db_table = "lide_target"


######
#
#  Misc
#
######


class FieldUnit(HistoryModel):
    """
    Defined units for particular fields
    """

    table = models.CharField(max_length=64)
    field = models.CharField(max_length=64)
    unit = models.ForeignKey('Unit', related_name='fieldunits')

    def __str__(self):
        return str(self.id)

    class Meta:
        db_table = "lide_fieldunit"


class NucleicAcidType(NameModel):
    """
    Nucleic Acid Type (DNA or RNA)
    """

    def __str__(self):
        return self.name

    class Meta:
        db_table = "lide_nucleicacidtype"


class RecordType(NameModel):
    """
    Record Type (DATA or CONTROL)
    """

    def __str__(self):
        return self.name

    class Meta:
        db_table = "lide_recordtype"


class OtherAnalysis(HistoryModel):
    """
    Other Analysis
    """

    description = models.TextField(blank=True)
    data = models.TextField(blank=True)

    def __str__(self):
        return str(self.id)

    class Meta:
        db_table = "lide_otheranalysis"
        verbose_name_plural = "otheranalyses"
