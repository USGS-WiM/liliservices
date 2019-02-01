from decimal import Decimal
from datetime import date
from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator
from django.conf import settings
from simple_history.models import HistoricalRecords


# Users will be stored in the core User model instead of a custom model.
# Default fields of the core User model: username, first_name, last_name, email, password, groups, user_permissions,
# is_staff, is_active, is_superuser, last_login, date_joined
# For more information, see: https://docs.djangoproject.com/en/1.11/ref/contrib/auth/#user


DECIMAL_PRECISION_100 = Decimal('1E-100')
DECIMAL_PRECISION_10 = Decimal('1E-10')
MINVAL_DECIMAL_100 = MinValueValidator(DECIMAL_PRECISION_100)
MINVAL_DECIMAL_10 = MinValueValidator(DECIMAL_PRECISION_10)
MINVAL_ZERO = MinValueValidator(0)


def get_sci_val(decimal_val):
    """
    returns the scientific notation for a decimal value
    :param decimal_val: the decimal value to be converted
    :return: the scientific notation of the decimal value
    """
    sci_val = '0'
    if decimal_val:
        sci_val = '{0: E}'.format(decimal_val)
        sci_val = sci_val.split('E')[0].rstrip('0').rstrip('.') + 'E' + sci_val.split('E')[1]
    return sci_val


class NonnegativeIntegerField(models.IntegerField):
    def __init__(self, *args, **kwargs):
        kwargs['validators'] = [MINVAL_ZERO]
        super(NonnegativeIntegerField, self).__init__(*args, **kwargs)


class NullableNonnegativeDecimalField120100(models.DecimalField):
    def __init__(self, *args, **kwargs):
        kwargs['max_digits'] = 120
        kwargs['decimal_places'] = 100
        kwargs['null'] = True
        kwargs['blank'] = True
        kwargs['validators'] = [MINVAL_ZERO]
        super(NullableNonnegativeDecimalField120100, self).__init__(*args, **kwargs)


class NonnegativeDecimalField2010(models.DecimalField):
    def __init__(self, *args, **kwargs):
        kwargs['max_digits'] = 20
        kwargs['decimal_places'] = 10
        kwargs['validators'] = [MINVAL_ZERO]
        super(NonnegativeDecimalField2010, self).__init__(*args, **kwargs)


class NonzeroDecimalField2010(models.DecimalField):
    def __init__(self, *args, **kwargs):
        kwargs['max_digits'] = 20
        kwargs['decimal_places'] = 10
        kwargs['validators'] = [MINVAL_DECIMAL_10]
        super(NonzeroDecimalField2010, self).__init__(*args, **kwargs)


class NullableNonnegativeDecimalField2010(models.DecimalField):
    def __init__(self, *args, **kwargs):
        kwargs['max_digits'] = 20
        kwargs['decimal_places'] = 10
        kwargs['null'] = True
        kwargs['blank'] = True
        kwargs['validators'] = [MINVAL_ZERO]
        super(NullableNonnegativeDecimalField2010, self).__init__(*args, **kwargs)


class NullableNonzeroDecimalField2010(models.DecimalField):
    def __init__(self, *args, **kwargs):
        kwargs['max_digits'] = 20
        kwargs['decimal_places'] = 10
        kwargs['null'] = True
        kwargs['blank'] = True
        kwargs['validators'] = [MINVAL_DECIMAL_10]
        super(NullableNonzeroDecimalField2010, self).__init__(*args, **kwargs)


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
    sampler_name = models.CharField(max_length=128, blank=True)
    sample_notes = models.TextField(blank=True)
    sample_description = models.TextField(blank=True)
    arrival_date = models.DateField(null=True, blank=True)
    arrival_notes = models.TextField(blank=True)
    collection_start_date = models.DateField(db_index=True)
    collection_start_time = models.TimeField(null=True, blank=True)
    collection_end_date = models.DateField(null=True, blank=True)
    collection_end_time = models.TimeField(null=True, blank=True)
    meter_reading_initial = NullableNonnegativeDecimalField2010()
    meter_reading_final = NullableNonnegativeDecimalField2010()
    meter_reading_unit = models.ForeignKey('Unit', null=True, related_name='samples_meter_units')
    total_volume_sampled_initial = NullableNonnegativeDecimalField2010()
    total_volume_sampled_unit_initial = models.ForeignKey('Unit', null=True, related_name='samples_tvs_units')
    total_volume_or_mass_sampled = NonnegativeDecimalField2010()
    sample_volume_initial = NullableNonnegativeDecimalField2010()
    filter_born_on_date = models.DateField(null=True, blank=True)
    filter_flag = models.BooleanField(default=False)
    secondary_concentration_flag = models.BooleanField(default=False)
    elution_notes = models.TextField(blank=True)
    technician_initials = models.CharField(max_length=128, blank=True)
    dissolution_volume = NullableNonzeroDecimalField2010()
    post_dilution_volume = NullableNonzeroDecimalField2010()
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

    @property
    def aliquot_string(self):
        """Returns the concatenated parent ID and child series number of the record"""
        return '%s-%s' % (self.sample, self.aliquot_number)

    sample = models.ForeignKey('Sample', related_name='aliquots')
    freezer_location = models.ForeignKey('FreezerLocation', related_name='aliquot')
    aliquot_number = NonnegativeIntegerField()
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


class FreezerLocationManager(models.Manager):

    # get the last occupied location, either in the all freezers regardless of study or for just a particular study
    def get_last_occupied_spot(self, study_id=None):
        if study_id is not None:
            sample_ids = Sample.objects.filter(study__exact=study_id).values_list('id')
            aliquot_ids = Aliquot.objects.filter(sample__in=sample_ids).values_list('id')
            max_freezer = self.filter(aliquot__in=aliquot_ids).aggregate(models.Max('freezer'))
            max_rack = self.filter(
                aliquot__in=aliquot_ids, freezer__exact=max_freezer['freezer__max']).aggregate(models.Max('rack'))
            max_box = self.filter(
                aliquot__in=aliquot_ids, freezer__exact=max_freezer['freezer__max'],
                rack__exact=max_rack['rack__max']).aggregate(models.Max('box'))
            max_row = self.filter(
                aliquot__in=aliquot_ids, freezer__exact=max_freezer['freezer__max'],
                rack__exact=max_rack['rack__max'], box__exact=max_box['box__max']).aggregate(models.Max('row'))
            max_spot = self.filter(
                aliquot__in=aliquot_ids, freezer__exact=max_freezer['freezer__max'],
                rack__exact=max_rack['rack__max'], box__exact=max_box['box__max'],
                row__exact=max_row['row__max']).aggregate(models.Max('spot'))
            last_spot = self.filter(
                aliquot__in=aliquot_ids, freezer__exact=max_freezer['freezer__max'],
                rack__exact=max_rack['rack__max'], box__exact=max_box['box__max'],
                row__exact=max_row['row__max'], spot__exact=max_spot['spot__max']).first()
        else:
            # ignore all freezers that do not yet have locations used by aliquots
            freezer_ids = list(Freezer.objects.all().values_list('id', flat=True))
            freezer_ids.sort()
            freezer_id = 0
            count_locations = 0
            while count_locations == 0:
                freezer_id = freezer_ids.pop()
                count_locations = self.filter(freezer__exact=freezer_id).count()
            max_freezer = Freezer.objects.filter(id=freezer_id).first()

            max_rack = self.filter(
                freezer__exact=max_freezer).aggregate(models.Max('rack'))
            max_box = self.filter(
                freezer__exact=max_freezer, rack__exact=max_rack['rack__max']).aggregate(models.Max('box'))
            max_row = self.filter(
                freezer__exact=max_freezer, rack__exact=max_rack['rack__max'],
                box__exact=max_box['box__max']).aggregate(models.Max('row'))
            max_spot = self.filter(
                freezer__exact=max_freezer, rack__exact=max_rack['rack__max'],
                box__exact=max_box['box__max'], row__exact=max_row['row__max']).aggregate(models.Max('spot'))
            last_spot = self.filter(
                freezer__exact=max_freezer, rack__exact=max_rack['rack__max'],
                box__exact=max_box['box__max'], row__exact=max_row['row__max'],
                spot__exact=max_spot['spot__max']).first()
        return last_spot

    # get the next available location, given a particular last spot
    def get_next_available_spot(self, last_spot):
        avail_spots = self.get_available_spots_in_box(last_spot)
        next_spot = {'freezer': last_spot.freezer.id}
        if avail_spots > 0:
            spots_in_row = last_spot.freezer.spots
            next_spot['rack'] = last_spot.rack
            next_spot['box'] = last_spot.box
            next_spot['row'] = last_spot.row if last_spot.spot < spots_in_row else last_spot.row + 1
            next_spot['spot'] = last_spot.spot + 1 if last_spot.spot < spots_in_row else 1
            next_spot['available_spots_in_box'] = avail_spots
        else:
            next_spot = self.get_next_empty_box()
        return next_spot

    # get the count of contiguous available spots left in a box after the spot occupied by this model instance (record)
    def get_available_spots_in_box(self, freezer_location):
        # get dimensions of a box being used in the freezer that contains the current model instance (record)
        rows_in_box = freezer_location.freezer.rows
        spots_in_row = freezer_location.freezer.spots
        spots_in_box = rows_in_box * spots_in_row

        # check if there are any occupied spots after this model instance (record) in the same row
        next_occupied_spot_in_row = self.filter(freezer__exact=freezer_location.freezer,
                                                rack__exact=freezer_location.rack, box__exact=freezer_location.box,
                                                row__exact=freezer_location.row, spot__gt=freezer_location.spot).first()
        if next_occupied_spot_in_row is not None:
            # there are occupied spots in the same row after this model instance (record),
            # so calculate the simple difference between the next occupied spot and this model instance (record)
            available_spots = next_occupied_spot_in_row.spot - freezer_location.spot - 1
        # else there are no other occupied spots after this model instance (record) in the row
        else:
            # check if there are any occupied spots in rows after the row of this model instance (record)
            next_occupied_spot_in_box = self.filter(freezer__exact=freezer_location.freezer,
                                                    rack__exact=freezer_location.rack, box__exact=freezer_location.box,
                                                    row__gt=freezer_location.row).first()
            if next_occupied_spot_in_box is not None:
                # there are occupied spots in rows after this model instance (record),
                # so calculate the simple difference between the next occupied spot and this model instance (record)
                empty_rows_between_studies = (next_occupied_spot_in_box.row - freezer_location.row) - 1
                empty_row_spots = empty_rows_between_studies * spots_in_row
                empty_spots_in_row_next_spot = next_occupied_spot_in_box.spot - 1
                empty_spots_in_row_last_spot = spots_in_row - freezer_location.spot
                available_spots = empty_spots_in_row_last_spot + empty_row_spots + empty_spots_in_row_next_spot
            # else there are no occupied spots in rows after this model instance (record)
            else:
                # calculate the simple difference between total box spots and this model instance (record)
                occupied_spots = ((freezer_location.row - 1) * spots_in_row) + freezer_location.spot
                available_spots = spots_in_box - occupied_spots
        return available_spots

    # get the next box with no occupied spots
    def get_next_empty_box(self):
        # if no last spot was found or adding another rack will exceed the number of racks allowed in any freezer,
        # next_empty_box should return None
        next_empty_box = None
        last_spot = self.get_last_occupied_spot()
        if last_spot is not None:
            # start building the next empty box object
            next_empty_box = {'freezer': last_spot.freezer.id}
            # check if adding another box will exceed the number of boxes allowed per rack in this freezer
            if last_spot.box + 1 > last_spot.freezer.boxes:
                # check if there is still room for another rack in this freezer,
                # and if so just increment the rack number
                if last_spot.rack + 1 <= last_spot.freezer.racks:
                    next_empty_box['rack'] = last_spot.rack + 1
                    next_empty_box['box'] = 1
                    next_empty_box['row'] = 1
                    next_empty_box['spot'] = 1
                    next_empty_box['available_spots_in_box'] = last_spot.freezer.rows * last_spot.freezer.spots
                # otherwise check if there is another freezer,
                # and if so return the first location in that entire freezer
                else:
                    next_freezer = Freezer.objects.filter(id=(last_spot.freezer.id + 1)).first()
                    if next_freezer is not None:
                        next_empty_box['freezer'] = next_freezer.id
                        next_empty_box['rack'] = 1
                        next_empty_box['box'] = 1
                        next_empty_box['row'] = 1
                        next_empty_box['spot'] = 1
                        next_empty_box['available_spots_in_box'] = next_freezer.rows * next_freezer.spots
            # there is still room for another box in this rack, so just increment the box number
            else:
                next_empty_box['rack'] = last_spot.rack
                next_empty_box['box'] = last_spot.box + 1
                next_empty_box['row'] = 1
                next_empty_box['spot'] = 1
                next_empty_box['available_spots_in_box'] = last_spot.freezer.rows * last_spot.freezer.spots
        return next_empty_box


class FreezerLocation(HistoryModel):
    """
    Freezer Location
    """

    freezer = models.ForeignKey('Freezer', related_name='freezerlocations')
    rack = NonnegativeIntegerField()
    box = NonnegativeIntegerField()
    row = NonnegativeIntegerField()
    spot = NonnegativeIntegerField()
    objects = FreezerLocationManager()

    def __str__(self):
        return str(self.id)

    class Meta:
        db_table = "lide_freezer_location"
        unique_together = ("freezer", "rack", "box", "row", "spot")


class Freezer(NameModel):
    """
    Freezer
    """

    racks = NonnegativeIntegerField()
    boxes = NonnegativeIntegerField()
    rows = NonnegativeIntegerField()
    spots = NonnegativeIntegerField()

    def __str__(self):
        return str(self.id)

    class Meta:
        db_table = "lide_freezer"


######
#
#  Final Sample Values
#
######


class FinalConcentratedSampleVolume(HistoryModel):
    """
    Final Concentrated Sample Volume
    """

    @property
    def final_concentrated_sample_volume_sci(self):
        return get_sci_val(self.final_concentrated_sample_volume)

    sample = models.OneToOneField('Sample', related_name='final_concentrated_sample_volume')
    concentration_type = models.ForeignKey('ConcentrationType', related_name='final_concentrated_sample_volumes')
    final_concentrated_sample_volume = models.DecimalField(
        max_digits=120, decimal_places=100, validators=[MINVAL_DECIMAL_100])
    notes = models.TextField(blank=True)

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


class FinalSampleMeanConcentration(HistoryModel):
    """
    Final Sample Mean Concentration
    """

    @property
    def final_sample_mean_concentration_sci(self):
        return get_sci_val(self.final_sample_mean_concentration)

    final_sample_mean_concentration = NullableNonnegativeDecimalField120100()
    sample = models.ForeignKey('Sample', related_name='final_sample_mean_concentrations')
    target = models.ForeignKey('Target', related_name='final_sample_mean_concentrations')

    # Calculate sample mean concentration for all samples whose target replicates are now in the database
    def calc_sample_mean_conc(self):
        reps_count = 0
        pos_replicate_concentrations = []
        reps = PCRReplicate.objects.filter(sample_extraction__sample=self.sample.id,
                                           pcrreplicate_batch__target__exact=self.target)
        for rep in reps:
            # ignore invalid reps and redos
            if rep.invalid is False and rep.pcrreplicate_batch.re_pcr is None:
                if rep.replicate_concentration is None:
                    # this rep has no replicate_concentration
                    # therefore not all sample-target combos are in the DB, so set this FSMC to null
                    return None
                if rep.replicate_concentration >= 0:
                    reps_count += 1
                    pos_replicate_concentrations.append(rep.replicate_concentration)
        return sum(pos_replicate_concentrations) / reps_count if reps_count > 0 else None

    def __str__(self):
        return str(self.id)

    class Meta:
        db_table = "lide_finalsamplemeanconcentration"
        unique_together = ("sample", "target")


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
    analysis_batch_notes = models.CharField(max_length=128, blank=True)

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
    extraction_volume = NonnegativeDecimalField2010()
    elution_volume = NonzeroDecimalField2010()

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

    @property
    def extraction_string(self):
        """Returns the concatenated parent ID and child series number of the record"""
        return '%s-%s' % (self.analysis_batch, self.extraction_number)

    analysis_batch = models.ForeignKey('AnalysisBatch', related_name='extractionbatches')
    extraction_method = models.ForeignKey('ExtractionMethod', related_name='extractionbatches')
    re_extraction = models.ForeignKey('self', null=True, related_name='extractionbatches')
    re_extraction_notes = models.TextField(blank=True)
    extraction_number = NonnegativeIntegerField()
    extraction_volume = NonnegativeDecimalField2010()
    extraction_date = models.DateField(default=date.today, db_index=True)
    pcr_date = models.DateField(default=date.today, db_index=True)
    qpcr_template_volume = models.DecimalField(
        max_digits=20, decimal_places=10, default=6, validators=[MINVAL_ZERO])
    elution_volume = NonzeroDecimalField2010()
    sample_dilution_factor = NonnegativeIntegerField()
    qpcr_reaction_volume = models.DecimalField(
        max_digits=20, decimal_places=10, default=20, validators=[MINVAL_DECIMAL_10])
    ext_pos_cq_value = NullableNonnegativeDecimalField2010()
    ext_pos_gc_reaction = NullableNonnegativeDecimalField120100()
    ext_pos_invalid = models.BooleanField(default=True)

    # override the save method to calculate invalid flag
    def save(self, *args, **kwargs):
        # assess the invalid flag
        # invalid flag defaults to True (i.e., the extraction batch is invalid)
        # and can only be set to False if the cq_value of this extraction batch is equal to zero
        self.ext_pos_invalid = False if self.ext_pos_cq_value == 0 else True

        super(ExtractionBatch, self).save(*args, **kwargs)

        if self.ext_pos_invalid:
            sampleextractions = SampleExtraction.objects.filter(extraction_batch=self.id)
            for sampleextraction in sampleextractions:
                pcrreplicates = PCRReplicate.objects.filter(sample_extraction=sampleextraction.id)
                for pcrreplicate in pcrreplicates:
                    pcrreplicate.invalid = True
                    pcrreplicate.save()

                    # determine if all replicates for a given sample-target combo are now in the database or not
                    # and calculate sample mean concentration if yes or set to null if no
                    pcrrepbatch = PCRReplicateBatch.objects.get(id=pcrreplicate.pcrreplicate_batch.id)
                    fsmc = FinalSampleMeanConcentration.objects.filter(
                        sample=sampleextraction.sample.id, target=pcrrepbatch.target.id).first()
                    # if the sample-target combo (fsmc) does not exist, create it
                    if not fsmc:
                        fsmc = FinalSampleMeanConcentration.objects.create(
                            sample=sampleextraction.sample, target=pcrrepbatch.target,
                            created_by=self.created_by, modified_by=self.modified_by)
                    # update final sample mean concentration
                    # if all the valid related reps have replicate_concentration values the FSMC will be calculated
                    # else not all valid related reps have replicate_concentration values, so FSMC will be set to null
                    fsmc.final_sample_mean_concentration = fsmc.calc_sample_mean_conc()
                    fsmc.save()

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

    @property
    def rt_pos_gc_reaction_sci(self):
        return get_sci_val(self.rt_pos_gc_reaction)

    extraction_batch = models.ForeignKey('ExtractionBatch', related_name='reversetranscriptions')
    template_volume = models.DecimalField(
        max_digits=20, decimal_places=10, default=8.6, validators=[MINVAL_ZERO])
    reaction_volume = models.DecimalField(
        max_digits=20, decimal_places=10, default=50, validators=[MINVAL_DECIMAL_10])
    rt_date = models.DateField(default=date.today, null=True, blank=True, db_index=True)
    re_rt = models.ForeignKey('self', null=True, related_name='reversetranscriptions')
    re_rt_notes = models.TextField(blank=True)
    rt_pos_cq_value = NullableNonnegativeDecimalField2010()
    rt_pos_gc_reaction = NullableNonnegativeDecimalField120100()
    rt_pos_invalid = models.BooleanField(default=True)

    # override the save method to calculate invalid flag
    def save(self, *args, **kwargs):
        # assess the invalid flag
        # invalid flag defaults to True (i.e., the RT is invalid)
        # and can only be set to False if the cq_value of this RT is equal to zero
        self.rt_pos_invalid = False if self.rt_pos_cq_value == 0 else True

        super(ReverseTranscription, self).save(*args, **kwargs)

        if self.rt_pos_invalid:
            sampleextractions = SampleExtraction.objects.filter(
                extraction_batch=self.extraction_batch)
            for sampleextraction in sampleextractions:
                pcrreplicates = PCRReplicate.objects.filter(sample_extraction=sampleextraction.id)
                for pcrreplicate in pcrreplicates:
                    pcrreplicate.invalid = True
                    pcrreplicate.save()

                    # determine if all replicates for a given sample-target combo are now in the database or not
                    # and calculate sample mean concentration if yes or set to null if no
                    pcrrepbatch = PCRReplicateBatch.objects.get(id=pcrreplicate.pcrreplicate_batch.id)
                    fsmc = FinalSampleMeanConcentration.objects.filter(
                        sample=sampleextraction.sample.id, target=pcrrepbatch.target.id).first()
                    # if the sample-target combo (fsmc) does not exist, create it
                    if not fsmc:
                        fsmc = FinalSampleMeanConcentration.objects.create(
                            sample=sampleextraction.sample, target=pcrrepbatch.target,
                            created_by=self.created_by, modified_by=self.modified_by)
                    # update final sample mean concentration
                    # if all the valid related reps have replicate_concentration values the FSMC will be calculated
                    # else not all valid related reps have replicate_concentration values, so FSMC will be set to null
                    fsmc.final_sample_mean_concentration = fsmc.calc_sample_mean_conc()
                    fsmc.save()

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
        ordering = ['sample', 'id']


class PCRReplicateBatch(HistoryModel):
    """
    Polymerase Chain Reaction Replicate Batch
    """

    @property
    def ext_neg_gc_reaction_sci(self):
        return get_sci_val(self.ext_neg_gc_reaction)

    @property
    def rt_neg_gc_reaction_sci(self):
        return get_sci_val(self.rt_neg_gc_reaction)

    @property
    def pcr_neg_gc_reaction_sci(self):
        return get_sci_val(self.pcr_neg_gc_reaction)

    @property
    def pcr_pos_gc_reaction_sci(self):
        return get_sci_val(self.pcr_pos_gc_reaction)

    extraction_batch = models.ForeignKey('ExtractionBatch', related_name='pcrreplicatebatches')
    target = models.ForeignKey('Target', related_name='pcrreplicatebatches')
    replicate_number = NonnegativeIntegerField()
    notes = models.TextField(blank=True)
    ext_neg_cq_value = NullableNonnegativeDecimalField2010()
    ext_neg_gc_reaction = NullableNonnegativeDecimalField120100()
    ext_neg_invalid = models.BooleanField(default=True)
    rt_neg_cq_value = NullableNonnegativeDecimalField2010()
    rt_neg_gc_reaction = NullableNonnegativeDecimalField120100()
    rt_neg_invalid = models.BooleanField(default=True)
    pcr_neg_cq_value = NullableNonnegativeDecimalField2010()
    pcr_neg_gc_reaction = NullableNonnegativeDecimalField120100()
    pcr_neg_invalid = models.BooleanField(default=True)
    pcr_pos_cq_value = NullableNonnegativeDecimalField2010()
    pcr_pos_gc_reaction = NullableNonnegativeDecimalField120100()
    pcr_pos_invalid = models.BooleanField(default=True)
    re_pcr = models.ForeignKey('self', null=True, related_name='pcrreplicatebatches')

    # override the save method to calculate and invalid flags
    def save(self, *args, **kwargs):
        # assess the invalid flags
        # invalid flags default to True (i.e., the rep is invalid)
        # and can only be set to False if the cq_values of this rep batch are equal to zero
        self.ext_neg_invalid = False if self.ext_neg_cq_value == 0 else True
        self.pcr_neg_invalid = False if self.pcr_neg_cq_value == 0 else True
        # reverse transcriptions are a special case... not every extraction batch will have a RT,
        # so if there is no RT, set rt_neg_invalid to False regardless of the value of rt_neg_cq_value,
        # but if there is a RT, apply the same logic as the other invalid flags
        if self.extraction_batch.reversetranscriptions.count() == 0:
            self.rt_neg_invalid = False
        else:
            self.rt_neg_invalid = False if self.rt_neg_cq_value == 0 else True
        # validating the pcr_pos will come in a later release of the software
        # sc = validated_data.get('standard_curve', None)
        self.pcr_pos_invalid = False

        super(PCRReplicateBatch, self).save(*args, **kwargs)

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

    @property
    def gc_reaction_sci(self):
        return get_sci_val(self.gc_reaction)

    @property
    def replicate_concentration_sci(self):
        return get_sci_val(self.replicate_concentration)

    sample_extraction = models.ForeignKey('SampleExtraction', related_name='pcrreplicates')
    pcrreplicate_batch = models.ForeignKey('PCRReplicateBatch', related_name='pcrreplicates')
    cq_value = NullableNonnegativeDecimalField2010()
    gc_reaction = NullableNonnegativeDecimalField120100()
    replicate_concentration = models.DecimalField(
        max_digits=120, decimal_places=100, null=True, blank=True, validators=[MINVAL_DECIMAL_100])
    concentration_unit = models.ForeignKey('Unit', related_name='pcrreplicates')
    invalid = models.BooleanField(default=True)
    invalid_override = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, related_name='pcrreplicates')

    # override the save method to assign or calculate concentration_unit, replicate_concentration, and invalid flag
    def save(self, *args, **kwargs):
        # assign the correct (and required) concentration unit value
        self.concentration_unit = self.get_conc_unit(self.sample_extraction.sample.id)

        # if there is a gc_reaction value, calculate the replicate_concentration and set the concentration_unit
        if self.gc_reaction is not None and self.gc_reaction > Decimal('0'):
            # calculate their replicate_concentration
            self.replicate_concentration = self.calc_rep_conc()

        # assess the invalid flags
        # invalid flags default to True (i.e., the rep is invalid) and can only be set to False if:
        #     1. all parent controls exist
        #     2. all parent control flags are False (i.e., the controls are valid)
        #     3. the cq_value and gc_reaction of this rep are greater than or equal to zero
        if self.invalid_override is None:
            if self.cq_value is not None and self.gc_reaction is not None:
                pcrreplicate_batch = PCRReplicateBatch.objects.filter(id=self.pcrreplicate_batch.id).first()
                # first check related peg_neg validity
                # assume no related peg_neg, in which case this control does not apply
                # but if there is a related peg_neg, check the validity of its reps with same target as this data rep
                any_peg_neg_invalid = False
                peg_neg_id = self.sample_extraction.sample.peg_neg
                if peg_neg_id is not None:
                    peg_neg_invalid_flags = []
                    target_id = pcrreplicate_batch.target.id
                    # only check sample extractions with the same peg_neg_id as the sample of this data rep
                    ext_ids = SampleExtraction.objects.filter(sample=peg_neg_id).values_list('id', flat=True)
                    for ext_id in ext_ids:
                        # only check reps with the same target as this data rep
                        reps = PCRReplicate.objects.filter(sample_extraction=ext_id,
                                                           pcrreplicate_batch__target__exact=target_id)
                        # if even a single one of the peg_neg reps is invalid, the data rep must be set to invalid
                        for rep in reps:
                            peg_neg_invalid_flags.append(rep.invalid)
                    any_peg_neg_invalid = any(peg_neg_invalid_flags)
                # then check all controls applicable to this rep
                if (
                        not any_peg_neg_invalid and
                        not pcrreplicate_batch.ext_neg_invalid and
                        not pcrreplicate_batch.rt_neg_invalid and
                        not pcrreplicate_batch.pcr_neg_invalid and
                        self.cq_value >= Decimal('0') and
                        self.gc_reaction >= Decimal('0')
                ):
                    self.invalid = False
                else:
                    self.invalid = True
            else:
                self.invalid = True

        super(PCRReplicate, self).save(*args, **kwargs)

        # determine if all replicates for a given sample-target combo are now in the database or not
        # and calculate sample mean concentration if yes or set to null if no
        fsmc = FinalSampleMeanConcentration.objects.filter(
            sample=self.sample_extraction.sample.id, target=self.pcrreplicate_batch.target.id).first()
        # if the sample-target combo (fsmc) does not exist, create it
        if not fsmc:
            fsmc = FinalSampleMeanConcentration.objects.create(
                sample=self.sample_extraction.sample, target=self.pcrreplicate_batch.target,
                created_by=self.created_by, modified_by=self.modified_by)
        # update final sample mean concentration
        # if all the valid related reps have replicate_concentration values the FSMC will be calculated
        # otherwise not all valid related reps have replicate_concentration values, so FSMC will be set to null
        fsmc.final_sample_mean_concentration = fsmc.calc_sample_mean_conc()
        fsmc.save()

    # get the concentration_unit
    def get_conc_unit(self, sample_id):
        sample = Sample.objects.get(id=sample_id)
        if sample.matrix.code in ['F', 'SM']:
            conc_unit = Unit.objects.get(name='gram')
        else:
            conc_unit = Unit.objects.get(name='Liter')
        return conc_unit

    # TODO: ask what to do about zeros
    # Calculate replicate_concentration, but only if gc_reaction is a positive number
    def calc_rep_conc(self):
        if self.gc_reaction is not None and self.gc_reaction > Decimal('0'):
            nucleic_acid_type = self.pcrreplicate_batch.target.nucleic_acid_type
            extr = self.sample_extraction
            eb = self.sample_extraction.extraction_batch
            sample = self.sample_extraction.sample
            matrix = sample.matrix.code
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
            if matrix in ['F', 'W', 'WW']:
                fcsv = FinalConcentratedSampleVolume.objects.get(sample=sample.id)
                prelim_value = prelim_value * (
                        fcsv.final_concentrated_sample_volume / sample.total_volume_or_mass_sampled)
            elif matrix == 'A':
                prelim_value = prelim_value * (sample.dissolution_volume / sample.total_volume_or_mass_sampled)
            elif matrix == 'SM':
                prelim_value = prelim_value * (sample.post_dilution_volume / sample.total_volume_or_mass_sampled)
            # finally, apply the unit-cancelling expression
            if matrix in ['A', 'F', 'W', 'WW']:
                # 1,000 microliters per 1 milliliter
                final_value = prelim_value * 1000
            elif matrix == 'LM':
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


# TODO: this whole StandardCurve class needs to be reviewed when the time comes
class StandardCurve(HistoryModel):
    """
    Standard Curve
    """

    r_value = NullableNonnegativeDecimalField2010()
    slope = NullableNonnegativeDecimalField2010()
    efficiency = NullableNonnegativeDecimalField2010()
    pos_ctrl_cq = NullableNonnegativeDecimalField2010()
    pos_ctrl_cq_range = NullableNonnegativeDecimalField2010()
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
    dilution_factor = models.IntegerField(null=True, blank=True, validators=[MINVAL_ZERO])

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
    notes = models.TextField(blank=True)

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
        unique_together = ("table", "field")


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
