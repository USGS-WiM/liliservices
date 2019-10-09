from decimal import Decimal
from datetime import date
from django.db import models
from django.db.models import F
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
    sci_val = ''
    if decimal_val is not None:
        if decimal_val == 0:
            sci_val = '0'
        else:
            sci_val = '{0: E}'.format(decimal_val)
            sci_val = sci_val.split('E')[0].rstrip('0').rstrip('.').lstrip() + 'E' + sci_val.split('E')[1]
    return sci_val


def recalc_reps(level, level_id, target=None, recalc_rep_conc=True, recalc_invalid=True):
    reps = None
    if level == 'Sample':
        reps = PCRReplicate.objects.filter(sample_extraction__sample=level_id)
    elif level == 'FinalSampleMeanConcentration':
        reps = PCRReplicate.objects.filter(sample_extraction__sample=level_id,
                                           pcrreplicate_batch__target__exact=target)
    elif level == 'ExtractionBatch':
        reps = PCRReplicate.objects.filter(sample_extraction__extraction_batch=level_id)
    elif level == 'PCRReplicateBatch':
        reps = PCRReplicate.objects.filter(pcrreplicate_batch=level_id)
    # elif level == 'SampleExtraction':
    #     reps = PCRReplicate.objects.filter(sample_extraction=level_id)
    elif level == 'Inhibition':
        reps_dna = PCRReplicate.objects.filter(sample_extraction__inhibition_dna=level_id)
        reps_rna = PCRReplicate.objects.filter(sample_extraction__inhibition_rna=level_id)
        reps = reps_dna.union(reps_rna).distinct()
    if reps:
        for rep in reps:
            if recalc_rep_conc:
                rep.replicate_concentration = rep.calc_rep_conc()
            if recalc_invalid and rep.invalid_override is None:
                rep.invalid = rep.calc_invalid()
            if recalc_rep_conc or recalc_invalid:
                rep.save()


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
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, models.PROTECT, null=True, blank=True, db_index=True,
                                   related_name='%(class)s_creator')
    modified_date = models.DateField(auto_now=True, null=True, blank=True)
    modified_by = models.ForeignKey(settings.AUTH_USER_MODEL, models.PROTECT, null=True, blank=True, db_index=True,
                                    related_name='%(class)s_modifier')
    history = HistoricalRecords(inherit=True)

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

    sample_type = models.ForeignKey('SampleType', models.PROTECT, related_name='samples')
    matrix = models.ForeignKey('Matrix', models.PROTECT, related_name='samples')
    filter_type = models.ForeignKey('FilterType', models.PROTECT, null=True, related_name='samples')
    study = models.ForeignKey('Study', models.PROTECT, related_name='samples')
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
    meter_reading_unit = models.ForeignKey('Unit', models.PROTECT, null=True, related_name='samplesmeterunits')
    total_volume_sampled_initial = NullableNonnegativeDecimalField2010()
    total_volume_sampled_unit_initial = models.ForeignKey(
        'Unit', models.PROTECT, null=True, related_name='samplestvsunits')
    total_volume_or_mass_sampled = NonnegativeDecimalField2010()
    sample_volume_initial = NullableNonnegativeDecimalField2010()
    filter_born_on_date = models.DateField(null=True, blank=True)
    filter_flag = models.BooleanField(default=False)
    secondary_concentration_flag = models.BooleanField(default=False)
    elution_notes = models.TextField(blank=True)
    technician_initials = models.CharField(max_length=128, blank=True)
    dissolution_volume = NullableNonzeroDecimalField2010()
    post_dilution_volume = NullableNonzeroDecimalField2010()
    analysisbatches = models.ManyToManyField('AnalysisBatch', through='SampleAnalysisBatch', related_name='samples')
    samplegroups = models.ManyToManyField('SampleGroup', through='SampleSampleGroup', related_name='samples')
    peg_neg = models.ForeignKey('self', on_delete=models.CASCADE, null=True, related_name='samples')
    record_type = models.ForeignKey('RecordType', models.PROTECT, default=1)

    # override the save method to check if a rep calc value changed, and if so, recalc rep conc and rep invalid and FSMC
    def save(self, *args, **kwargs):

        # do_recalc_reps = False
        #
        # # a value can only be changed if the instance already exists
        # if self.pk:
        #     old_sample = Sample.objects.get(id=self.pk)
        #     if self.matrix.id != old_sample.matrix.id:
        #         do_recalc_reps = True
        #     if self.total_volume_or_mass_sampled != old_sample.total_volume_or_mass_sampled:
        #         do_recalc_reps = True
        #     if self.matrix.code == 'A' and self.dissolution_volume != old_sample.dissolution_volume:
        #         do_recalc_reps = True
        #     elif self.matrix.code == 'SM' and self.post_dilution_volume != old_sample.post_dilution_volume:
        #         do_recalc_reps = True

        super(Sample, self).save(*args, **kwargs)

        # if do_recalc_reps:
        #     recalc_reps('Sample', self.id)

        # ALWAYS recalc child PCR Replicates
        recalc_reps('Sample', self.id)

    def __str__(self):
        return str(self.id)

    class Meta:
        db_table = "lide_sample"
        ordering = ['id']


class Aliquot(HistoryModel):
    """
    Aliquot
    """

    @property
    def aliquot_string(self):
        """Returns the concatenated parent ID and child series number of the record"""
        return '%s-%s' % (self.sample, self.aliquot_number)

    sample = models.ForeignKey('Sample', models.PROTECT, related_name='aliquots')
    freezer_location = models.ForeignKey('FreezerLocation', models.PROTECT, related_name='aliquots')
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

    matrix = models.ForeignKey('Matrix', models.PROTECT, related_name='filtertypes')

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

    # get the last occupied location, either in all freezers regardless of study or for just a particular study
    def get_last_occupied_spot(self, study_id=None):
        if study_id is not None:
            sample_ids = Sample.objects.filter(study__exact=study_id).values_list('id')
            aliquot_ids = Aliquot.objects.filter(sample__in=sample_ids).values_list('id')
            max_freezer = self.filter(aliquots__in=aliquot_ids).aggregate(models.Max('freezer'))
            max_rack = self.filter(
                aliquots__in=aliquot_ids, freezer__exact=max_freezer['freezer__max']).aggregate(models.Max('rack'))
            max_box = self.filter(
                aliquots__in=aliquot_ids, freezer__exact=max_freezer['freezer__max'],
                rack__exact=max_rack['rack__max']).aggregate(models.Max('box'))
            max_row = self.filter(
                aliquots__in=aliquot_ids, freezer__exact=max_freezer['freezer__max'],
                rack__exact=max_rack['rack__max'], box__exact=max_box['box__max']).aggregate(models.Max('row'))
            max_spot = self.filter(
                aliquots__in=aliquot_ids, freezer__exact=max_freezer['freezer__max'],
                rack__exact=max_rack['rack__max'], box__exact=max_box['box__max'],
                row__exact=max_row['row__max']).aggregate(models.Max('spot'))
            last_spot = self.filter(
                aliquots__in=aliquot_ids, freezer__exact=max_freezer['freezer__max'],
                rack__exact=max_rack['rack__max'], box__exact=max_box['box__max'],
                row__exact=max_row['row__max'], spot__exact=max_spot['spot__max']).first()
        else:
            first_empty_box = self.get_first_empty_box()
            max_row = self.filter(
                freezer__exact=first_empty_box['freezer'], rack__exact=first_empty_box['rack'],
                box__exact=(first_empty_box['box'] - 1)).aggregate(models.Max('row'))
            max_spot = self.filter(
                freezer__exact=first_empty_box['freezer'], rack__exact=first_empty_box['rack'],
                box__exact=(first_empty_box['box'] - 1), row__exact=max_row['row__max']).aggregate(models.Max('spot'))
            last_spot = self.filter(
                freezer__exact=first_empty_box['freezer'], rack__exact=first_empty_box['rack'],
                box__exact=(first_empty_box['box'] - 1), row__exact=max_row['row__max'],
                spot__exact=max_spot['spot__max']).first()

            # # # This finds the first empty box after the last occupied box, which is not what the we really want
            # # ignore all freezers that do not yet have locations used by aliquots
            # freezer_ids = list(Freezer.objects.all().order_by('id').values_list('id', flat=True))
            # freezer_id = 0
            # count_locations = 0
            # while count_locations == 0:
            #     freezer_id = freezer_ids.pop()
            #     count_locations = self.filter(freezer__exact=freezer_id).count()
            # max_freezer = Freezer.objects.filter(id=freezer_id).first()
            #
            # max_rack = self.filter(
            #     freezer__exact=max_freezer).aggregate(models.Max('rack'))
            # max_box = self.filter(
            #     freezer__exact=max_freezer, rack__exact=max_rack['rack__max']).aggregate(models.Max('box'))
            # max_row = self.filter(
            #     freezer__exact=max_freezer, rack__exact=max_rack['rack__max'],
            #     box__exact=max_box['box__max']).aggregate(models.Max('row'))
            # max_spot = self.filter(
            #     freezer__exact=max_freezer, rack__exact=max_rack['rack__max'],
            #     box__exact=max_box['box__max'], row__exact=max_row['row__max']).aggregate(models.Max('spot'))
            # last_spot = self.filter(
            #     freezer__exact=max_freezer, rack__exact=max_rack['rack__max'],
            #     box__exact=max_box['box__max'], row__exact=max_row['row__max'],
            #     spot__exact=max_spot['spot__max']).first()
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
            next_spot = self.get_next_empty_box(last_spot)
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

    # Starting with the first freezer, traverse all boxes to find the first empty box
    def get_first_empty_box(self):
        freezer_ids = list(Freezer.objects.all().order_by('id').values_list('id', flat=True))
        while len(freezer_ids) > 0:
            freezer_id = freezer_ids.pop(0)
            freezer = Freezer.objects.filter(id=freezer_id).first()
            # start building the next empty box object
            next_empty_box = {'freezer': freezer.id}
            # get dimensions of a box being used in the freezer that contains the current model instance (record)
            rows_in_box = freezer.rows
            spots_in_row = freezer.spots
            spots_in_box = rows_in_box * spots_in_row

            # start with the first box in the first rack of this freezer then increment until an empty box is found
            cur_rack = 1
            cur_box = 1
            while cur_rack <= freezer.racks:
                while cur_box <= freezer.boxes:
                    # get the initial spot in the box
                    first_spot = self.filter(freezer=freezer_id, rack=cur_rack, box=cur_box, row=1, spot=1).first()
                    # if this box is empty (does not exit), return it, otherwise continue to the next box
                    if not first_spot:
                        next_empty_box['rack'] = cur_rack
                        next_empty_box['box'] = cur_box
                        next_empty_box['row'] = 1
                        next_empty_box['spot'] = 1
                        next_empty_box['available_spots_in_box'] = spots_in_box
                        return next_empty_box
                    else:
                        cur_box += 1
                cur_rack += 1

    # get the next box with no occupied spots after a specified spot
    def get_next_empty_box(self, last_spot):
        # start building the next empty box object
        next_empty_box = {'freezer': last_spot.freezer.id}

        # get dimensions of a box being used in the freezer that contains the current model instance (record)
        rows_in_box = last_spot.freezer.rows
        spots_in_row = last_spot.freezer.spots
        spots_in_box = rows_in_box * spots_in_row

        # start with the first box in the first rack of this freezer then increment until an empty box is found
        cur_rack = last_spot.rack
        cur_box = last_spot.box
        while cur_rack <= last_spot.freezer.racks:
            while cur_box <= last_spot.freezer.boxes:
                # get the initial spot in the box
                first_spot = self.filter(
                    freezer=last_spot.freezer.id, rack=cur_rack, box=cur_box, row=1, spot=1).first()
                # if this box is empty (does not exit), return it, otherwise continue to the next box
                if not first_spot:
                    next_empty_box['rack'] = cur_rack
                    next_empty_box['box'] = cur_box
                    next_empty_box['row'] = 1
                    next_empty_box['spot'] = 1
                    next_empty_box['available_spots_in_box'] = spots_in_box
                    return next_empty_box
                else:
                    cur_box += 1
            cur_rack += 1
        # return None if no last spot was found or adding a rack will exceed the number of racks allowed in any freezer
        return None


class FreezerLocation(HistoryModel):
    """
    Freezer Location
    """

    freezer = models.ForeignKey('Freezer', models.PROTECT, related_name='freezerlocations')
    rack = NonnegativeIntegerField()
    box = NonnegativeIntegerField()
    row = NonnegativeIntegerField()
    spot = NonnegativeIntegerField()
    objects = FreezerLocationManager()

    def __str__(self):
        return str(self.id)

    class Meta:
        db_table = "lide_freezerlocation"
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

    sample = models.OneToOneField('Sample', models.CASCADE, related_name='finalconcentratedsamplevolume')
    concentration_type = models.ForeignKey(
        'ConcentrationType', models.PROTECT, related_name='finalconcentratedsamplevolumes')
    final_concentrated_sample_volume = models.DecimalField(
        max_digits=120, decimal_places=100, validators=[MINVAL_DECIMAL_100])
    notes = models.TextField(blank=True)

    # override the save method to check if a rep calc value changed,
    # and if so, recalc rep conc and rep invalid and FSMC
    def save(self, *args, **kwargs):

        # do_recalc_reps = False
        #
        # # a value can only be changed if the instance already exists
        # if self.pk:
        #     old_fcsv = FinalConcentratedSampleVolume.objects.get(id=self.pk)
        #     if self.final_concentrated_sample_volume != old_fcsv.final_concentrated_sample_volume:
        #         do_recalc_reps = True

        super(FinalConcentratedSampleVolume, self).save(*args, **kwargs)

        # if do_recalc_reps:
        #     recalc_reps('Sample', self.sample.id)

        # ALWAYS recalc child PCR Replicates
        recalc_reps('Sample', self.sample.id)

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
    def result(self):
        value = self.final_sample_mean_concentration
        if value is None:
            return "No Result"
        elif value == Decimal('0'):
            return "Negative"
        elif value > Decimal('0'):
            return "Positive"
        else:
            return "No Result"

    @property
    def final_sample_mean_concentration_sci(self):
        return get_sci_val(self.final_sample_mean_concentration)

    @property
    def sample_target_replicates(self):

        def make_rep_identifier_object(rep_obj):
            identifier_obj = {
                "id": rep_obj.id,
                "analysis_batch": rep_obj.pcrreplicate_batch.extraction_batch.analysis_batch.id,
                "extraction_number": rep_obj.pcrreplicate_batch.extraction_batch.extraction_number,
                "replicate_number": rep_obj.pcrreplicate_batch.replicate_number
            }
            return identifier_obj

        total_count = 0
        invalid_override_invalids = []
        qpcr_results_missing = []
        concentration_calc_values_missing = []
        positive_concentrations = []
        negative_concentrations = []
        controls_invalids = []
        redones = []
        invalid_override_invalid_count = 0
        qpcr_results_missing_count = 0
        concentration_calc_values_missing_count = 0
        positive_concentration_count = 0
        negative_concentration_count = 0
        controls_invalid_count = 0
        redone_count = 0

        reps = PCRReplicate.objects.filter(sample_extraction__sample=self.sample.id,
                                           pcrreplicate_batch__target__exact=self.target)
        for rep in reps:
            total_count += 1
            # ignore 'redones' (batches that have been redone)
            # in other words, only allow reps for batches that have not been redone
            if rep.pcrreplicate_batch.re_pcr is None:
                if rep.invalid is False:
                    if rep.invalid_override:
                        invalid_override_invalid_count += 1
                        invalid_override_invalids.append(make_rep_identifier_object(rep))
                    elif rep.replicate_concentration is None:
                        concentration_calc_values_missing_count += 1
                        concentration_calc_values_missing.append(make_rep_identifier_object(rep))
                    elif rep.replicate_concentration > Decimal('0'):
                        positive_concentration_count += 1
                        positive_concentrations.append(make_rep_identifier_object(rep))
                    else:
                        # a replicate_concentration less than zero is impossible due to the model field definition
                        negative_concentration_count += 1
                        negative_concentrations.append(make_rep_identifier_object(rep))
                else:
                    if rep.cq_value is None:
                        qpcr_results_missing_count += 1
                        qpcr_results_missing.append(make_rep_identifier_object(rep))
                        invalid_reasons = rep.invalid_reasons
                        invalid_reasons.pop('cq_value_missing')
                        invalid_reasons.pop('gc_reaction_missing')
                        if any(val for val in invalid_reasons.values() if val is True):
                            controls_invalid_count += 1
                            controls_invalids.append(make_rep_identifier_object(rep))
                    else:
                        # a cq_value less than zero is impossible due to the model field definition
                        # so this rep could only be invalid if a parent control invalidated it
                        # or if the user overrode the validation
                        invalid_reasons = rep.invalid_reasons
                        invalid_reasons.pop('cq_value_missing')
                        invalid_reasons.pop('gc_reaction_missing')
                        if any(val for val in invalid_reasons.values() if val is True):
                            controls_invalid_count += 1
                            controls_invalids.append(make_rep_identifier_object(rep))
            else:
                redone_count += 1
                redones.append(make_rep_identifier_object(rep))

        data = {
            "invalid_override_invalid_count": invalid_override_invalid_count,
            "invalid_override_invalids": invalid_override_invalids,
            "qpcr_results_missing_count": qpcr_results_missing_count,
            "qpcr_results_missing": qpcr_results_missing,
            "concentration_calc_values_missing_count": concentration_calc_values_missing_count,
            "concentration_calc_values_missing": concentration_calc_values_missing,
            "positive_concentration_count": positive_concentration_count,
            "positive_concentrations": positive_concentrations,
            "negative_concentration_count": negative_concentration_count,
            "negative_concentrations": negative_concentrations,
            "controls_invalid_count": controls_invalid_count,
            "controls_invalids": controls_invalids,
            "redone_count": redone_count,
            "redones": redones
        }
        return data

    final_sample_mean_concentration = NullableNonnegativeDecimalField120100()
    sample = models.ForeignKey('Sample', models.CASCADE, related_name='finalsamplemeanconcentrations')
    target = models.ForeignKey('Target', models.PROTECT, related_name='finalsamplemeanconcentrations')

    # Calculate sample mean concentration for all samples whose target replicates are now in the database and all valid
    # Concentrations from replicates are used to determine the Mean Sample Concentration
    # by taking the average of positive replicates (negative replicates (value of "0") are ignored).
    # If all replicates are negative ("0"), then the Mean Sample Concentration is "0".
    def calc_sample_mean_conc(self):
        sample_target_replicates = self.sample_target_replicates

        if (sample_target_replicates['invalid_override_invalid_count'] == 0
                and sample_target_replicates['qpcr_results_missing_count'] == 0
                and sample_target_replicates['concentration_calc_values_missing_count'] == 0
                and sample_target_replicates['controls_invalid_count'] == 0):

            pos_reps_count = sample_target_replicates['positive_concentration_count']
            if pos_reps_count > 0:
                rep_ids = [rep['id'] for rep in sample_target_replicates['positive_concentrations']]
                pos_replicate_concentrations = list(PCRReplicate.objects.filter(
                    id__in=rep_ids).values_list(
                    'replicate_concentration', flat=True))
                return sum(pos_replicate_concentrations) / pos_reps_count
            else:
                if sample_target_replicates['negative_concentration_count'] > 0:
                    return 0
                else:
                    return None
        else:
            return None

    def __str__(self):
        return str(self.id)

    class Meta:
        db_table = "lide_finalsamplemeanconcentration"
        unique_together = ("sample", "target")
        ordering = ['sample', 'id']


######
#
#  Sample Groups
#
######


class SampleSampleGroup(HistoryModel):
    """
    Table to allow many-to-many relationship between SampleGroups and Samples.
    """

    sample = models.ForeignKey('Sample', models.CASCADE)
    samplegroup = models.ForeignKey('SampleGroup', models.CASCADE)

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

    sample = models.ForeignKey('Sample', models.CASCADE)
    analysis_batch = models.ForeignKey('AnalysisBatch', models.CASCADE)

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

    target = models.ForeignKey('Target', models.PROTECT, related_name='analysisbatchtemplates')
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

    analysis_batch = models.ForeignKey('AnalysisBatch', models.CASCADE, related_name='extractionbatches')
    extraction_method = models.ForeignKey('ExtractionMethod', models.CASCADE, related_name='extractionbatches')
    re_extraction = models.ForeignKey('self', on_delete=models.CASCADE, null=True, related_name='extractionbatches')
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
    ext_pos_dna_cq_value = NullableNonnegativeDecimalField2010()
    ext_pos_dna_invalid = models.BooleanField(default=True)
    inh_pos_cq_value = NullableNonnegativeDecimalField2010()
    inh_pos_nucleic_acid_type = models.ForeignKey('NucleicAcidType', models.PROTECT, null=True)

    # override the save method to calculate invalid flag
    # and to check if a rep calc value changed, and if so, recalc rep conc and rep invalid and FSMC
    def save(self, *args, **kwargs):
        # assess the invalid flag
        # invalid flag defaults to True (i.e., the extraction batch is invalid)
        # and can only be set to False if the cq_value of this extraction batch is greater than zero
        self.ext_pos_dna_invalid = True
        if self.ext_pos_dna_cq_value is not None and self.ext_pos_dna_cq_value > 0:
            self.ext_pos_dna_invalid = False

        # do_recalc_reps = False
        # is_new = False if self.pk else True

        # # a value can only be changed if the instance already exists
        # if not is_new:
        #     old_extraction_batch = ExtractionBatch.objects.get(id=self.pk)
        #     if self.qpcr_reaction_volume != old_extraction_batch.qpcr_reaction_volume:
        #         do_recalc_reps = True
        #     if self.qpcr_template_volume != old_extraction_batch.qpcr_template_volume:
        #         do_recalc_reps = True
        #     if self.elution_volume != old_extraction_batch.elution_volume:
        #         do_recalc_reps = True
        #     if self.extraction_volume != old_extraction_batch.extraction_volume:
        #         do_recalc_reps = True
        #     if self.sample_dilution_factor != old_extraction_batch.sample_dilution_factor:
        #         do_recalc_reps = True

        super(ExtractionBatch, self).save(*args, **kwargs)

        # # Invalidate all child PCR Replicates if this (their parent Extraction Batch) is invalid
        # if self.ext_pos_dna_invalid and not is_new:
        #     PCRReplicate.objects.filter(sample_extraction__extraction_batch=self.id).update(invalid=True)
        #     do_recalc_reps = True

        # if not is_new:
        #     recalc_reps('ExtractionBatch', self.id)

        # ALWAYS recalc child PCR Replicates
        recalc_reps('ExtractionBatch', self.id)

    def __str__(self):
        return self.extraction_string

    class Meta:
        db_table = "lide_extractionbatch"
        unique_together = ("analysis_batch", "extraction_number", "re_extraction")
        verbose_name_plural = "extractionbatches"


class ReverseTranscription(HistoryModel):
    """
    Reverse Transcription
    """

    extraction_batch = models.ForeignKey('ExtractionBatch', models.CASCADE, related_name='reversetranscriptions')
    template_volume = models.DecimalField(
        max_digits=20, decimal_places=10, default=8.6, validators=[MINVAL_ZERO])
    reaction_volume = models.DecimalField(
        max_digits=20, decimal_places=10, default=50, validators=[MINVAL_DECIMAL_10])
    rt_date = models.DateField(default=date.today, null=True, blank=True, db_index=True)
    re_rt = models.ForeignKey('self', on_delete=models.CASCADE, null=True, related_name='reversetranscriptions')
    re_rt_notes = models.TextField(blank=True)
    ext_pos_rna_rt_cq_value = NullableNonnegativeDecimalField2010()
    ext_pos_rna_rt_invalid = models.BooleanField(default=True)

    # override the save method to calculate invalid flag
    def save(self, *args, **kwargs):
        # assess the invalid flag
        # invalid flag defaults to True (i.e., the RT is invalid)
        # and can only be set to False if the cq_value of this RT batch is greater than zero
        self.ext_pos_rna_rt_invalid = True
        if self.ext_pos_rna_rt_cq_value is not None and self.ext_pos_rna_rt_cq_value > 0:
            self.ext_pos_rna_rt_invalid = False

        # do_recalc_reps = False
        # is_new = False if self.pk else True
        super(ReverseTranscription, self).save(*args, **kwargs)

        # # Invalidate all child PCR Replicates if this (their parent RT) is invalid
        # if self.ext_pos_rna_rt_invalid and not is_new:
        #     PCRReplicate.objects.filter(
        #         sample_extraction__extraction_batch=self.extraction_batch.id).update(invalid=True)
        #     do_recalc_reps = True

        # if do_recalc_reps:
        #     recalc_reps('ExtractionBatch', self.extraction_batch.id)

        # ALWAYS recalc child PCR Replicates
        recalc_reps('ExtractionBatch', self.extraction_batch.id)

    def __str__(self):
        return str(self.id)

    class Meta:
        db_table = "lide_reversetranscription"
        unique_together = ("extraction_batch", "re_rt")


class SampleExtraction(HistoryModel):
    """
    Sample Extraction
    """

    sample = models.ForeignKey('Sample', models.CASCADE, related_name='sampleextractions')
    extraction_batch = models.ForeignKey('ExtractionBatch', models.CASCADE, related_name='sampleextractions')
    inhibition_dna = models.ForeignKey('Inhibition', models.CASCADE, null=True, related_name='sampleextractionsdna')
    inhibition_rna = models.ForeignKey('Inhibition', models.CASCADE, null=True, related_name='sampleextractionsrna')

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

    extraction_batch = models.ForeignKey('ExtractionBatch', models.CASCADE, related_name='pcrreplicatebatches')
    target = models.ForeignKey('Target', models.PROTECT, related_name='pcrreplicatebatches')
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
    re_pcr = models.ForeignKey('self', on_delete=models.CASCADE, null=True, related_name='pcrreplicatebatches')

    # override the save method to calculate invalid flags
    # and to check if a rep calc value changed, and if so, recalc rep conc and rep invalid and FSMC
    def save(self, *args, **kwargs):
        # assess the invalid flags
        # invalid flags default to True (i.e., the rep is invalid)
        # and can only be set to False if the cq_values of this rep batch are equal to zero

        # also, if any negative controls are positive (have a cq_value greater than zero),
        # not only the child reps of this rep batch need to be invalidated,
        # but also all the child repsof the parent extraction batch need to be invalidated.
        invalidate_reps = False
        self.ext_neg_invalid = False if self.ext_neg_cq_value == Decimal('0') else True
        self.pcr_neg_invalid = False if self.pcr_neg_cq_value == Decimal('0') else True
        if self.ext_neg_cq_value is not None and self.ext_neg_cq_value > Decimal('0'):
            invalidate_reps = True
        if self.pcr_neg_cq_value is not None and self.pcr_neg_cq_value > Decimal('0'):
            invalidate_reps = True

        # rt_neg is a special case that only applies if the target is RNA,
        # and even then not every extraction batch will have a RT,
        # so if there is no RT, set rt_neg_invalid to False regardless of the value of rt_neg_cq_value,
        # but if there is a RT, apply the same logic as the other invalid flags
        self.rt_neg_invalid = False
        if self.target.nucleic_acid_type.name.upper() == 'RNA':
            rt = ReverseTranscription.objects.filter(extraction_batch=self.extraction_batch.id, re_rt=None).first()
            self.rt_neg_invalid = False if rt and self.rt_neg_cq_value == Decimal('0') else True
            if self.rt_neg_cq_value is not None and self.rt_neg_cq_value > Decimal('0'):
                invalidate_reps = True

        # validating the pcr_pos will come in a later release of the software
        # sc = validated_data.get('standard_curve', None)
        self.pcr_pos_invalid = False

        # do_recalc_reps = False
        #
        # # a value can only be changed if the instance already exists
        # if self.pk:
        #     old_pcrreplicate_batch = PCRReplicateBatch.objects.get(id=self.pk)
        #     if self.target.id != old_pcrreplicate_batch.target.id:
        #         do_recalc_reps = True

        super(PCRReplicateBatch, self).save(*args, **kwargs)

        # if do_recalc_reps:
        #     recalc_reps('PCRReplicateBatch', self.id)

        # invalidate child PCR Replicates of parent Extraction Batch if any negative control is positive
        if invalidate_reps:
            PCRReplicate.objects.filter(
                sample_extraction__extraction_batch=self.extraction_batch.id).update(invalid=True)

        # ALWAYS recalc child PCR Replicates
        recalc_reps('PCRReplicateBatch', self.id)

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

    @property
    def invalid_reasons(self):
        reasons = {}
        if self.invalid:
            pcrreplicate_batch = PCRReplicateBatch.objects.filter(id=self.pcrreplicate_batch.id).first()
            # first check related peg_neg validity
            # assume no related peg_neg, in which case this control does not apply
            # but if there is a related peg_neg, check the validity of its reps with same target as this data rep
            peg_neg_missings = []
            peg_neg_invalids = []
            peg_neg_not_extracted = False
            sample = self.sample_extraction.sample

            # record_type 1 means regular data (not a control), record_type 2 means control data (not regular data)
            # only a regular data sample can potentially have a peg_neg control
            # the inverse (a control data sample having a peg_neg control) is impossible
            peg_neg_id = sample.peg_neg.id if sample.peg_neg is not None and sample.record_type.id == 1 else None
            if peg_neg_id is not None:
                target_id = pcrreplicate_batch.target.id
                # only get reps with the same target as this data rep
                peg_neg_rep_count = PCRReplicate.objects.filter(
                    sample_extraction__sample=peg_neg_id, pcrreplicate_batch__target__exact=target_id).count()
                # if there are no peg_neg reps, the the data rep must be set to invalid
                if peg_neg_rep_count == 0:
                    peg_neg_not_extracted = True
                peg_neg_invalids = PCRReplicate.objects.filter(sample_extraction__sample=peg_neg_id,
                                                               pcrreplicate_batch__target__exact=target_id,
                                                               invalid=True, cq_value__isnull=False).annotate(
                    sample=F('sample_extraction__sample')).annotate(
                    analysis_batch=F('pcrreplicate_batch__extraction_batch__analysis_batch')).annotate(
                    extraction_number=F('pcrreplicate_batch__extraction_batch__extraction_number')).annotate(
                    replicate_number=F('pcrreplicate_batch__replicate_number')).annotate(
                    target=F('pcrreplicate_batch__target')
                ).values('sample', 'analysis_batch', 'extraction_number', 'replicate_number', 'target')
                peg_neg_missings = PCRReplicate.objects.filter(sample_extraction__sample=peg_neg_id,
                                                               pcrreplicate_batch__target__exact=target_id,
                                                               cq_value__isnull=True).annotate(
                    sample=F('sample_extraction__sample')).annotate(
                    analysis_batch=F('pcrreplicate_batch__extraction_batch__analysis_batch')).annotate(
                    extraction_number=F('pcrreplicate_batch__extraction_batch__extraction_number')).annotate(
                    replicate_number=F('pcrreplicate_batch__replicate_number')).annotate(
                    target=F('pcrreplicate_batch__target')
                ).values('sample', 'analysis_batch', 'extraction_number', 'replicate_number', 'target')

            # Parent PegNeg Controls

            if peg_neg_not_extracted:
                reasons["peg_neg_not_extracted"] = True
            else:
                reasons["peg_neg_not_extracted"] = False
            if len(peg_neg_invalids) > 0:
                reasons["peg_neg_reps_invalid"] = True
                reasons["peg_neg_reps_invalid_list"] = list(peg_neg_invalids)
            else:
                reasons["peg_neg_reps_invalid"] = False
                reasons["peg_neg_reps_invalid_list"] = ""
            if len(peg_neg_missings) > 0:
                reasons["peg_neg_reps_missing"] = True
                reasons["peg_neg_reps_missing_list"] = list(peg_neg_missings)
            else:
                reasons["peg_neg_reps_missing"] = False
                reasons["peg_neg_reps_missing_list"] = ""

            # then check all other controls applicable to this rep

            # Parent ExtractionBatch Controls

            # ext_pos_dna is a special case that only applies if the target of the pcrreplicate_batch is RNA
            if pcrreplicate_batch.target.nucleic_acid_type.name.upper() == 'DNA':
                if pcrreplicate_batch.extraction_batch.ext_pos_dna_cq_value is None:
                    reasons["ext_pos_dna_missing"] = True
                else:
                    reasons["ext_pos_dna_missing"] = False
                if (pcrreplicate_batch.extraction_batch.ext_pos_dna_cq_value is not None
                        and not pcrreplicate_batch.extraction_batch.ext_pos_dna_cq_value > Decimal('0')):
                    reasons["ext_pos_dna_invalid"] = True
                else:
                    reasons["ext_pos_dna_invalid"] = False
            else:
                reasons["ext_pos_dna_missing"] = False
                reasons["ext_pos_dna_invalid"] = False
            # ext_pos_rt_rna is a special case that only applies if the target of the pcrreplicate_batch is RNA
            if pcrreplicate_batch.target.nucleic_acid_type.name.upper() == 'RNA':
                rt = ReverseTranscription.objects.filter(
                    extraction_batch=pcrreplicate_batch.extraction_batch.id, re_rt=None).first()
                if rt and rt.ext_pos_rna_rt_cq_value is None:
                    reasons["ext_rt_pos_rna_missing"] = True
                else:
                    reasons["ext_rt_pos_rna_missing"] = False
                if rt and rt.ext_pos_rna_rt_cq_value is not None and not rt.ext_pos_rna_rt_cq_value > Decimal('0'):
                    reasons["ext_rt_pos_rna_invalid"] = True
                else:
                    reasons["ext_rt_pos_rna_invalid"] = False
            else:
                reasons["ext_rt_pos_rna_missing"] = False
                reasons["ext_rt_pos_rna_invalid"] = False

            # Parent Sibling PCRReplicateBatch Controls

            ext_neg_invalids = PCRReplicateBatch.objects.filter(
                extraction_batch=pcrreplicate_batch.extraction_batch.id,
                target=pcrreplicate_batch.target.id,
                ext_neg_invalid=True,
                ext_neg_cq_value__isnull=False
            ).exclude(id=pcrreplicate_batch.id
                      ).annotate(analysis_batch=F('extraction_batch__analysis_batch')
                                 ).annotate(extraction_number=F('extraction_batch__extraction_number')
                                            ).values('analysis_batch', 'extraction_number', 'replicate_number',
                                                     'target')
            ext_neg_missings = PCRReplicateBatch.objects.filter(
                extraction_batch=pcrreplicate_batch.extraction_batch.id,
                target=pcrreplicate_batch.target.id,
                ext_neg_cq_value__isnull=True
            ).exclude(id=pcrreplicate_batch.id).annotate(analysis_batch=F('extraction_batch__analysis_batch')
                                                         ).annotate(
                extraction_number=F('extraction_batch__extraction_number')
            ).values('analysis_batch', 'extraction_number', 'replicate_number', 'target')

            # rt_neg is a special case that only applies if the target of the pcrreplicate_batch is RNA
            if self.pcrreplicate_batch.target.nucleic_acid_type.id == 2:
                rt_neg_invalids = PCRReplicateBatch.objects.filter(
                    extraction_batch=pcrreplicate_batch.extraction_batch.id,
                    target=pcrreplicate_batch.target.id,
                    rt_neg_invalid=True,
                    rt_neg_cq_value__isnull=False,
                    target__nucleic_acid_type=2
                ).exclude(id=pcrreplicate_batch.id).annotate(analysis_batch=F('extraction_batch__analysis_batch')
                                                             ).annotate(
                    extraction_number=F('extraction_batch__extraction_number')
                    ).values('analysis_batch', 'extraction_number', 'replicate_number', 'target')
                rt_neg_missings = PCRReplicateBatch.objects.filter(
                    extraction_batch=pcrreplicate_batch.extraction_batch.id,
                    target=pcrreplicate_batch.target.id,
                    rt_neg_cq_value__isnull=True,
                    target__nucleic_acid_type=2
                ).exclude(id=pcrreplicate_batch.id).annotate(analysis_batch=F('extraction_batch__analysis_batch')
                                                             ).annotate(
                    extraction_number=F('extraction_batch__extraction_number')
                ).values('analysis_batch', 'extraction_number', 'replicate_number', 'target')
            else:
                rt_neg_invalids = PCRReplicateBatch.objects.none()
                rt_neg_missings = PCRReplicateBatch.objects.none()

            pcr_neg_invalids = PCRReplicateBatch.objects.filter(
                extraction_batch=pcrreplicate_batch.extraction_batch.id,
                target=pcrreplicate_batch.target.id,
                pcr_neg_invalid=True,
                pcr_neg_cq_value__isnull=False
            ).exclude(id=pcrreplicate_batch.id).annotate(analysis_batch=F('extraction_batch__analysis_batch')
                                                         ).annotate(
                extraction_number=F('extraction_batch__extraction_number')
            ).values('analysis_batch', 'extraction_number', 'replicate_number', 'target')
            pcr_neg_missings = PCRReplicateBatch.objects.filter(
                extraction_batch=pcrreplicate_batch.extraction_batch.id,
                target=pcrreplicate_batch.target.id,
                pcr_neg_cq_value__isnull=True
            ).exclude(id=pcrreplicate_batch.id).annotate(analysis_batch=F('extraction_batch__analysis_batch')
                                                         ).annotate(
                extraction_number=F('extraction_batch__extraction_number')
            ).values('analysis_batch', 'extraction_number', 'replicate_number', 'target')

            if len(ext_neg_invalids) > 0 or len(rt_neg_invalids) > 0 or len(pcr_neg_invalids) > 0:
                reasons["sibling_pcr_rep_controls_invalid"] = True
                reasons["sibling_pcr_rep_controls_invalid_list"] = list(
                    ext_neg_invalids.union(rt_neg_invalids).union(pcr_neg_invalids))
            else:
                reasons["sibling_pcr_rep_controls_invalid"] = False
                reasons["sibling_pcr_rep_controls_invalid_list"] = ""
            if len(ext_neg_missings) > 0 or len(rt_neg_missings) > 0 or len(pcr_neg_missings) > 0:
                reasons["sibling_pcr_rep_controls_missing"] = True
                reasons["sibling_pcr_rep_controls_missing_list"] = list(
                    ext_neg_missings.union(rt_neg_missings).union(pcr_neg_missings))
            else:
                reasons["sibling_pcr_rep_controls_missing"] = False
                reasons["sibling_pcr_rep_controls_missing_list"] = ""

            # Parent PCRReplicateBatch Controls

            if pcrreplicate_batch.ext_neg_cq_value is None:
                reasons["ext_neg_missing"] = True
            else:
                reasons["ext_neg_missing"] = False
            if pcrreplicate_batch.ext_neg_cq_value is not None and pcrreplicate_batch.ext_neg_cq_value > Decimal('0'):
                reasons["ext_neg_invalid"] = True
            else:
                reasons["ext_neg_invalid"] = False
            # rt_neg is a special case that only applies if the target of the pcrreplicate_batch is RNA
            if pcrreplicate_batch.rt_neg_invalid:
                if pcrreplicate_batch.rt_neg_cq_value is None:
                    reasons["rt_neg_missing"] = True
                else:
                    reasons["rt_neg_missing"] = False
                if pcrreplicate_batch.rt_neg_cq_value is not None and pcrreplicate_batch.rt_neg_cq_value > Decimal('0'):
                    reasons["rt_neg_invalid"] = True
                else:
                    reasons["rt_neg_invalid"] = False
            else:
                reasons["rt_neg_missing"] = False
                reasons["rt_neg_invalid"] = False
            if pcrreplicate_batch.pcr_neg_cq_value is None:
                reasons["pcr_neg_missing"] = True
            else:
                reasons["pcr_neg_missing"] = False
            if pcrreplicate_batch.pcr_neg_cq_value is not None and pcrreplicate_batch.pcr_neg_cq_value > Decimal('0'):
                reasons["pcr_neg_invalid"] = True
            else:
                reasons["pcr_neg_invalid"] = False

            # Self Values

            if self.cq_value is None:
                reasons["cq_value_missing"] = True
            else:
                reasons["cq_value_missing"] = False
            if self.gc_reaction is None:
                reasons["gc_reaction_missing"] = True
            else:
                reasons["gc_reaction_missing"] = False
            if self.invalid_override is not None:
                reasons["invalid_override"] = True
            else:
                reasons["invalid_override"] = False

        else:
            reasons = {
                "peg_neg_not_extracted": False,
                "peg_neg_reps_invalid": False, "peg_neg_reps_invalid_list": False,
                "peg_neg_reps_missing": False, "peg_neg_reps_missing_list": False,
                "ext_pos_dna_missing": False, "ext_pos_dna_invalid": False,
                "ext_rt_pos_rna_missing": False, "ext_rt_pos_rna_invalid": False,
                "sibling_pcr_rep_controls_invalid": False, "sibling_pcr_rep_controls_invalid_list": False,
                "sibling_pcr_rep_controls_missing": False, "sibling_pcr_rep_controls_missing_list": False,
                "ext_neg_missing": False, "ext_neg_invalid": False,
                "rt_neg_missing": False, "rt_neg_invalid": False,
                "pcr_neg_missing": False, "pcr_neg_invalid": False,
                "cq_value_missing": False, "gc_reaction_missing": False,
                "invalid_override": False
            }

        return reasons

    @property
    def missing_calculation_values(self):
        values = {}
        sample = self.sample_extraction.sample
        if self.inhibition_dilution_factor is None:
            values["inhibition_dilution_factor"] = True
        else:
            values["inhibition_dilution_factor"] = False
        if sample.matrix.code in ['F', 'W', 'WW']:
            fcsv = FinalConcentratedSampleVolume.objects.filter(sample=sample.id).first()
            if not fcsv or fcsv.final_concentrated_sample_volume is None:
                values["final_concentrated_sample_volume"] = True
            else:
                values["final_concentrated_sample_volume"] = False
        else:
            values["final_concentrated_sample_volume"] = False
        if sample.matrix.code == 'A' and sample.dissolution_volume is None:
            values["sample dissolution_volume"] = True
        else:
            values["sample dissolution_volume"] = False
        if sample.matrix.code == 'SM' and sample.post_dilution_volume is None:
            values["sample post_dilution_volume"] = True
        else:
            values["sample post_dilution_volume"] = False
        return values

    @property
    def inhibition(self):
        sample_extraction = self.sample_extraction
        nucleic_acid_type_name = self.pcrreplicate_batch.target.nucleic_acid_type.name.upper()
        if nucleic_acid_type_name == 'DNA':
            inhibition_id = sample_extraction.inhibition_dna.id
        elif nucleic_acid_type_name == 'RNA':
            inhibition_id = sample_extraction.inhibition_rna.id
        else:
            inhibition_id = None
        data = {
            "id": inhibition_id,
            "sample": self.sample_extraction.sample.id,
            "analysis_batch": self.pcrreplicate_batch.extraction_batch.analysis_batch.id,
            "extraction_number": self.pcrreplicate_batch.extraction_batch.extraction_number,
            "nucleic_acid_type": nucleic_acid_type_name
        }
        return data

    @property
    def inhibition_dilution_factor(self):
        sample_extraction = self.sample_extraction
        nucleic_acid_type_name = self.pcrreplicate_batch.target.nucleic_acid_type.name.upper()
        if nucleic_acid_type_name == 'DNA':
            data = sample_extraction.inhibition_dna.dilution_factor
        elif nucleic_acid_type_name == 'RNA':
            data = sample_extraction.inhibition_rna.dilution_factor
        else:
            data = None
        return data

    @property
    def calculation_values(self):
        eb = self.sample_extraction.extraction_batch
        samp = self.sample_extraction.sample
        fcsv = FinalConcentratedSampleVolume.objects.filter(sample=samp.id).first()
        calc_vals = {
            "nucleic_acid_type_name": self.pcrreplicate_batch.target.nucleic_acid_type.name,
            "matrix_code": samp.matrix.code,
            "qpcr_reaction_volume": eb.qpcr_reaction_volume,
            "qpcr_template_volume": eb.qpcr_template_volume,
            "elution_volume": eb.elution_volume,
            "extraction_volume": eb.extraction_volume,
            "sample_dilution_factor": eb.sample_dilution_factor,
            "inhibition_dilution_factor": self.inhibition_dilution_factor,
            "total_volume_or_mass_sampled": samp.total_volume_or_mass_sampled,
            "final_concentrated_sample_volume": fcsv.final_concentrated_sample_volume if fcsv else None,
            "dissolution_volume": samp.dissolution_volume,
            "post_dilution_volume": samp.post_dilution_volume
        }
        # final_concentrated_sample_volume = FinalConcentratedSampleVolume.objects.values_list(
        #     'final_concentrated_sample_volume', flat=True).get(sample=self.sample_extraction.sample.id)
        return calc_vals

    sample_extraction = models.ForeignKey('SampleExtraction', models.CASCADE, related_name='pcrreplicates')
    pcrreplicate_batch = models.ForeignKey('PCRReplicateBatch', models.CASCADE, related_name='pcrreplicates')
    cq_value = NullableNonnegativeDecimalField2010()
    gc_reaction = NullableNonnegativeDecimalField120100()
    replicate_concentration = models.DecimalField(
        max_digits=120, decimal_places=100, null=True, blank=True, validators=[MINVAL_DECIMAL_100])
    concentration_unit = models.ForeignKey('Unit', models.PROTECT, related_name='pcrreplicates')
    invalid = models.BooleanField(default=True)
    invalid_override = models.ForeignKey(
        settings.AUTH_USER_MODEL, models.PROTECT, null=True, related_name='pcrreplicates')
    # objects = PCRReplicateManager()

    # override the save method to assign or calculate concentration_unit, replicate_concentration, and invalid flag
    def save(self, *args, **kwargs):
        # assign the correct (and required) concentration unit value on new records
        if self.pk is None:
            self.concentration_unit = self.get_conc_unit(self.sample_extraction.sample.id)

        super(PCRReplicate, self).save(*args, **kwargs)

        # determine if all replicates for a given sample-target combo are now in the database or not
        # and calculate sample mean concentration if yes or set to null if no

        # first find a matching sample-target combo (fsmc)
        fsmc = FinalSampleMeanConcentration.objects.filter(
            sample=self.sample_extraction.sample.id, target=self.pcrreplicate_batch.target.id).first()
        # if the sample-target combo (fsmc) does not exist, create it
        if not fsmc:
            fsmc = FinalSampleMeanConcentration.objects.create(
                sample=self.sample_extraction.sample, target=self.pcrreplicate_batch.target,
                created_by=self.created_by, modified_by=self.modified_by)

        # then update final sample mean concentration
        # if all the valid related reps have replicate_concentration values the FSMC will be calculated
        # else not all valid related reps have replicate_concentration values, so FSMC will be set to null
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

    # Calculate replicate_concentration, but only if gc_reaction is a positive number
    # Equations are for determining the final concentration for a replicate.
    # Concentrations from replicates are used to determine the Mean Sample Concentration
    # by taking the average of positive replicates (negative replicates (value of "0") are ignored).
    # If all replicates are negative ("0"), then the Mean Sample Concentration is "0".
    def calc_rep_conc(self):
        # ensure that all necessary values are not null, otherwise return null
        # aside from the following, all other necessary fields are required (not nullable) at time of creation
        # all reps must have gc_reaction and inhibition_dilution_factor
        # reps with matrix F, W, or WW must have final_concentrated_sample_volume
        # reps with matrix A must have dissolution_volume
        # reps with matrix SM must have post_dilution_volume
        if self.gc_reaction is not None and self.inhibition_dilution_factor is not None:
            if self.gc_reaction > Decimal('0'):
                sample = self.sample_extraction.sample
                matrix = sample.matrix.code
                fcsv = None

                if matrix in ['F', 'W', 'WW']:
                    fcsv = FinalConcentratedSampleVolume.objects.filter(sample=sample.id).first()
                    if not fcsv or fcsv.final_concentrated_sample_volume is None:
                        return None
                elif matrix == 'A' and sample.dissolution_volume is None:
                    return None
                elif matrix == 'SM' and sample.post_dilution_volume is None:
                    return None

                nucleic_acid_type_name = self.pcrreplicate_batch.target.nucleic_acid_type.name.upper()
                extr = self.sample_extraction
                eb = self.sample_extraction.extraction_batch

                # first apply the universal expressions
                prelim_value = (self.gc_reaction / eb.qpcr_reaction_volume) * (
                        eb.qpcr_reaction_volume / eb.qpcr_template_volume) * (
                                       eb.elution_volume / eb.extraction_volume) * (
                                   eb.sample_dilution_factor)
                if nucleic_acid_type_name == 'DNA':
                    prelim_value = prelim_value * extr.inhibition_dna.dilution_factor
                # apply the RT the expression if applicable
                elif nucleic_acid_type_name == 'RNA':
                    # assume that there can be only one RT per EB, except when there is a re_rt,
                    # in which case the 'old' RT is no longer valid and would have a RT ID value in the re_rt field
                    # that references the only valid RT;
                    # in other words, the re_rt value must be null for the record to be valid
                    rt = ReverseTranscription.objects.filter(extraction_batch=eb, re_rt=None).first()
                    dl = extr.inhibition_rna.dilution_factor
                    prelim_value = prelim_value * dl * (rt.reaction_volume / rt.template_volume)
                # then apply the final volume-or-mass ratio expression (note: liquid_manure does not use this)
                if matrix in ['F', 'W', 'WW']:
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
                # a gc_reaction less than zero is impossible due to the model field definition
                return 0
        else:
            return None

    def calc_invalid(self):
        # assess the invalid flags
        # invalid flags default to True (i.e., the rep is invalid) and can only be set to False if:
        #     1. all parent controls exist
        #     2. all parent control flags are False (i.e., the controls are valid)
        #        (NOTE: **ALL** PCR Replicate Batch controls from the same parent Extraction Batch
        #        are considered parent controls for this rep, per cooperator statement July 24, 2019)
        #     3. the cq_value and gc_reaction of this rep are greater than or equal to zero
        if self.invalid_override is None:
            if self.cq_value is not None and self.gc_reaction is not None:
                pcrreplicate_batch = PCRReplicateBatch.objects.filter(id=self.pcrreplicate_batch.id).first()
                sample = Sample.objects.filter(id=self.sample_extraction.sample.id).first()

                # first check related peg_neg validity
                # assume no related peg_neg, in which case this control does not apply
                # but if there is a related peg_neg (or if the rep itself is from a peg_neg),
                # check the validity of all the parent sample's peg_neg reps with the same target as this data rep
                any_peg_neg_invalid = False
                # record_type 1 means regular data (not a control), record_type 2 means control data (not regular data)
                # only a regular data sample can potentially have a peg_neg control
                # the inverse (a control data sample having a peg_neg control) is impossible
                peg_neg_id = sample.peg_neg.id if sample.peg_neg is not None and sample.record_type.id == 1 else None
                if peg_neg_id is not None:
                    target_id = pcrreplicate_batch.target.id
                    # only check sample extractions with the same peg_neg_id as the sample of this data rep
                    # only check reps with the same target as this data rep
                    reps = PCRReplicate.objects.filter(
                        sample_extraction__sample=peg_neg_id, pcrreplicate_batch__target__exact=target_id)
                    # if even a single one of the peg_neg reps is invalid, or there are no peg_neg reps
                    # (because the peg_neg sample has not yet been extracted), the data rep must be set to invalid
                    if len(reps) > 0:
                        invalid_reps = list(PCRReplicate.objects.filter(
                            sample_extraction__sample=peg_neg_id, pcrreplicate_batch__target__exact=target_id,
                            invalid=True).values_list('id'))
                        any_peg_neg_invalid = True if len(invalid_reps) > 0 else False
                    else:
                        any_peg_neg_invalid = True

                # then check all other controls applicable to this rep
                rna_pos_invalid = False
                dna_pos_invalid = False

                # # just for debugging
                # ext_neg_invalids = PCRReplicateBatch.objects.filter(
                #     extraction_batch=pcrreplicate_batch.extraction_batch.id,
                #     target=pcrreplicate_batch.target.id).values_list('id', 'ext_neg_invalid')
                # rt_neg_invalids = PCRReplicateBatch.objects.filter(
                #     extraction_batch=pcrreplicate_batch.extraction_batch.id,
                #     target=pcrreplicate_batch.target.id).values_list('id', 'rt_neg_invalid')
                # pcr_neg_invalids = PCRReplicateBatch.objects.filter(
                #     extraction_batch=pcrreplicate_batch.extraction_batch.id,
                #     target=pcrreplicate_batch.target.id).values_list('id', 'pcr_neg_invalid')

                ext_neg_invalid = any(list(PCRReplicateBatch.objects.filter(
                    extraction_batch=pcrreplicate_batch.extraction_batch.id,
                    target=pcrreplicate_batch.target.id
                ).values_list('ext_neg_invalid', flat=True)))
                rt_neg_invalid = any(list(PCRReplicateBatch.objects.filter(
                    extraction_batch=pcrreplicate_batch.extraction_batch.id,
                    target=pcrreplicate_batch.target.id
                ).values_list('rt_neg_invalid', flat=True)))
                pcr_neg_invalid = any(list(PCRReplicateBatch.objects.filter(
                    extraction_batch=pcrreplicate_batch.extraction_batch.id,
                    target=pcrreplicate_batch.target.id
                ).values_list('pcr_neg_invalid', flat=True)))
                if pcrreplicate_batch.target.nucleic_acid_type.name.upper() == 'RNA':
                    rt = ReverseTranscription.objects.filter(
                        extraction_batch=pcrreplicate_batch.extraction_batch.id, re_rt=None).first()
                    rna_pos_invalid = rt.ext_pos_rna_rt_invalid if rt else False
                if pcrreplicate_batch.target.nucleic_acid_type.name.upper() == 'DNA':
                    dna_pos_invalid = pcrreplicate_batch.extraction_batch.ext_pos_dna_invalid
                if (
                        not any_peg_neg_invalid and
                        not dna_pos_invalid and
                        not rna_pos_invalid and
                        not ext_neg_invalid and
                        not rt_neg_invalid and
                        not pcr_neg_invalid and
                        self.cq_value is not None and self.cq_value >= Decimal('0') and
                        self.gc_reaction is not None and self.gc_reaction >= Decimal('0')
                ):
                    # this rep is valid
                    return False
                else:
                    # if the rep itself comes from a peg_neg sample, and it is invalid,
                    # then invalidate all related reps with the same target from samples using that peg_neg
                    if sample.record_type.id == 2:
                        PCRReplicate.objects.filter(
                            sample_extraction__sample__peg_neg__id=self.sample_extraction.sample.id,
                            pcrreplicate_batch__target__id=self.pcrreplicate_batch.target.id).update(invalid=True)
                    return True
            else:
                return True
        else:
            return self.invalid if self.invalid else True

    def __str__(self):
        return str(self.id)

    class Meta:
        db_table = "lide_pcrreplicate"
        unique_together = ("sample_extraction", "pcrreplicate_batch")


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

    sample = models.ForeignKey('Sample', models.CASCADE, related_name='inhibitions')
    extraction_batch = models.ForeignKey('ExtractionBatch', models.CASCADE, related_name='inhibitions')
    inhibition_date = models.DateField(default=date.today, db_index=True)
    nucleic_acid_type = models.ForeignKey('NucleicAcidType', models.PROTECT, default=1)
    cq_value = NullableNonnegativeDecimalField2010()
    dilution_factor = models.IntegerField(null=True, blank=True, validators=[MINVAL_ZERO])

    # override the save method to check if a rep calc value changed, and if so, recalc rep conc and rep invalid and FSMC
    def save(self, *args, **kwargs):

        # do_recalc_reps = False
        #
        # # a value can only be changed if the instance already exists
        # if self.pk:
        #     old_inhibition = Inhibition.objects.get(id=self.pk)
        #     if self.dilution_factor != old_inhibition.dilution_factor:
        #         do_recalc_reps = True

        super(Inhibition, self).save(*args, **kwargs)

        # if do_recalc_reps:
        #     recalc_reps('Inhibition', self.id)

        # ALWAYS recalc child PCR Replicates
        recalc_reps('Inhibition', self.id)

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
    nucleic_acid_type = models.ForeignKey('NucleicAcidType', models.PROTECT, default=1)
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
    unit = models.ForeignKey('Unit', models.PROTECT, related_name='fieldunits')

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


class ReportFile(HistoryModel):
    """
    File created and stored on the server when a report is requested
    """

    def _get_filename(self):
        """Returns the name of the file"""
        return '%s' % str(self.file).split('/')[-1]

    def reportfile_location(self, instance):
        """Returns a custom location for the report file, in a folder named for its report type"""
        return 'reports/{0}/{1}'.format(self.get_report_type_display(), instance)

    # TODO: confirm report names
    REPORT_TYPES = (
        (1, 'Inhibition',),
        (2, 'ResultsSummary',),
        (3, 'IndividualSample',),
        (4, 'QualityControl',),
        (5, 'ControlsResults',),
    )

    REPORT_STATUSES = (
        (1, 'Pending',),
        (2, 'Complete',),
        (3, 'Failed',)
    )

    name = property(_get_filename)
    file = models.FileField(upload_to=reportfile_location, null=True)
    report_type = models.IntegerField(choices=REPORT_TYPES)
    report_status = models.IntegerField(choices=REPORT_STATUSES)
    fail_reason = models.TextField(blank=True)

    def __str__(self):
        return str(self.name)

    class Meta:
        db_table = "lide_reportfile"
