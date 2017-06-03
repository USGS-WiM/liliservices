from datetime import date
from django.core import validators
from django.db import models
from django.contrib.auth.models import User
from django.contrib import admin
from django.conf import settings
from localflavor.us.models import USStateField, USZipCodeField
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


class AddressModel(HistoryModel):
    """
    An abstract base class model for common address fields.
    """

    street = models.CharField(max_length=255, blank=True)
    unit = models.CharField(max_length=255, blank=True) 
    city = models.CharField(max_length=255, blank=True)
    state = USStateField(null=True, blank=True)
    zipcode = USZipCodeField(null=True, blank=True)

    class Meta:
        abstract = True


class NameModel(HistoryModel):
    """
    An abstract base class model for the common name field.
    """

    name = models.CharField(max_length=128, null=True, blank=True)

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

    study = models.ForeignKey('Study', related_name='samples')
    study_site_name = models.CharField(max_length=128, null=True, blank=True) #QUESTION: shouldn't this be in it's own table ("StudySite") and just related here with a foreign key?
    study_site_id = models.IntegerField() #QUESTION: shouldn't this be in it's own table ("StudySite") and just related here with a foreign key?
    collaborator_sample = models.IntegerField(unique=True)
    collect_start_date = models.DateField(null=True, blank=True)
    collect_start_time = models.TimeField(null=True, blank=True)
    collect_end_date = models.DateField(null=True, blank=True)
    collect_end_time = models.TimeField(null=True, blank=True)
    description = models.TextField(blank=True)
    filtered_volume = models.FloatField(null=True, blank=True)
    filter = models.ForeignKey('FilterType', related_name='samples')
    filter_bornon_date = models.DateField(null=True, blank=True) #QUESTION: is this just the filter's create date?
    sample_name = models.CharField(max_length=128, null=True, blank=True) #QUESTION: shouldn't this be in it's own table ("Sampler" or "Person") and just related here with a foreign key?
    notes = models.TextField()
    imr = models.FloatField(null=True, blank=True)
    fmr = models.FloatField(null=True, blank=True)
    unit = models.CharField(max_length=128, null=True, blank=True) #QUESTION: shouldn't this be in it's own table ("Unit") and just related here with a foreign key?
    sample_type = models.ForeignKey('SampleType', related_name='samples')
    sample_location_type = models.ForeignKey('SampleLocationType', related_name='samples')
    sample_environment = models.ForeignKey('SampleEnvironment', related_name='samples')
    water_type = models.ForeignKey('WaterType', related_name='samples')
    initial_volume = models.FloatField(null=True, blank=True)
    tvs = models.FloatField(null=True, blank=True)  #QUESTION: What are these TVS things? Shouldn't they have their own distinct ("TVS") table?
    tvs_unit = models.CharField(max_length=128, null=True, blank=True) #QUESTION: shouldn't this be in it's own table ("Unit") and just related here with a foreign key?
    tvs_stage = models.FloatField(null=True, blank=True)
    tvs_calculation = models.FloatField(null=True, blank=True)
    tvs_stage_calculation = models.FloatField(null=True, blank=True)
    matrix = models.CharField(max_length=128, null=True, blank=True)  #QUESTION: why is this here and in Filter Type? Shouldn't there be a distinct "Matrix" table?
    filter_flag = models.BooleanField(default=False)
    secondary_concentration_flag = models.BooleanField(default=False)
    analysisbatches = models.ManyToManyField('AnalysisBatch', through='SampleAnalysisBatch', related_name='samples')

    def __str__(self):
        return self.id

    class Meta:
        db_table = "lide_sample"


class AnalysisBatch(HistoryModel):
    """
    Analysis Batch
    """

    some_field = models.CharField(max_length=128, null=True, blank=True)
    samples = models.ManyToManyField('Sample', through='SampleAnalysisBatch', related_name='analysisbatches')

    def __str__(self):
        return self.id

    class Meta:
        db_table = "lide_analysisbatch"


class Extraction(HistoryModel):
    """
    Extraction
    """

    analysis_batch = models.ForeignKey('AnalysisBatch', related_name='extractions')
    extraction_code = models.IntegerField(unique=True)
    extraction_date = models.DateField(null=True, blank=True) #QUESTION: is this just create_date?

    def __str__(self):
        return self.id

    class Meta:
        db_table = "lide_extraction"


class SampleType(NameModel):
    """
    Sample Type
    """

    def __str__(self):
        return self.id

    class Meta:
        db_table = "lide_sampletype"


class SampleEnvironment(NameModel):
    """
    Sample Environment
    """

    def __str__(self):
        return self.id

    class Meta:
        db_table = "lide_sampleenvironment"


class FilterType(NameModel):
    """
    Filter Type
    """

    matrix = models.CharField(max_length=128, null=True, blank=True)

    def __str__(self):
        return self.id

    class Meta:
        db_table = "lide_filtertype"


class Study(NameModel):
    """
    Study
    """

    description = models.TextField(blank=True)

    def __str__(self):
        return self.id

    class Meta:
        db_table = "lide_study"


class WaterType(NameModel):
    """
    Water Type
    """

    def __str__(self):
        return self.id

    class Meta:
        db_table = "lide_watertype"


class SampleLocationType(NameModel):
    """
    Sample Location Type
    """

    def __str__(self):
        return self.id

    class Meta:
        db_table = "lide_samplelocationtype"


class Inhibition(NameModel):
    """
    Inhibition
    """

    type = models.CharField(max_length=128, null=True, blank=True) #QUESTION: how is this different from the name field?
    dilution = models.FloatField(null=True, blank=True)

    def __str__(self):
        return self.id

    class Meta:
        db_table = "lide_inhibition"


class RT(NameModel):
    """
    RT
    """

    extraction = models.ForeignKey('Extraction', related_name='rts')
    volume_in = models.FloatField(null=True, blank=True)
    volume_out = models.FloatField(null=True, blank=True)
    cq = models.FloatField(null=True, blank=True)
    rt_date = models.DateField(null=True, blank=True) #QUESTION: is this just create date?

    def __str__(self):
        return self.id

    class Meta:
        db_table = "lide_rt"


class StandardCurve(HistoryModel):
    """
    Standard Curve
    """

    r_val = models.FloatField(null=True, blank=True)
    slope = models.FloatField(null=True, blank=True)
    efficiency = models.CharField(max_length=128, null=True, blank=True) #QUESTION: what is the actual field type? This isjust a guess.

    def __str__(self):
        return self.id

    class Meta:
        db_table = "lide_standardcurve"


class PCRReplicate(HistoryModel):
    """
    PCR Replicate
    """

    sample = models.ForeignKey('Sample', related_name='pcrreplicates')
    target = models.ForeignKey('Target', related_name='pcrreplicates')
    rt = models.ForeignKey('RT', related_name='pcrreplicates')
    replicate = models.IntegerField()
    pcr_date = models.DateField(null=True, blank=True) #QUESTION: is this just create date?
    cq = models.FloatField(null=True, blank=True)
    gc_rxn = models.FloatField(null=True, blank=True)
    concentration = models.FloatField(null=True, blank=True)
    sample_mean_concentration = models.FloatField(null=True, blank=True) #QUESTION: does this belong here? seems like a "mean" value should be above (i.e., the one in 1:N) the table of the values producing the mean.
    concentration_unit = models.CharField(max_length=128, null=True, blank=True) #QUESTION: shouldn't this be in it's own table ("Unit") and just related here with a foreign key?
    

    def __str__(self):
        return self.id

    class Meta:
        db_table = "lide_pcrreplicate"


class ControlType(NameModel):
    """
    Control Type
    """

    abbreviation = models.CharField(max_length=128, null=True, blank=True)

    def __str__(self):
        return self.id

    class Meta:
        db_table = "lide_controltype"


class Control(NameModel):
    """
    Control
    """

    type = models.ForeignKey('ControlType', related_name='controls')
    sample = models.ForeignKey('Sample', related_name='controls')
    target = models.ForeignKey('Target', related_name='controls')
    cq = models.FloatField(null=True, blank=True)
    control_date = models.DateField(null=True, blank=True) #QUESTION: is this just create date?

    def __str__(self):
        return self.id

    class Meta:
        db_table = "lide_control"


class Target(HistoryModel):
    """
    Target
    """

    abbreviation = models.CharField(max_length=128, null=True, blank=True)
    type = models.CharField(max_length=128, null=True, blank=True) #QUESTION: how is this different from the name field?

    def __str__(self):
        return self.id

    class Meta:
        db_table = "lide_target"


class OtherAnalysis(HistoryModel):
    """
    Other Analysis
    """

    description = models.TextField(blank=True)
    data = models.TextField(blank=True)
    other_analysis_date = models.DateField(null=True, blank=True) #QUESTION: is this just create date?

    def __str__(self):
        return self.id

    class Meta:
        db_table = "lide_otheranalysis"


class SampleAnalysisBatch(HistoryModel):
    """
    Table to allow many-to-many relationship between Samples and Analysis Batches.
    """

    sample = models.ForeignKey('Sample', related_name='sampleanalysisbatches')
    analysis_batch = models.ForeignKey('AnalysisBatch', related_name='sampleanalysisbatches')

    def __str__(self):
        return self.id

    class Meta:
        db_table = "lide_sampleanalysisbatch"
        unique_together = ("sample", "analysi_batch")
