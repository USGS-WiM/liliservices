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
    sample_environment = models.ForeignKey('SampleEnvironment', related_name='samples')
    sample_location = models.ForeignKey('SampleLocation', related_name='samples')
    water_type = models.ForeignKey('WaterType', related_name='samples')
    filter_type = models.ForeignKey('FilterType', related_name='samples')
    study = models.ForeignKey('Study', related_name='samples')
    study_site_name = models.CharField(max_length=128, null=True, blank=True) #QUESTION: shouldn't this be in its own table ("StudySite") and just related here with a foreign key?
    study_site_id = models.IntegerField() #QUESTION: shouldn't this be in its own table ("StudySite") and just related here with a foreign key?
    collaborator_sample_id = models.IntegerField(unique=True)
    sampler_name = models.CharField(max_length=128, null=True, blank=True) #QUESTION: shouldn't this be in its own table ("Sampler" or "Person") and just related here with a foreign key?
    notes = models.TextField(blank=True)
    description = models.TextField(blank=True)
    collect_start_date = models.DateField(null=True, blank=True)
    collect_start_time = models.TimeField(null=True, blank=True)
    collect_end_date = models.DateField(null=True, blank=True)
    collect_end_time = models.TimeField(null=True, blank=True)
    meter_reading_initial = models.FloatField(null=True, blank=True)
    meter_reading_final = models.FloatField(null=True, blank=True)
    meter_reading_unit = models.CharField(max_length=128, null=True, blank=True) #QUESTION: shouldn't this be in its own table ("Unit") and just related here with a foreign key?
    total_volume_sampled_initial = models.FloatField(null=True, blank=True)
    total_volume_sampled_unit_initial = models.CharField(max_length=128, null=True, blank=True) #QUESTION: shouldn't this be in it's own table ("Unit") and just related here with a foreign key?
    total_volume_sampled = models.FloatField(null=True, blank=True)
    total_volume_sampled_stage = models.FloatField(null=True, blank=True) #QUESTION: Shouldn't this reside solely in the application code, and not in the DB? 
    total_volume_sampled_calculation = models.FloatField(null=True, blank=True) #QUESTION: Shouldn't this reside solely in the application code, and not in the DB? 
    total_volume_sampled_stage_calculation = models.FloatField(null=True, blank=True) #QUESTION: Shouldn't this reside solely in the application code, and not in the DB? 
    filtered_volume = models.FloatField(null=True, blank=True)
    filter_born_on_date = models.DateField(null=True, blank=True) #QUESTION: is this just the filter's create date?
    matrix = models.CharField(max_length=128, null=True, blank=True) #QUESTION: why is this here and in Filter Type? Shouldn't this be in it's own table ("Matrix") and just related here with a foreign key?
    filter_flag = models.BooleanField(default=False) #QUESTION: what is the purpose of this flag? Shouldn't it be a control?
    secondary_concentration_flag = models.BooleanField(default=False) #QUESTION: what is the purpose of this flag? Shouldn't it be a control?
    analysisbatches = models.ManyToManyField('AnalysisBatch', through='SampleAnalysisBatch', related_name='sampleanalysisbatches')

    def __str__(self):
        return str(self.id)

    class Meta:
        db_table = "lide_sample"
        #TODO: 'unique together' fields


class SampleType(NameModel):
    """
    Sample Type
    """

    def __str__(self):
        return str(self.id)

    class Meta:
        db_table = "lide_sampletype"


class SampleEnvironment(NameModel):
    """
    Sample Environment
    """

    def __str__(self):
        return str(self.id)

    class Meta:
        db_table = "lide_sampleenvironment"


class SampleLocation(NameModel):
    """
    Sample Location
    """

    def __str__(self):
        return str(self.id)

    class Meta:
        db_table = "lide_samplelocation"


class FilterType(NameModel):
    """
    Filter Type
    """

    matrix = models.CharField(max_length=128, null=True, blank=True)

    def __str__(self):
        return str(self.id)

    class Meta:
        db_table = "lide_filtertype"


class WaterType(NameModel):
    """
    Water Type
    """

    def __str__(self):
        return str(self.id)

    class Meta:
        db_table = "lide_watertype"


class Study(NameModel):
    """
    Study
    """

    description = models.TextField(blank=True)

    def __str__(self):
        return str(self.id)

    class Meta:
        db_table = "lide_study"


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

    #QUESTION: shouldn't this relate directly to sample, since an extract comes from a sample?
    analysis_batch = models.ForeignKey('AnalysisBatch', related_name='extractions')
    extraction_code = models.IntegerField(unique=True) #QUESTION: how will this be determined/assigned?
    extraction_date = models.DateField(null=True, blank=True) #QUESTION: is this just create_date?

    def __str__(self):
        return str(self.id)

    class Meta:
        db_table = "lide_extraction"
        #TODO: 'unique together' fields


class Inhibition(NameModel):
    """
    Inhibition
    """

    #QUESTION: How is this table related to other tables? I took the liberty of adding a foreign key to PCRReplicate
    type = models.CharField(max_length=128, null=True, blank=True) #QUESTION: how is this different from the name field?
    dilution = models.FloatField(null=True, blank=True)

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
    reverse_transcription_date = models.DateField(null=True, blank=True) #QUESTION: is this just create date?

    def __str__(self):
        return str(self.id)

    class Meta:
        db_table = "lide_reversetranscription"


class PCRReplicate(HistoryModel):
    """
    Polymerase Chain Reaction Replicate
    """

    sample = models.ForeignKey('Sample', related_name='pcrreplicates') #QUESTION: should this relation really be here, since the replicate comes directly from an extraction, which in turn comes directly from a sample?
    extraction = models.ForeignKey('Extraction', related_name='pcrreplicates')
    inhibition =  models.ForeignKey('Inhibition', related_name='pcrreplicates')
    reverse_transcription = models.ForeignKey('ReverseTranscription', related_name='pcrreplicates')
    target = models.ForeignKey('Target', related_name='pcrreplicates')
    replicate = models.IntegerField()
    pcr_date = models.DateField(null=True, blank=True) #QUESTION: is this just create date?
    cycle_of_quantification = models.FloatField(null=True, blank=True)
    gc_rxn = models.FloatField(null=True, blank=True) #QUESTION: what is this?
    concentration = models.FloatField(null=True, blank=True)
    sample_mean_concentration = models.FloatField(null=True, blank=True) #QUESTION: does this belong here? seems like a "mean" value should be above (i.e., the one in 1:N) the table of the values producing the mean.
    concentration_unit = models.CharField(max_length=128, null=True, blank=True) #QUESTION: shouldn't this be in it's own table ("Unit") and just related here with a foreign key?

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
    efficiency = models.CharField(max_length=128, null=True, blank=True) #QUESTION: what is the actual field type (char, int, float)? This is just a guess.

    def __str__(self):
        return str(self.id)

    class Meta:
        db_table = "lide_standardcurve"


class Target(HistoryModel):
    """
    Target
    """

    abbreviation = models.CharField(max_length=128, null=True, blank=True)
    type = models.CharField(max_length=128, null=True, blank=True) #QUESTION: how is this different from the name field?

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

    #QUESTION: shouldn't there also be some kind of 'qc value' field and a 'qc flag' field?
    #QUESTION: aren't qcs performed on other objects besides samples, like extraction or replicate?
    type = models.ForeignKey('ControlType', related_name='controls')
    sample = models.ForeignKey('Sample', related_name='controls')
    target = models.ForeignKey('Target', related_name='controls')
    cycle_of_quantification = models.FloatField(null=True, blank=True) #QUESTION: why would a qc have a CQ?
    control_date = models.DateField(null=True, blank=True) #QUESTION: is this just create date?

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
    other_analysis_date = models.DateField(null=True, blank=True) #QUESTION: is this just create date?

    def __str__(self):
        return str(self.id)

    class Meta:
        db_table = "lide_otheranalysis"

