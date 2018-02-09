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


# TODO: assign proper field types and properties to each model field

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
    matrix_type = models.ForeignKey('MatrixType', related_name='samples')
    filter_type = models.ForeignKey('FilterType', null=True, related_name='samples')
    study = models.ForeignKey('Study', related_name='samples')
    study_site_name = models.CharField(max_length=128, null=True, blank=True)  # COMMENT: I don't like this. Location information should be kept in a dedicated table for possible future use in spatial analysis
    collaborator_sample_id = models.CharField(max_length=128, unique=True)
    sampler_name = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, related_name='sampler_name')  # QUESTION: This should probably be required, yes?
    sample_notes = models.TextField(blank=True)
    sample_description = models.TextField(blank=True)
    arrival_date = models.DateField(null=True, blank=True)
    arrival_notes = models.TextField(blank=True)
    collection_start_date = models.DateField(null=True, blank=True)
    collection_start_time = models.TimeField(null=True, blank=True)
    collection_end_date = models.DateField(null=True, blank=True)
    collection_end_time = models.TimeField(null=True, blank=True)
    meter_reading_initial = models.FloatField(null=True, blank=True)  # COMMENT: this field probably doesn't belong here, it should go in a related table dedicated to this matrix type
    meter_reading_final = models.FloatField(null=True, blank=True)  # COMMENT: this field probably doesn't belong here, it should go in a related table dedicated to this matrix type
    meter_reading_unit = models.ForeignKey('Unit', null=True, related_name='samples_meter_units')  # QUESTION: This should probably be required, yes?  # COMMENT: this field doesn't belong here, it should go in a related table dedicated to this matrix type
    total_volume_sampled_initial = models.FloatField(null=True, blank=True)
    total_volume_sampled_unit_initial = models.ForeignKey('Unit', null=True, related_name='samples_tvs_units')  # QUESTION: This should probably be required, yes?
    total_volume_or_mass_sampled = models.FloatField(null=True, blank=True)
    sample_volume_initial = models.FloatField(null=True, blank=True)
    sample_volume_filtered = models.FloatField(null=True, blank=True)
    filter_born_on_date = models.DateField(null=True, blank=True)  # COMMENT: Are these throw-away filters? Or do they need/want to keep track of them for later analysis? If the latter, it would need a dedicated table, yes?
    filter_flag = models.BooleanField(default=False)
    secondary_concentration_flag = models.BooleanField(default=False)
    elution_notes = models.TextField(blank=True)  # COMMENT: this field probably doesn't belong here, it should go in a related table dedicated to this matrix type
    technician_initials = models.CharField(max_length=4, null=True, blank=True)  # COMMENT: this field could be replaced by the created_by/edited_by fields
    dissolution_volume = models.FloatField(null=True, blank=True)  # COMMENT: this field probably doesn't belong here, it should go in a related table dedicated to this matrix type
    post_dilution_volume = models.FloatField(null=True, blank=True)  # COMMENT: this field probably doesn't belong here, it should go in a related table dedicated to this matrix type
    analysisbatches = models.ManyToManyField('AnalysisBatch', through='SampleAnalysisBatch',
                                             related_name='sampleanalysisbatches')
    samplegroups = models.ManyToManyField('SampleGroup', through='SampleSampleGroup', related_name='samples')
    peg_neg = models.ForeignKey('self', null=True, related_name='samples')
    record_type = models.ForeignKey('RecordType', default=1)

    def __str__(self):
        return str(self.id)

    class Meta:
        db_table = "lide_sample"
        # TODO: 'unique together' fields


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
    aliquot_number = models.IntegerField(null=True)
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


class MatrixType(NameModel):
    """
    Matrix Type
    """

    code = models.CharField(max_length=128, unique=True)

    def __str__(self):
        return self.name

    class Meta:
        db_table = "lide_matrixtype"


class FilterType(NameModel):
    """
    Filter Type
    """

    matrix = models.ForeignKey('MatrixType', related_name='filters')

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


class Unit(NameModel):
    """
    Defined units of measurement for data values.
    """

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
        # QUESTION: should there be unique freezer locations?


class Freezer(HistoryModel):
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
    final_concentrated_sample_volume = models.FloatField(null=True, blank=True)
    final_concentrated_sample_volume_notes = models.TextField(blank=True)

    def __str__(self):
        return str(self.id)

    class Meta:
        db_table = "lide_finalconcentratedsamplevolume"
        # QUESTION: should there be unique final concentrated sample volumes?


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


class AnalysisBatch(HistoryModel):
    """
    Analysis Batch
    """

    samples = models.ManyToManyField('Sample', through='SampleAnalysisBatch', related_name='sampleanalysisbatches')
    analysis_batch_description = models.CharField(max_length=128, null=True, blank=True)
    analysis_batch_notes = models.CharField(max_length=128, null=True, blank=True)

    def __str__(self):
        return str(self.id)

    class Meta:
        db_table = "lide_analysisbatch"


class AnalysisBatchTemplate(NameModel):
    """
    Analysis Batch Template
    """

    target = models.ForeignKey('Target', related_name='analysisbatchtemplates')
    description = models.TextField(blank=True)
    extraction_volume = models.FloatField(null=True, blank=True)
    elution_volume = models.FloatField(null=True, blank=True)

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
    reextraction = models.ForeignKey('self', null=True, related_name='extractionbatches')
    reextraction_note = models.CharField(max_length=255, null=True, blank=True)
    extraction_number = models.IntegerField()
    extraction_volume = models.FloatField(null=True, blank=True)
    extraction_date = models.DateField(default=date.today, null=True, blank=True, db_index=True)
    pcr_date = models.DateField(default=date.today, null=True, blank=True, db_index=True)
    template_volume = models.FloatField(null=True, blank=True)
    elution_volume = models.FloatField(null=True, blank=True)
    sample_dilution_factor = models.IntegerField(null=True, blank=True)
    reaction_volume = models.FloatField(null=True, blank=True)
    ext_pos_cq_value = models.FloatField(null=True, blank=True)
    ext_pos_gc_reaction = models.FloatField(null=True, blank=True)
    ext_pos_bad_result_flag = models.BooleanField(default=False)

    def __str__(self):
        return self.extraction_string

    class Meta:
        db_table = "lide_extractionbatch"
        unique_together = ("analysis_batch", "extraction_number")


class ReverseTranscription(HistoryModel):
    """
    Reverse Transcription
    """

    extraction_batch = models.ForeignKey('ExtractionBatch', related_name='reversetranscriptions')
    template_volume = models.FloatField(null=True, blank=True)
    reaction_volume = models.FloatField(null=True, blank=True)
    rt_date = models.DateField(default=date.today, null=True, blank=True, db_index=True)
    re_rt = models.ForeignKey('self', null=True, related_name='reversetranscriptions')
    re_rt_note = models.CharField(max_length=255, null=True, blank=True)
    rt_pos_cq_value = models.FloatField(null=True, blank=True)
    rt_pos_gc_reaction = models.FloatField(null=True, blank=True)
    rt_pos_bad_result_flag = models.BooleanField(default=False)

    def __str__(self):
        return str(self.id)

    class Meta:
        db_table = "lide_reversetranscription"
        unique_together = ("extraction_batch", "re_rt")


class Extraction(HistoryModel):
    """
    Extraction
    """

    sample = models.ForeignKey('Sample', related_name='extractions')
    extraction_batch = models.ForeignKey('ExtractionBatch', related_name='extractions')
    inhibition_dna = models.ForeignKey('Inhibition', null=True, related_name='extractions_dna')
    inhibition_rna = models.ForeignKey('Inhibition', null=True, related_name='extractions_rna')

    def __str__(self):
        return str(self.id)

    class Meta:
        db_table = "lide_extraction"
        unique_together = ("sample", "extraction_batch")


class PCRReplicateBatch(HistoryModel):
    """
    Polymerase Chain Reaction Replicate Batch
    """

    extraction_batch = models.ForeignKey('ExtractionBatch', related_name='pcrreplicatebatches')
    target = models.ForeignKey('Target', related_name='pcrreplicatebatches')
    replicate_number = models.FloatField(null=True, blank=True)
    note = models.TextField(blank=True)
    ext_neg_cq_value = models.FloatField(null=True, blank=True)
    ext_neg_gc_reaction = models.FloatField(null=True, blank=True)
    ext_neg_bad_result_flag = models.BooleanField(default=False)
    rt_neg_cq_value = models.FloatField(null=True, blank=True)
    rt_neg_gc_reaction = models.FloatField(null=True, blank=True)
    rt_neg_bad_result_flag = models.BooleanField(default=False)
    pcr_neg_cq_value = models.FloatField(null=True, blank=True)
    pcr_neg_gc_reaction = models.FloatField(null=True, blank=True)
    pcr_neg_bad_result_flag = models.BooleanField(default=False)
    pcr_pos_cq_value = models.FloatField(null=True, blank=True)
    pcr_pos_gc_reaction = models.FloatField(null=True, blank=True)
    pcr_pos_bad_result_flag = models.BooleanField(default=False)

    def __str__(self):
        return str(self.id)

    class Meta:
        db_table = "lide_pcrreplicatebatch"
        unique_together = ("extraction_batch", "target", "replicate_number")


class PCRReplicate(HistoryModel):
    """
    Polymerase Chain Reaction Replicate
    """

    extraction = models.ForeignKey('Extraction', related_name='pcrreplicates')
    pcrreplicate_batch = models.ForeignKey('PCRReplicateBatch', related_name='pcrreplicates')
    cq_value = models.FloatField(null=True, blank=True)
    gc_reaction = models.FloatField(null=True, blank=True)
    replicate_concentration = models.FloatField(null=True, blank=True)
    concentration_unit = models.ForeignKey('Unit', null=True, related_name='pcrreplicates')  # QUESTION: This should probably be required, yes?
    bad_result_flag = models.BooleanField(default=False)
    re_pcr = models.BooleanField(default=False)

    def __str__(self):
        return str(self.id)

    class Meta:
        db_table = "lide_pcrreplicate"
        unique_together = ("extraction", "pcrreplicate_batch")


class Result(HistoryModel):
    """
    Result
    """

    sample_mean_concentration = models.FloatField(null=True, blank=True)
    sample = models.ForeignKey('Sample', related_name='results')
    target = models.ForeignKey('Target', related_name='results')

    def __str__(self):
        return str(self.id)

    class Meta:
        db_table = "lide_result"
        # QUESTION: should sample and target be unique_together?


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
    inhibition_date = models.DateField(default=date.today, null=True, blank=True, db_index=True)
    nucleic_acid_type = models.ForeignKey('NucleicAcidType', default=1)
    dilution_factor = models.IntegerField(null=True, blank=True)

    def __str__(self):
        return str(self.id)

    class Meta:
        db_table = "lide_inhibition"
        # QUESTION: can there be more than one inhibition per EB? if so, we should probably have an inhibition_number field to ensure uniqueness among inhibitions within one EB


class Target(NameModel):
    """
    Target
    """

    code = models.CharField(max_length=128, null=True, blank=True)
    nucleic_acid_type = models.ForeignKey('NucleicAcidType', default=1)
    notes = models.CharField(max_length=128, null=True, blank=True)

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
