from datetime import date
from django.db import models
from django.contrib.auth.models import User
from django.conf import settings
from simple_history.models import HistoricalRecords
from simple_history.admin import SimpleHistoryAdmin


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


#TODO: assign proper field types and properties to each model field

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
    filter_type = models.ForeignKey('FilterType', related_name='samples')
    study = models.ForeignKey('Study', related_name='samples')
    study_site_name = models.CharField(max_length=128, null=True, blank=True)  # COMMENT: I don't like this. Location information should be kept in a dedicated table for possible future use in spatial analysis
    collaborator_sample_id = models.CharField(max_length=128, unique=True)
    sampler_name = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='sampler_name', null=True, blank=True)
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
    meter_reading_unit = models.ForeignKey('UnitType', null=True, related_name='samples_meter_units')  # COMMENT: this field doesn't belong here, it should go in a related table dedicated to this matrix type
    total_volume_sampled_initial = models.FloatField(null=True, blank=True)
    total_volume_sampled_unit_initial = models.ForeignKey('UnitType', null=True, related_name='samples_tvs_units')
    total_volume_sampled = models.FloatField(null=True, blank=True)
    sample_volume_initial = models.FloatField(null=True, blank=True)
    sample_volume_filtered = models.FloatField(null=True, blank=True)
    filter_born_on_date = models.DateField(null=True, blank=True)  # COMMENT: Are these throw-away filters? Or do they need/want to keep track of them for later analysis? If the latter, it would need a dedicated table, yes?
    filter_flag = models.BooleanField(default=False)
    secondary_concentration_flag = models.BooleanField(default=False)
    elution_date = models.DateField(null=True, blank=True)  # COMMENT: this field probably doesn't belong here, it should go in a related table dedicated to this matrix type
    elution_notes = models.TextField(blank=True)  # COMMENT: this field probably doesn't belong here, it should go in a related table dedicated to this matrix type
    technician_initials = models.CharField(max_length=4, null=True, blank=True)  # COMMENT: this field could be replaced by the created_by/edited_by fields
    air_subsample_volume = models.FloatField(null=True, blank=True)  # COMMENT: this field probably doesn't belong here, it should go in a related table dedicated to this matrix type
    post_dilution_volume = models.FloatField(null=True, blank=True)  # COMMENT: this field probably doesn't belong here, it should go in a related table dedicated to this matrix type
    pump_flow_rate = models.FloatField(null=True, blank=True)  # COMMENT: this field probably doesn't belong here, it should go in a related table dedicated to this matrix type
    analysisbatches = models.ManyToManyField('AnalysisBatch', through='SampleAnalysisBatch',
                                             related_name='sampleanalysisbatches')

    def __str__(self):
        return str(self.id)

    class Meta:
        db_table = "lide_sample"
        #TODO: 'unique together' fields


class SampleType(NameModel):
    """
    Sample Type
    """

    code = models.CharField(max_length=128, unique=True)

    def __str__(self):
        return str(self.id)

    class Meta:
        db_table = "lide_sampletype"


class MatrixType(NameModel):
    """
    Matrix Type
    """

    code = models.CharField(max_length=128, unique=True)

    def __str__(self):
        return str(self.id)

    class Meta:
        db_table = "lide_matrixtype"


class FilterType(NameModel):
    """
    Filter Type
    """

    matrix = models.ForeignKey('MatrixType', related_name='filters')

    def __str__(self):
        return str(self.id)

    class Meta:
        db_table = "lide_filtertype"


class Study(NameModel):
    """
    Study
    """

    description = models.TextField(blank=True)

    def __str__(self):
        return str(self.id)

    class Meta:
        db_table = "lide_study"


class UnitType(models.Model):
    """Defined units of measurement for data values."""

    unit = models.CharField(max_length=128, unique=True)
    description = models.TextField(blank=True)

    def __str__(self):
        return str(self.id)

    class Meta:
        db_table = "lide_unittype"


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

    some_field = models.CharField(max_length=128, null=True, blank=True) #Temporary placeholder until further details are known.
    samples = models.ManyToManyField('Sample', through='SampleAnalysisBatch', related_name='sampleanalysisbatches')

    def __str__(self):
        return str(self.id)

    class Meta:
        db_table = "lide_analysisbatch"
        #TODO: 'unique together' fields


class Extraction(HistoryModel):
    """
    Extraction
    """

    sample = models.ForeignKey('Sample', related_name='extractions')
    analysis_batch = models.ForeignKey('AnalysisBatch', related_name='extractions')
    extraction_number = models.IntegerField(unique=True)
    inhibition = models.ManyToManyField('Inhibition', through='ExtractionInhibition',
                                        related_name='extractioninhibitions')

    def __str__(self):
        return str(self.id)

    class Meta:
        db_table = "lide_extraction"
        unique_together = ("sample", "extraction_number")


class ExtractionInhibition(HistoryModel):
    """
    Table to allow many-to-many relationship between Extractions and Inhibitions.
    """

    extraction = models.ForeignKey('Extraction')
    inhibition = models.ForeignKey('Inhibition')

    def __str__(self):
        return str(self.id)

    class Meta:
        db_table = "lide_extractioninhibition"
        unique_together = ("extraction", "inhibition")


class Inhibition(NameModel):
    """
    Inhibition
    """

    type = models.CharField(max_length=128, null=True, blank=True)  # COMMENT: this should be a controlled list, either an enum field or a FK to a type table
    dilution = models.FloatField(null=True, blank=True)
    extraction = models.ManyToManyField('Extraction', through='ExtractionInhibition',
                                        related_name='extractioninhibitions')

    def __str__(self):
        return str(self.id)

    class Meta:
        db_table = "lide_inhibition"


class ReverseTranscription(NameModel):
    """
    Reverse Transcription
    """

    extraction = models.ForeignKey('Extraction', related_name='reversetranscriptions')
    volume_in = models.FloatField(null=True, blank=True)
    volume_out = models.FloatField(null=True, blank=True)
    cycle_of_quantification = models.FloatField(null=True, blank=True)

    def __str__(self):
        return str(self.id)

    class Meta:
        db_table = "lide_reversetranscription"


class PCRReplicate(HistoryModel):
    """
    Polymerase Chain Reaction Replicate
    """

    extraction = models.ForeignKey('Extraction', related_name='pcrreplicates')
    inhibition =  models.ForeignKey('Inhibition', related_name='pcrreplicates')
    reverse_transcription = models.ForeignKey('ReverseTranscription', related_name='pcrreplicates')
    target = models.ForeignKey('Target', related_name='pcrreplicates')
    replicate = models.IntegerField()
    cycle_of_quantification = models.FloatField(null=True, blank=True)
    guanine_cytosine_content_reaction = models.FloatField(null=True, blank=True)
    concentration = models.FloatField(null=True, blank=True)
    #sample_mean_concentration = models.FloatField(null=True, blank=True) #QUESTION: does this belong here? seems like a "mean" value should be above (i.e., the one in 1:N) the table of the values producing the mean.
    concentration_unit = models.ForeignKey('UnitType', null=True, related_name='pcr_replicates')

    def __str__(self):
        return str(self.id)

    class Meta:
        db_table = "lide_pcrreplicate"
        #TODO: 'unique together' fields


class StandardCurve(HistoryModel):
    """
    Standard Curve
    """

    r_value = models.FloatField(null=True, blank=True)
    slope = models.FloatField(null=True, blank=True)
    efficiency = models.FloatField(null=True, blank=True)

    def __str__(self):
        return str(self.id)

    class Meta:
        db_table = "lide_standardcurve"


class Target(HistoryModel):
    """
    Target
    """

    abbreviation = models.CharField(max_length=128, null=True, blank=True)
    type = models.CharField(max_length=128, null=True, blank=True) #COMMENT: this should be a controlled list, either an enum field or a FK to a type table

    def __str__(self):
        return str(self.id)

    class Meta:
        db_table = "lide_target"


######
#
#  Controls
#
######
#QUESTION: for completeness/explicitness sake, should these be named "Quality Controls" instead?


class ControlType(NameModel):
    """
    Control Type
    """

    abbreviation = models.CharField(max_length=128, null=True, blank=True)

    def __str__(self):
        return str(self.id)

    class Meta:
        db_table = "lide_controltype"


class Control(NameModel):
    """
    Control
    """

    type = models.ForeignKey('ControlType', related_name='controls')
    sample = models.ForeignKey('Sample', related_name='controls')
    target = models.ForeignKey('Target', related_name='controls')
    qc_value = models.FloatField(null=True, blank=True)
    qc_flag = models.BooleanField(default=False)

    def __str__(self):
        return str(self.id)

    class Meta:
        db_table = "lide_control"
        #TODO: 'unique together' fields


######
#
#  Misc
#
######


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

