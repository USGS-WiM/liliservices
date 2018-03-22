from datetime import datetime
from rest_framework import serializers
from lideservices.models import *


######
#
#  Freezer Locations
#
######


class FreezerLocationSerializer(serializers.ModelSerializer):
    created_by = serializers.StringRelatedField()
    modified_by = serializers.StringRelatedField()

    class Meta:
        model = FreezerLocation
        fields = ('id', 'freezer', 'rack', 'box', 'row', 'spot',
                  'created_date', 'created_by', 'modified_date', 'modified_by',)


class FreezerSerializer(serializers.ModelSerializer):
    created_by = serializers.StringRelatedField()
    modified_by = serializers.StringRelatedField()

    class Meta:
        model = Freezer
        fields = ('id', 'racks', 'boxes', 'rows', 'spots',
                  'created_date', 'created_by', 'modified_date', 'modified_by',)


######
#
#  Samples
#
######


class AliquotListSerializer(serializers.ListSerializer):

    # ensure either a freezer_location ID or coordinates (freezer, rack, box, row, spot) is included in request data
    def validate(self, data):
        if self.context['request'].method == 'POST':
            d = data[0]
            if 'sample' not in d:
                pass
            if 'samples' not in d:
                message = "A list of sample IDs is required"
                raise serializers.ValidationError(message)
            if 'freezer_location' not in d:
                if 'freezer' not in d or 'rack' not in d or 'box' not in d or 'row' not in d or 'spot' not in d:
                    message = "Either a freezer_location ID or coordinates (freezer, rack, box, row, spot) is required"
                    raise serializers.ValidationError(message)
        elif self.context['request'].method == 'PUT':
            is_valid = True
            details = []
            for item in data:
                if 'sample' not in item:
                    is_valid = False
                    details.append("sample is a required field")
                if 'freezer_location' not in item:
                    is_valid = False
                    details.append("freezer_location is a required field")
                if 'rack' in item or 'box' in item or 'row' in item or 'spot' in item:
                    is_valid = False
                    message = "coordinates (freezer, rack, box, row, spot) are not allowed in updates; "
                    message += "use freezer_location ID instead"
                    details.append(message)
                if 'aliquot_number' not in item or item['aliquot_number'] == 0:
                    details.append("aliquot_number is a required field")
            if not is_valid:
                raise serializers.ValidationError(details)
        return data

    # bulk create
    def create(self, validated_data):
        validated_data = validated_data[0]

        # pull out the freezer location fields from the request
        if 'freezer_location' in validated_data:
            freezer_location_id = validated_data['freezer_location'].id
            freezer_location = FreezerLocation.objects.filter(id=freezer_location_id).first()
            if freezer_location:
                freezer = freezer_location.freezer.id
                rack = freezer_location.rack
                box = freezer_location.box
                row = freezer_location.row
                spot = freezer_location.spot
            else:
                raise serializers.ValidationError("No Freezer Location exists with ID: " + str(freezer_location_id))
        else:
            freezer = validated_data.pop('freezer')
            rack = validated_data.pop('rack')
            box = validated_data.pop('box')
            row = validated_data.pop('row')
            spot = validated_data.pop('spot')

        # pull out aliquot count from the request
        if 'aliquot_count' in validated_data:
            aliquot_count = validated_data.pop('aliquot_count')
        else:
            aliquot_count = 1

        # pull out sample IDs from the request
        sample_ids = validated_data.pop('samples')

        aliquots = []
        sample_count = 0
        freezer_object = Freezer.objects.filter(id=freezer).first()
        for sample_id in sample_ids:
            sample = Sample.objects.get(id=sample_id)
            for count_num in range(0, aliquot_count):
                validated_data['sample'] = sample

                # first determine if any aliquots exist for the parent sample
                prev_aliquots = Aliquot.objects.filter(sample=sample_id)
                if prev_aliquots:
                    max_aliquot_number = max(prev_aliquot.aliquot_number for prev_aliquot in prev_aliquots)
                else:
                    max_aliquot_number = 0
                # then assign the proper aliquot_number
                validated_data['aliquot_number'] = max_aliquot_number + 1

                # next create the freezer location for this aliquot to use
                # use the existing freezer location if it was submitted and the aliquot count is exactly 1
                if 'freezer_location' in validated_data and len(sample_ids) == 1 and aliquot_count == 1:
                    validated_data['freezer_location'] = freezer_location
                # otherwise create a new freezer location for all other aliquots
                # ensure that all locations are real (i.e., no spot 10 when there can only be 9 spots)
                else:
                    if freezer_object:
                        if (sample_count == 0 and count_num != 0) or sample_count != 0:
                            spot += 1
                        if spot > freezer_object.spots:
                            spot = 1
                            row += 1
                            if row > freezer_object.rows:
                                row = 1
                                box += 1
                                if box > freezer_object.boxes:
                                    box = 1
                                    rack += 1
                                    if rack > freezer_object.racks:
                                        message = "This freezer is full! No more spots can be allocated. Aborting."
                                        raise serializers.ValidationError(message)

                        user = self.context['request'].user
                        fl = FreezerLocation.objects.create(freezer=freezer_object, rack=rack, box=box, row=row,
                                                            spot=spot, created_by=user, modified_by=user)
                        validated_data['freezer_location'] = fl
                    else:
                        raise serializers.ValidationError("No Freezer exists with ID: " + str(freezer))

                aliquot = Aliquot.objects.create(**validated_data)
                aliquots.append(aliquot)
            sample_count += 1

        return aliquots

    # bulk update
    def update(self, instance, validated_data):
        # Maps for id->instance and id->data item.
        aliquot_mapping = {aliquot.id: aliquot for aliquot in instance}
        data_mapping = {item['id']: item for item in validated_data}

        # Perform updates but ignore insertions
        ret = []
        for aliquot_id, data in data_mapping.items():
            aliquot = aliquot_mapping.get(aliquot_id, None)
            if aliquot is not None:
                data['modified_by'] = self.context['request'].user
                ret.append(self.child.update(aliquot, data))

    created_by = serializers.StringRelatedField()
    modified_by = serializers.StringRelatedField()
    samples = serializers.ListField(write_only=True, required=False)
    aliquot_number = serializers.IntegerField(default=0)
    aliquot_count = serializers.IntegerField(write_only=True, required=False)
    freezer = serializers.IntegerField(write_only=True, required=False)
    rack = serializers.IntegerField(write_only=True, required=False)
    box = serializers.IntegerField(write_only=True, required=False)
    row = serializers.IntegerField(write_only=True, required=False)
    spot = serializers.IntegerField(write_only=True, required=False)

    class Meta:
        model = Aliquot
        fields = ('id', 'aliquot_string', 'sample', 'freezer_location', 'aliquot_number', 'frozen',
                  'created_date', 'created_by', 'modified_date', 'modified_by',
                  'samples', 'aliquot_count', 'freezer', 'rack', 'box', 'row', 'spot',)
        extra_kwargs = {
            'sample': {'required': False},
            'freezer_location': {'required': False}
        }
        validators = []


class AliquotCustomSerializer(serializers.ModelSerializer):
    created_by = serializers.StringRelatedField()
    modified_by = serializers.StringRelatedField()
    # freezer_location = FreezerLocationSerializer()
    samples = serializers.ListField(write_only=True, required=False)
    aliquot_number = serializers.IntegerField(default=0)
    aliquot_count = serializers.IntegerField(write_only=True, required=False)
    freezer = serializers.IntegerField(write_only=True, required=False)
    rack = serializers.IntegerField(write_only=True, required=False)
    box = serializers.IntegerField(write_only=True, required=False)
    row = serializers.IntegerField(write_only=True, required=False)
    spot = serializers.IntegerField(write_only=True, required=False)

    class Meta:
        model = Aliquot
        fields = ('id', 'aliquot_string', 'sample', 'freezer_location', 'aliquot_number', 'frozen',
                  'created_date', 'created_by', 'modified_date', 'modified_by',
                  'samples', 'aliquot_count', 'freezer', 'rack', 'box', 'row', 'spot',)
        extra_kwargs = {
            'sample': {'required': False},
            'freezer_location': {'required': False}
        }
        validators = []
        list_serializer_class = AliquotListSerializer


class AliquotSerializer(serializers.ModelSerializer):
    created_by = serializers.StringRelatedField()
    modified_by = serializers.StringRelatedField()
    freezer_location = FreezerLocationSerializer()

    class Meta:
        model = Aliquot
        fields = ('id', 'aliquot_string', 'sample', 'freezer_location', 'aliquot_number', 'frozen',
                  'created_date', 'created_by', 'modified_date', 'modified_by',)


class SampleSerializer(serializers.ModelSerializer):

    # validate required fields by matrix (beyond the fields required for every sample record regardless of matrix)
    def validate(self, data):
        matrix = data['matrix']
        if matrix.code == 'W':
            if 'filter_type' not in data:
                message = "filter_type is a required field for the water matrix"
                raise serializers.ValidationError(message)
        elif matrix.code == 'SM':
            if 'post_dilution_volume' not in data:
                message = "post_dilution_volume is a required field for the solid manure matrix"
                raise serializers.ValidationError(message)
        elif matrix.code == 'A':
            is_valid = True
            details = []
            if 'filter_type' not in data:
                details.append("filter_type is a required field for the water matrix")
            if 'dissolution_volume' not in data:
                details.append("dissolution_volume is a required field for the solid manure matrix")
            if not is_valid:
                raise serializers.ValidationError(details)
        return data

    # peg_neg_targets_extracted
    def get_peg_neg_targets_extracted(self, obj):
        targets_extracted = []
        peg_neg = obj.peg_neg
        if peg_neg is not None:
            sample_extractions = peg_neg.sampleextractions.values()

            if sample_extractions is not None:
                for sample_extraction in sample_extractions:
                    replicates = sample_extraction.get('pcrreplicates')
                    if replicates is not None:
                        for replicate in replicates:
                            target_id = replicate.get('target_id')

                            # get the unique target IDs for this peg neg
                            if target_id not in targets_extracted:
                                targets_extracted.append(target_id)

        return targets_extracted

    created_by = serializers.StringRelatedField()
    modified_by = serializers.StringRelatedField()
    sample_type_string = serializers.StringRelatedField(source='sample_type')
    matrix_string = serializers.StringRelatedField(source='matrix')
    filter_type_string = serializers.StringRelatedField(source='filter_type')
    study_string = serializers.StringRelatedField(source='study')
    sampler_name_string = serializers.StringRelatedField(source='sampler_name')
    aliquots = AliquotSerializer(many=True, read_only=True)
    peg_neg_targets_extracted = serializers.SerializerMethodField()
    final_concentrated_sample_volume = serializers.FloatField(
        source='final_concentrated_sample_volume.final_concentrated_sample_volume', read_only=True)
    final_concentrated_sample_volume_type = serializers.StringRelatedField(
        source='final_concentrated_sample_volume.concentration_type.name', read_only=True)
    final_concentrated_sample_volume_notes = serializers.CharField(
        source='final_concentrated_sample_volume.notes', read_only=True)

    class Meta:
        model = Sample
        fields = ('id', 'sample_type', 'sample_type_string', 'matrix', 'matrix_string', 'filter_type',
                  'filter_type_string', 'study', 'study_string', 'study_site_name', 'collaborator_sample_id',
                  'sampler_name', 'sampler_name_string', 'sample_notes', 'sample_description', 'arrival_date',
                  'arrival_notes', 'collection_start_date', 'collection_start_time', 'collection_end_date',
                  'collection_end_time', 'meter_reading_initial', 'meter_reading_final', 'meter_reading_unit',
                  'total_volume_sampled_initial', 'total_volume_sampled_unit_initial', 'total_volume_or_mass_sampled',
                  'sample_volume_initial', 'sample_volume_filtered', 'filter_born_on_date', 'filter_flag',
                  'secondary_concentration_flag', 'elution_notes', 'technician_initials', 'dissolution_volume',
                  'post_dilution_volume', 'analysisbatches', 'samplegroups', 'record_type', 'peg_neg',
                  'peg_neg_targets_extracted', 'final_concentrated_sample_volume',
                  'final_concentrated_sample_volume_type', 'final_concentrated_sample_volume_notes', 'aliquots',
                  'created_date', 'created_by', 'modified_date', 'modified_by',)


class SampleTypeSerializer(serializers.ModelSerializer):
    created_by = serializers.StringRelatedField()
    modified_by = serializers.StringRelatedField()

    class Meta:
        model = SampleType
        fields = ('id', 'name', 'code', 'created_date', 'created_by', 'modified_date', 'modified_by',)


class MatrixSerializer(serializers.ModelSerializer):
    created_by = serializers.StringRelatedField()
    modified_by = serializers.StringRelatedField()

    class Meta:
        model = Matrix
        fields = ('id', 'name', 'code', 'created_date', 'created_by', 'modified_date', 'modified_by',)


class FilterTypeSerializer(serializers.ModelSerializer):
    created_by = serializers.StringRelatedField()
    modified_by = serializers.StringRelatedField()

    class Meta:
        model = FilterType
        fields = ('id', 'name', 'matrix',  'created_date', 'created_by', 'modified_date', 'modified_by',)


class StudySerializer(serializers.ModelSerializer):
    created_by = serializers.StringRelatedField()
    modified_by = serializers.StringRelatedField()

    class Meta:
        model = Study
        fields = ('id', 'name', 'description', 'created_date', 'created_by', 'modified_date', 'modified_by',)


class UnitSerializer(serializers.ModelSerializer):
    created_by = serializers.StringRelatedField()
    modified_by = serializers.StringRelatedField()

    class Meta:
        model = Unit
        fields = ('id', 'name', 'symbol', 'description', 'created_date', 'created_by', 'modified_date', 'modified_by',)


######
#
#  Concentrated Sample Volumes
#
######


class FinalConcentratedSampleVolumeListSerializer(serializers.ListSerializer):
    created_by = serializers.StringRelatedField()
    modified_by = serializers.StringRelatedField()

    # bulk create
    def create(self, validated_data):
        fcsvs = [FinalConcentratedSampleVolume(**item) for item in validated_data]
        return FinalConcentratedSampleVolume.objects.bulk_create(fcsvs)

    # bulk update
    def update(self, instance, validated_data):
        # Maps for id->instance and id->data item.
        fcsv_mapping = {fcsv.id: fcsv for fcsv in instance}
        data_mapping = {item['id']: item for item in validated_data}

        # Perform updates but ignore insertions
        ret = []
        for fcsv_id, data in data_mapping.items():
            fcsv = fcsv_mapping.get(fcsv_id, None)
            if fcsv is not None:
                data['modified_by'] = self.context['request'].user
                ret.append(self.child.update(fcsv, data))

    class Meta:
        model = FinalConcentratedSampleVolume
        fields = ('id', 'sample', 'concentration_type', 'final_concentrated_sample_volume', 'notes',
                  'created_date', 'created_by', 'modified_date', 'modified_by',)


class FinalConcentratedSampleVolumeSerializer(serializers.ModelSerializer):
    created_by = serializers.StringRelatedField()
    modified_by = serializers.StringRelatedField()

    class Meta:
        model = FinalConcentratedSampleVolume
        fields = ('id', 'sample', 'concentration_type', 'final_concentrated_sample_volume', 'notes',
                  'created_date', 'created_by', 'modified_date', 'modified_by',)
        list_serializer_class = FinalConcentratedSampleVolumeListSerializer


class ConcentrationTypeSerializer(serializers.ModelSerializer):
    created_by = serializers.StringRelatedField()
    modified_by = serializers.StringRelatedField()

    class Meta:
        model = ConcentrationType
        fields = ('id', 'name', 'created_date', 'created_by', 'modified_date', 'modified_by',)


######
#
#  Sample Groups
#
######


class SampleSampleGroupSerializer(serializers.ModelSerializer):
    created_by = serializers.StringRelatedField()
    modified_by = serializers.StringRelatedField()

    class Meta:
        model = Unit
        fields = ('id', 'sample', 'samplegroup', 'created_date', 'created_by', 'modified_date', 'modified_by',)


class SampleGroupSerializer(serializers.ModelSerializer):
    created_by = serializers.StringRelatedField()
    modified_by = serializers.StringRelatedField()

    class Meta:
        model = Unit
        fields = ('id', 'name', 'description', 'created_date', 'created_by', 'modified_date', 'modified_by',)


######
#
#  Analyses
#
######


class SampleAnalysisBatchSerializer(serializers.ModelSerializer):
    created_by = serializers.StringRelatedField()
    modified_by = serializers.StringRelatedField()

    def validate(self, data):
        # if the Analysis Batch already exists
        ab_id = self.initial_data.get('analysis_batch', None)
        if ab_id is not None:
            # check if the Analysis Batch has any Extraction Batches
            ebs = ExtractionBatch.objects.filter(analysis_batch=ab_id)
            if len(ebs) > 0:
                # if yes, raise a validation error
                message = "the samples list of an analysis batch cannot be altered"
                message += " after the analysis batch has one or more extraction batches"
                raise serializers.ValidationError(message)

        return data

    class Meta:
        model = SampleAnalysisBatch
        fields = ('id', 'sample', 'analysis_batch', 'created_date', 'created_by', 'modified_date', 'modified_by',)


class AnalysisBatchSerializer(serializers.ModelSerializer):
    created_by = serializers.StringRelatedField()
    modified_by = serializers.StringRelatedField()
    new_samples = serializers.JSONField(write_only=True)

    def validate(self, data):
        if self.context['request'].method == 'POST':
            if 'new_samples' not in data:
                raise serializers.ValidationError("new_samples is a required field")

        return data

    # on create, also create child objects (sample-analysisbacth M:M relates)
    def create(self, validated_data):
        # pull out sample ID list from the request
        if 'new_samples' in validated_data:
            new_samples = validated_data.pop('new_samples')
        else:
            new_samples = []

        # create the Analysis Batch object
        analysis_batch = AnalysisBatch.objects.create(**validated_data)

        # create a Sample Analysis Batch object for each sample ID submitted
        if new_samples:
            for sample_id in new_samples:
                sample = Sample.objects.get(id=sample_id)
                SampleAnalysisBatch.objects.create(analysis_batch=analysis_batch, sample=sample)

        return analysis_batch

    # on update, also update child objects (sample-analysisbacth M:M relates), including additions and deletions
    def update(self, instance, validated_data):
        user = self.context['request'].user

        # get the old (current) sample ID list for this Analysis Batch
        old_samples = Sample.objects.filter(analysisbatches=instance.id)

        # pull out sample ID list from the request
        if 'new_samples' in self.initial_data:
            new_sample_ids = self.initial_data['new_samples']
            new_samples = Sample.objects.filter(id__in=new_sample_ids)
        else:
            new_samples = []

        # update the Analysis Batch object
        instance.analysis_batch_description = validated_data.get('analysis_batch_description',
                                                                 instance.analysis_batch_description)
        instance.analysis_batch_notes = validated_data.get('analysis_batch_notes', instance.analysis_batch_notes)
        instance.modified_by = user
        instance.save()

        # identify and delete relates where sample IDs are present in old list but not new list
        delete_samples = list(set(old_samples) - set(new_samples))
        for sample_id in delete_samples:
            delete_sample = SampleAnalysisBatch.objects.filter(analysis_batch=instance, sample=sample_id)
            delete_sample.delete()

        # identify and create relates where sample IDs are present in new list but not old list
        add_samples = list(set(new_samples) - set(old_samples))
        for sample_id in add_samples:
            SampleAnalysisBatch.objects.create(analysis_batch=instance, sample=sample_id,
                                               created_by=user, modified_by=user)

        return instance

    class Meta:
        model = AnalysisBatch
        fields = ('id', 'samples', 'analysis_batch_description', 'analysis_batch_notes', 'new_samples',
                  'created_date', 'created_by', 'modified_date', 'modified_by',)


class AnalysisBatchTemplateSerializer(serializers.ModelSerializer):
    created_by = serializers.StringRelatedField()
    modified_by = serializers.StringRelatedField()

    class Meta:
        model = AnalysisBatchTemplate
        fields = ('id', 'name', 'target', 'description', 'extraction_volume', 'elution_volume',
                  'created_date', 'created_by', 'modified_date', 'modified_by',)


######
#
#  Extractions
#
######


class ExtractionMethodSerializer(serializers.ModelSerializer):

    class Meta:
        model = ExtractionMethod
        fields = ('id', 'name', 'created_date', 'created_by', 'modified_date', 'modified_by',)


class ExtractionBatchSerializer(serializers.ModelSerializer):
    created_by = serializers.StringRelatedField()
    modified_by = serializers.StringRelatedField()
    extraction_number = serializers.IntegerField(read_only=True, default=0)
    sampleextractions = serializers.PrimaryKeyRelatedField(read_only=True, many=True)
    inhibitions = serializers.PrimaryKeyRelatedField(read_only=True, many=True)
    new_rt = serializers.JSONField(write_only=True, required=False)
    new_replicates = serializers.ListField(write_only=True, required=False)
    new_sample_extractions = serializers.ListField(write_only=True, required=False)

    def validate(self, data):
        if self.context['request'].method == 'POST':
            # if 'new_rt' not in data:
            #     raise serializers.ValidationError("new_rt is a required field")
            if 'new_sample_extractions' not in data:
                raise serializers.ValidationError("new_sample_extractions is a required field")
            if 'new_replicates' not in data:
                raise serializers.ValidationError("new_replicates is a required field")
            if 'new_sample_extractions' in data:
                is_valid = True
                details = []
                for item in data['new_samples_extractions']:
                    if 'sample' not in item:
                        is_valid = False
                        details.append("sample is a required field within new_sample_extractions")
                    if 'inhibition_dna' not in item and 'inhibition_rna' not in item:
                        is_valid = False
                        message = ""
                        if 'sample' in item:
                            message += "new sample_extraction with sample_id " + item['sample']
                            message += " is missing an inhibition; "
                        message += "Either inhibition_dna or inhibition_rna is required within new_sample_extractions"
                        message += " (these two fields cannot both be null) "
                        details.append(message)
                if not is_valid:
                    raise serializers.ValidationError(details)
            if 'new_replicates' in data:
                is_valid = True
                details = []
                for item in data['new_replicates']:
                    if 'count' not in item:
                        message = "count is a required field within new_replicates"
                        details.append(message)
                    if 'target' not in item:
                        message = "target is a required field within new_replicates"
                        details.append(message)
                if not is_valid:
                    raise serializers.ValidationError(details)
        # elif self.context['request'].method == 'PUT':
        #     if 'extraction_number' not in data or data['extraction_number'] == 0:
        #         message = "extraction_number is a required field"
        #         raise serializers.ValidationError(message)
        return data

    # on create, also create child objects (sample_extractions and replicates)
    def create(self, validated_data):
        # pull out child reverse transcription definition from the request
        rt = validated_data.pop('new_rt') if 'new_rt' in validated_data else None

        # pull out child sample_extractions list from the request
        sample_extractions = validated_data.pop('new_sample_extractions')

        # pull out child replicates list from the request
        replicates = validated_data.pop('new_replicates')

        # create the Extraction Batch object
        # but first determine if any extraction batches exist for the parent analysis batch
        prev_extr_batches = ExtractionBatch.objects.filter(analysis_batch=validated_data['analysis_batch'])
        if prev_extr_batches:
            max_extraction_number = max(prev_extr_batch.extraction_number for prev_extr_batch in prev_extr_batches)
        else:
            max_extraction_number = 0
        validated_data['extraction_number'] = max_extraction_number + 1

        # if the positive control is included and greater than zero, mark the whole record as invalid
        if 'ext_pos_cq_value' in validated_data:
            if validated_data['ext_pos_cq_value'] is not None and validated_data['ext_pos_cq_value'] > 0:
                validated_data['ext_pos_invalidg'] = True
        if 'ext_pos_gc_reaction' in validated_data:
            if validated_data['ext_pos_gc_reaction'] is not None and validated_data['ext_pos_gc_reaction'] > 0:
                validated_data['ext_pos_invalid'] = True

        extr_batch = ExtractionBatch.objects.create(**validated_data)

        # create the child replicate batches for this extraction batch
        if replicates is not None:
            for replicate in replicates:
                target_id = replicate['target']
                target = Target.objects.filter(id=target_id).first()
                if target:
                    for x in range(1, replicate['count']):
                        PCRReplicateBatch.objects.create(extraction_batch=extr_batch, target=target, replicate_number=x)
                else:
                    raise serializers.ValidationError("No Target exists with ID: " + str(target_id))

        # create the child sample_extractions for this extraction batch
        if sample_extractions is not None:
            for sample_extraction in sample_extractions:
                sample_id = sample_extraction['sample']
                sample = Sample.objects.filter(id=sample_id).first()
                sample_extraction['sample'] = sample
                if sample_extraction:
                    user = self.context['request'].user
                    sample_extraction['created_by'] = user
                    sample_extraction['modified_by'] = user
                    if 'inhibition_dna' in sample_extraction:
                        inhib_dna = sample_extraction['inhibition_dna']
                        # if inhib_dna is an integer, assume it is an existing Inhibition ID
                        if isinstance(inhib_dna, int):
                            inhib = Inhibition.objects.filter(id=inhib_dna).first()
                            if inhib:
                                sample_extraction['inhibition_dna'] = inhib
                            else:
                                raise serializers.ValidationError("No Inhibition exists with ID: " + str(inhib_dna))
                        else:
                            # otherwise assume inhib_dna is a date string
                            dna = NucleicAcidType.objects.get(name="DNA")

                            try:
                                datetime.strptime(inhib_dna, '%Y-%m-%d')
                                sample_extraction['inhibition_dna'] = Inhibition.objects.create(
                                    extraction_batch=extr_batch, sample=sample, inhibition_date=inhib_dna,
                                    nucleic_acid_type=dna, created_by=user, modified_by=user)
                            # if inhib_dna is not a date string, assign it today's date
                            except ValueError:
                                today = datetime.today().strftime('%Y-%m-%d')
                                sample_extraction['inhibition_dna'] = Inhibition.objects.create(
                                    extraction_batch=extr_batch, sample=sample, inhibition_date=today,
                                    nucleic_acid_type=dna, created_by=user, modified_by=user)
                    if 'inhibition_rna' in sample_extraction:
                        inhib_rna = sample_extraction['inhibition_rna']
                        # if inhib_rna is an integer, assume it is an existing Inhibition ID
                        if isinstance(inhib_rna, int):
                            inhib = Inhibition.objects.filter(id=inhib_rna).first()
                            if inhib:
                                sample_extraction['inhibition_rna'] = inhib
                            else:
                                raise serializers.ValidationError("No Inhibition exists with ID: " + str(inhib_rna))
                        else:
                            # otherwise assume inhib_rna is a date string
                            rna = NucleicAcidType.objects.get(name="RNA")
                            try:
                                datetime.strptime(inhib_rna, '%Y-%m-%d')
                                sample_extraction['inhibition_rna'] = Inhibition.objects.create(
                                    extraction_batch=extr_batch, sample=sample, inhibition_date=inhib_rna,
                                    nucleic_acid_type=rna, created_by=user, modified_by=user)
                            # if inhib_rna is not a date string, assign it today's date
                            except ValueError:
                                today = datetime.today().strftime('%Y-%m-%d')
                                sample_extraction['inhibition_rna'] = Inhibition.objects.create(
                                    extraction_batch=extr_batch, sample=sample, inhibition_date=today,
                                    nucleic_acid_type=rna, created_by=user, modified_by=user)

                    new_extr = SampleExtraction.objects.create(extraction_batch=extr_batch, **sample_extraction)

                    # create the child replicates for this sample_extraction
                    if replicates is not None:
                        for replicate in replicates:
                            target_id = replicate['target']
                            target = Target.objects.filter(id=target_id).first()
                            if target:
                                # create the child replicates for this sample_extraction
                                for x in range(1, replicate['count']):
                                    rep_batch = PCRReplicateBatch.objects.get(
                                        extraction_batch=extr_batch, target=target, replicate_number=x)
                                    PCRReplicate.objects.create(
                                        sample_extraction=new_extr, pcrreplicate_batch=rep_batch)
                            else:
                                raise serializers.ValidationError("No Target exists with ID: " + str(target_id))

                else:
                    raise serializers.ValidationError("No SampleExtraction exists with Sample ID: " + str(sample_id))

        # create the child reverse transcription if present
        if rt is not None:
            if rt['rt_date'] == "":
                rt['rt_date'] = None
            ReverseTranscription.objects.create(extraction_batch=extr_batch, **rt)

        return extr_batch

    # on update, any submitted nested objects (sample_extractions, replicates) will be ignored
    def update(self, instance, validated_data):
        # remove child reverse transcription definition from the request
        if 'new_rt' in validated_data:
            validated_data.pop('new_rt')

        # remove child extractions list from the request
        if 'new_sample_extractions' in validated_data:
            validated_data.pop('new_sample_extractions')

        # remove child replicates list from the request
        if 'new_replicates' in validated_data:
            validated_data.pop('new_replicates')

        # # ensure extraction_number is never zero
        # if 'extraction_number' in validated_data and validated_data['extraction_number'] == 0:
        #     validated_data['extraction_number'] = instance.extraction_number

        # if the positive control is included and greater than zero, mark the whole record as invalid
        if 'ext_pos_cq_value' in validated_data:
            if validated_data['ext_pos_cq_value'] is not None and validated_data['ext_pos_cq_value'] > 0:
                validated_data['ext_pos_invalid'] = True
        if 'ext_pos_gc_reaction' in validated_data:
            if validated_data['ext_pos_gc_reaction'] is not None and validated_data['ext_pos_gc_reaction'] > 0:
                validated_data['ext_pos_invalid'] = True

        # update the Extraction Batch object
        instance.analysis_batch = validated_data.get('analysis_batch', instance.analysis_batch)
        instance.extraction_method = validated_data.get('extraction_method', instance.extraction_method)
        instance.re_extraction = validated_data.get('re_extraction', instance.re_extraction)
        instance.re_extraction_notes = validated_data.get('re_extraction_notes', instance.re_extraction_notes)
        instance.extraction_number = instance.extraction_number
        instance.extraction_volume = validated_data.get('extraction_volume', instance.extraction_volume)
        instance.extraction_date = validated_data.get('extraction_date', instance.extraction_date)
        instance.pcr_date = validated_data.get('pcr_date', instance.pcr_date)
        instance.qpcr_template_volume = validated_data.get('qpcr_template_volume', instance.qpcr_template_volume)
        instance.elution_volume = validated_data.get('elution_volume', instance.elution_volume)
        instance.sample_dilution_factor = validated_data.get('sample_dilution_factor', instance.sample_dilution_factor)
        instance.qpcr_reaction_volume = validated_data.get('qpcr_reaction_volume', instance.qpcr_reaction_volume)
        instance.ext_pos_cq_value = validated_data.get('ext_pos_cq_value', instance.ext_pos_cq_value)
        instance.ext_pos_gc_reaction = validated_data.get('ext_pos_gc_reaction', instance.ext_pos_gc_reaction)
        instance.ext_pos_invalid = validated_data.get('ext_pos_invalid', instance.ext_pos_invalid)
        instance.modified_by = self.context['request'].user
        instance.save()

        return instance

    # # extraction_method
    # def get_extraction_method(self, obj):
    #     extraction_method_id = obj.extraction_method_id
    #     extraction_method = ExtractionMethod.objects.get(id=extraction_method_id)
    #     extraction_method_name = extraction_method.name
    #     data = {"id": extraction_method_id, "name": extraction_method_name}
    #     return data

    class Meta:
        model = ExtractionBatch
        fields = ('id', 'extraction_string', 'analysis_batch', 'extraction_method', 're_extraction',
                  're_extraction_notes', 'extraction_number', 'extraction_volume', 'extraction_date', 'pcr_date',
                  'qpcr_template_volume', 'elution_volume', 'sample_dilution_factor', 'qpcr_reaction_volume',
                  'sampleextractions', 'inhibitions', 'ext_pos_cq_value', 'ext_pos_gc_reaction',
                  'ext_pos_invalid', 'new_rt', 'new_replicates', 'new_sample_extractions',
                  'created_date', 'created_by', 'modified_date', 'modified_by',)


class ReverseTranscriptionSerializer(serializers.ModelSerializer):
    created_by = serializers.StringRelatedField()
    modified_by = serializers.StringRelatedField()

    def create(self, validated_data):
        # if the positive control is included and greater than zero, mark the whole record as invalid
        if 'rt_pos_cq_value' in validated_data:
            if validated_data['rt_pos_cq_value'] is not None and validated_data['rt_pos_cq_value'] > 0:
                validated_data['rt_pos_invalid'] = True
        if 'rt_pos_gc_reaction' in validated_data:
            if validated_data['rt_pos_gc_reaction'] is not None and validated_data['rt_pos_gc_reaction'] > 0:
                validated_data['rt_pos_invalid'] = True

        return ReverseTranscription.objects.create(**validated_data)

    def update(self, instance, validated_data):
        # if the positive control is included and greater than zero, mark the whole record as invalid
        if 'rt_pos_cq_value' in validated_data:
            if validated_data['rt_pos_cq_value'] is not None and validated_data['rt_pos_cq_value'] > 0:
                validated_data['rt_pos_invalid'] = True
        if 'rt_pos_gc_reaction' in validated_data:
            if validated_data['rt_pos_gc_reaction'] is not None and validated_data['rt_pos_gc_reaction'] > 0:
                validated_data['rt_pos_invalid'] = True

        # update the Reverse Transcription object
        instance.extraction_batch = validated_data.get('extraction_batch', instance.extraction_batch)
        instance.template_volume = validated_data.get('template_volume', instance.template_volume)
        instance.reaction_volume = validated_data.get('reaction_volume', instance.reaction_volume)
        instance.rt_date = validated_data.get('rt_date', instance.rt_date)
        instance.re_rt = validated_data.get('re_rt', instance.re_rt)
        instance.re_rt_notes = validated_data.get('re_rt_notes', instance.re_rt_notes)
        instance.rt_pos_cq_value = validated_data.get('rt_pos_cq_value', instance.rt_pos_cq_value)
        instance.rt_pos_gc_reaction = validated_data.get('rt_pos_gc_reaction', instance.rt_pos_gc_reaction)
        instance.rt_pos_invalid = validated_data.get('rt_pos_invalid',
                                                             instance.rt_pos_invalid)
        instance.modified_by = self.context['request'].user
        instance.save()

        return instance

    class Meta:
        model = ReverseTranscription
        fields = ('id', 'extraction_batch', 'template_volume', 'reaction_volume', 'rt_date', 're_rt', 're_rt_notes',
                  'rt_pos_cq_value', 'rt_pos_gc_reaction', 'rt_pos_invalid',
                  'created_date', 'created_by', 'modified_date', 'modified_by',)


class SampleExtractionSerializer(serializers.ModelSerializer):
    created_by = serializers.StringRelatedField()
    modified_by = serializers.StringRelatedField()

    def validate(self, data):
        if 'inhibition_dna' not in data and 'inhibition_rna' not in data:
            message = "Either inhibition_dna or inhibition_rna is required (these two fields cannot both be null)"
            raise serializers.ValidationError(message)
        return data

    class Meta:
        model = SampleExtraction
        fields = ('id', 'sample', 'extraction_batch', 'inhibition_dna', 'inhibition_rna', 'pcrreplicates',
                  'created_date', 'created_by', 'modified_date', 'modified_by',)


class PCRReplicateListSerializer(serializers.ListSerializer):

    # bulk update
    def update(self, instance, validated_data):
        # Maps for id->instance and id->data item.
        pcrrep_mapping = {pcrrep.id: pcrrep for pcrrep in instance}
        data_mapping = {item['id']: item for item in validated_data}

        # Perform updates but ignore insertions
        ret = []
        for pcrrep_id, data in data_mapping.items():
            pcrrep = pcrrep_mapping.get(pcrrep_id, None)
            if pcrrep is not None:
                data['modified_by'] = self.context['request'].user
                ret.append(self.child.update(pcrrep, data))

    def get_inhibition_dilution_factor(self, obj):
        sample_extraction_id = obj.sample_extraction_id
        sample_extraction = SampleExtraction.objects.get(id=sample_extraction_id)
        pcrreplicate_batch_id = obj.pcrreplicate_batch_id
        pcrreplicate_batch = PCRReplicateBatch.objects.get(id=pcrreplicate_batch_id)
        nucleic_acid_type = pcrreplicate_batch.target.nucleic_acid_type
        if nucleic_acid_type == 'DNA':
            data = sample_extraction.inhibition_dna.dilution_factor
        elif nucleic_acid_type == 'RNA':
            data = sample_extraction.inhibition_rna.dilution_factor
        else:
            data = None
        return data

    def get_all_parent_controls_uploaded(self, obj):
        data = False
        pcrrep_batch = PCRReplicateBatch.objects.get(id=obj.pcrreplicate_batch_id)
        if pcrrep_batch.ext_neg_cq_value and pcrrep_batch.rt_neg_cq_value and pcrrep_batch.pcr_neg_cq_value:
            data = True
        return data

    created_by = serializers.StringRelatedField()
    modified_by = serializers.StringRelatedField()
    sample = serializers.PrimaryKeyRelatedField(source='sample_extraction.sample', read_only=True)
    peg_neg = serializers.PrimaryKeyRelatedField(source='sample_extraction.sample.peg_neg', read_only=True)
    inhibition_dilution_factor = serializers.SerializerMethodField()
    all_parent_controls_uploaded = serializers.SerializerMethodField()
    invalid_override_string = serializers.StringRelatedField(source='invalid_override')

    class Meta:
        model = PCRReplicate
        fields = ('id', 'sample_extraction', 'sample', 'peg_neg', 'inhibition_dilution_factor', 'pcrreplicate_batch',
                  'cq_value', 'gc_reaction', 'replicate_concentration', 'concentration_unit',
                  'invalid', 'invalid_override', 'invalid_override_string',
                  'all_parent_controls_uploaded', 'created_date', 'created_by', 'modified_date', 'modified_by',)
        extra_kwargs = {
            'concentration_unit': {'required': False}
        }


class PCRReplicateSerializer(serializers.ModelSerializer):

    def update(self, instance, validated_data):
        # update the instance
        instance.sample_extraction = validated_data.get('sample_extraction', instance.sample_extraction)
        instance.pcrreplicate_batch = validated_data.get('pcrreplicate_batch', instance.pcrreplicate_batch)
        instance.cq_value = validated_data.get('cq_value', instance.cq_value)
        instance.gc_reaction = validated_data.get('gc_reaction', instance.gc_reaction)
        instance.replicate_concentration = validated_data.get('replicate_concentration',
                                                              instance.replicate_concentration)
        instance.concentration_unit = validated_data.get('concentration_unit', instance.concentration_unit)
        instance.invalid = validated_data.get('invalid', instance.invalid)
        instance.invalid_override = validated_data.get('invalid_override',
                                                               instance.invalid_override)
        if 'request' in self.context and 'user' in self.context['request']:
            instance.modified_by = self.context['request'].user
        else:
            instance.modified_by = validated_data.get('modified_by', instance.modified_by)

        instance.save()

        return instance

    def get_inhibition_dilution_factor(self, obj):
        sample_extraction_id = obj.sample_extraction_id
        sample_extraction = SampleExtraction.objects.get(id=sample_extraction_id)
        pcrreplicate_batch_id = obj.pcrreplicate_batch_id
        pcrreplicate_batch = PCRReplicateBatch.objects.get(id=pcrreplicate_batch_id)
        nucleic_acid_type = pcrreplicate_batch.target.nucleic_acid_type
        if nucleic_acid_type == 'DNA':
            data = sample_extraction.inhibition_dna.dilution_factor
        elif nucleic_acid_type == 'RNA':
            data = sample_extraction.inhibition_rna.dilution_factor
        else:
            data = None
        return data

    def get_all_parent_controls_uploaded(self, obj):
        data = False
        pcrrep_batch = PCRReplicateBatch.objects.get(id=obj.pcrreplicate_batch_id)
        if pcrrep_batch.ext_neg_cq_value and pcrrep_batch.rt_neg_cq_value and pcrrep_batch.pcr_neg_cq_value:
            data = True
        return data

    created_by = serializers.StringRelatedField()
    modified_by = serializers.StringRelatedField()
    sample = serializers.PrimaryKeyRelatedField(source='sample_extraction.sample', read_only=True)
    peg_neg = serializers.PrimaryKeyRelatedField(source='sample_extraction.sample.peg_neg', read_only=True)
    inhibition_dilution_factor = serializers.SerializerMethodField()
    all_parent_controls_uploaded = serializers.SerializerMethodField()
    invalid_override_string = serializers.StringRelatedField(source='invalid_override')

    class Meta:
        model = PCRReplicate
        fields = ('id', 'sample_extraction', 'sample', 'peg_neg', 'inhibition_dilution_factor', 'pcrreplicate_batch',
                  'cq_value', 'gc_reaction', 'replicate_concentration', 'concentration_unit',
                  'invalid', 'invalid_override', 'invalid_override_string',
                  'all_parent_controls_uploaded', 'created_date', 'created_by', 'modified_date', 'modified_by',)
        list_serializer_class = PCRReplicateListSerializer
        extra_kwargs = {
            'concentration_unit': {'required': False}
        }


class PCRReplicateBatchSerializer(serializers.ModelSerializer):

    def validate(self, data):
        """
        Ensure target organism results file fields are included in request data.
        """
        if self.context['request'].method == 'PUT':
            validation_errors = []
            # if 'analysis_batch' not in data:
            #     validation_errors.append("analysis_batch is required")
            # if 'extraction_number' not in data:
            #     validation_errors.append("extraction_number is required")
            # if 'target' not in data:
            #     validation_errors.append("target is required")
            # if 'replicate_number' not in data:
            #     validation_errors.append("replicate_number is required")
            # if 'standard_curve' not in data:
            #     validation_errors.append("standard_curve is required")
            if 'ext_neg_cq_value' not in data:
                validation_errors.append("ext_neg_cq_value is required")
            if 'pcr_neg_cq_value' not in data:
                validation_errors.append("pcr_neg_cq_value is required")
            if 'pcr_pos_gc_reaction' not in data:
                validation_errors.append("pcr_pos_gc_reaction is required")
            if 'updated_pcrreplicates' not in data:
                validation_errors.append("updated_pcrreplicates is required")
            else:
                is_valid = True
                details = []
                updated_pcrreplicates = data.get('updated_pcrreplicates')
                count = 0
                for rep in updated_pcrreplicates:
                    if 'sample' not in rep:
                        is_valid = False
                        details.append({"updated_pcrreplicates " + count: "sample is required"})
                    if 'cq_value' not in rep:
                        is_valid = False
                        details.append({"updated_pcrreplicates " + count: "cq_value is required"})
                    if 'gc_reaction' not in rep:
                        is_valid = False
                        details.append({"updated_pcrreplicates " + count: "gc_reaction is required"})
                    count = count + 1
                if not is_valid:
                    validation_errors.append(details)
            if validation_errors:
                raise serializers.ValidationError(validation_errors)
        return data

    def update(self, instance, validated_data):
        user = self.context['request'].user
        is_valid = True
        valid_data = []
        response_errors = []

        updated_pcrreplicates = validated_data.get('updated_pcrreplicates', None)
        existing_reps = PCRReplicate.objects.filter(pcrreplicate_batch=instance.id)
        if len(existing_reps) == len(updated_pcrreplicates):
            # first validate the controls
            extneg_cq = validated_data.get('ext_neg_cq_value', 0)
            rtneg_cq = validated_data.get('rt_neg_cq_value', 0)
            pcrneg_cq = validated_data.get('pcr_neg_cq_value', 0)
            ext_neg_flag = False if extneg_cq == 0 else True
            rt_neg_flag = False if rtneg_cq == 0 else True
            pcr_neg_flag = False if pcrneg_cq == 0 else True
            # validating the pcr_pos will come in a later release of the software
            # sc = validated_data.get('standard_curve', None)
            pcr_pos_flag = False

            # then update the instance, but do not save until all child replicates are valid
            eb = validated_data.get('extraction_batch', instance.extraction_batch)
            target = validated_data.get('target', instance.target)
            # rn = validated_data.get('replicate_number', instance.replicate_number)
            instance.notes = validated_data.get('notes', instance.notes)
            instance.ext_neg_cq_value = extneg_cq
            instance.ext_neg_gc_reaction = validated_data.get('ext_neg_gc_reaction', 0)
            instance.ext_neg_invalid = ext_neg_flag
            instance.rt_neg_cq_value = rtneg_cq
            instance.rt_neg_gc_reaction = validated_data.get('rt_neg_gc_reaction', 0)
            instance.rt_neg_invalid = rt_neg_flag
            instance.pcr_neg_cq_value = pcrneg_cq
            instance.pcr_neg_gc_reaction = validated_data.get('pcr_neg_gc_reaction', 0)
            instance.pcr_neg_invalid = pcr_neg_flag
            instance.pcr_pos_cq_value = validated_data.get('pcr_pos_cq_value', 0)
            instance.pcr_pos_gc_reaction = validated_data.get('pcr_pos_gc_reaction', 0)
            instance.pcr_pos_invalid = pcr_pos_flag
            instance.re_pcr = validated_data.get('re_pcr', instance.re_pcr)
            instance.modified_by = user
            valid_data.append('pcrrepbatch')

            # next ensure the submitted pcr replicates exist in the DB
            for pcrreplicate in updated_pcrreplicates:
                sample_id = pcrreplicate.get('sample', None)
                sample = Sample.objects.filter(id=sample_id).first()
                if sample:
                    if isinstance(eb, int):
                        eb = ExtractionBatch.objects.filter(id=eb).first()
                    sample_extraction = SampleExtraction.objects.filter(
                        extraction_batch=eb.id, sample=sample.id).first()
                    if sample_extraction:
                        # finally validate the pcr reps and calculate their final replicate concentrations
                        cq_value = pcrreplicate.get('cq_value', 0)
                        gc_reaction = pcrreplicate.get('gene_copies_per_reaction', 0)
                        pcrrep = PCRReplicate.objects.filter(
                            extraction=sample_extraction.id, pcrreplicate_batch=instance.id).first()
                        if pcrrep:
                            # ensure that the concentrated/dissolved/diluted volume exists for this sample
                            if sample.dissolution_volume is None or sample.post_dilution_volume is None:
                                fcsv = FinalConcentratedSampleVolume.objects.get(sample=sample.id)
                                if fcsv.final_concentrated_sample_volume is None:
                                    is_valid = False
                                    message = "No concentrated/dissolved/diluted volume exists"
                                    message += " for Sample ID: " + sample
                                    response_errors.append({"pcrreplicate": message})
                                    # skip to the next item in the loop
                                    continue
                            # that particular sample volume exists, so finish updating this rep
                            # ensure target is a Target object, not an integer
                            if isinstance(target, int):
                                target = Target.objects.get(id=target).first()
                            new_data = {'pcrreplicate_batch': instance.id, 'cq_value': cq_value,
                                        'gc_reaction': gc_reaction, 'modified_by': user}
                            serializer = PCRReplicateSerializer(pcrrep, data=new_data, partial=True)
                            if serializer.is_valid():
                                valid_data.append(serializer)
                            else:
                                is_valid = False
                                response_errors.append(serializer.errors)
                        else:
                            is_valid = False
                            message = "No PCRReplicate exists with PCRReplicate Batch ID: " + instance.id + ", "
                            message += "SampleExtraction ID: " + sample_extraction.id
                            response_errors.append({"pcrreplicate": message})
                    else:
                        is_valid = False
                        message = "No SampleExtraction exists with Extraction Batch ID: " + eb.id + ", "
                        message += "Sample ID: " + sample_id
                        response_errors.append({"sampleextraction": message})
                else:
                    is_valid = False
                    message = "No Sample exists with Sample ID: " + sample_id
                    response_errors.append({"sample": message})
        else:
            is_valid = False
            message = "The number of submitted PCR replicates (" + str(len(updated_pcrreplicates)) + ") does not match "
            message += "the number of existing PCR replicates (" + str(len(existing_reps)) + ") for this batch."
            response_errors.append({"updated_pcrreplicates": message})
        if is_valid:
            # now that all items are proven valid, save and return them to the user
            for item in valid_data:
                if item == 'pcrrepbatch':
                    instance.save()
                else:
                    # this save will also calculate sample mean concentrations if applicable
                    item.save()
            return instance
        else:
            raise serializers.ValidationError(response_errors)

    def calc_flag(self, cq_value, extneg_cq, rtneg_cq, pcrneg_cq, gc_reaction):
        invalid = True
        if cq_value is None:
            if rtneg_cq is not None:
                if extneg_cq == 0 and rtneg_cq == 0 and pcrneg_cq == 0 and gc_reaction >= 0:
                    invalid = False
            else:
                if extneg_cq == 0 and pcrneg_cq == 0 and gc_reaction >= 0:
                    invalid = False
        return invalid

    created_by = serializers.StringRelatedField()
    modified_by = serializers.StringRelatedField()
    updated_pcrreplicates = serializers.ListField(write_only=True)
    extraction_batch = ExtractionBatchSerializer(required=False)
    pcrreplicates = PCRReplicateSerializer(many=True, read_only=True)

    class Meta:
        model = PCRReplicateBatch
        fields = ('id', 'extraction_batch', 'target', 'replicate_number', 'notes', 'ext_neg_cq_value',
                  'ext_neg_gc_reaction', 'ext_neg_invalid', 'rt_neg_cq_value', 'rt_neg_gc_reaction',
                  'rt_neg_invalid', 'pcr_neg_cq_value', 'pcr_neg_gc_reaction', 'pcr_neg_invalid',
                  'pcr_pos_cq_value', 'pcr_pos_gc_reaction', 'pcr_pos_invalid', 're_pcr', 'pcrreplicates',
                  'updated_pcrreplicates', 'created_date', 'created_by', 'modified_date', 'modified_by',)
        extra_kwargs = {
            'extraction_batch': {'required': False},
            'pcrreplicates': {'required': False}
        }


class ResultSerializer(serializers.ModelSerializer):
    created_by = serializers.StringRelatedField()
    modified_by = serializers.StringRelatedField()

    class Meta:
        model = Result
        fields = ('id', 'sample_mean_concentration', 'sample', 'target',
                  'created_date', 'created_by', 'modified_date', 'modified_by',)


class StandardCurveSerializer(serializers.ModelSerializer):
    created_by = serializers.StringRelatedField()
    modified_by = serializers.StringRelatedField()

    class Meta:
        model = StandardCurve
        fields = ('id', 'r_value', 'slope', 'efficiency', 'pos_ctrl_cq', 'pos_ctrl_cq_range', 'created_date',
                  'created_by', 'modified_date', 'modified_by',)


class InhibitionListSerializer(serializers.ListSerializer):
    created_by = serializers.StringRelatedField()
    modified_by = serializers.StringRelatedField()

    def validate_dilution_factor(self, value):
        """
        Ensure dilution factor is only ever 1, 5, or 10 (or null)
        """
        if value not in (1, 5, 10, None):
            raise serializers.ValidationError("dilution_factor can only have a value of 1, 5, 10, or null")
        return value

    # bulk create
    def create(self, validated_data):
        inhibitions = [Inhibition(**item) for item in validated_data]
        return Inhibition.objects.bulk_create(inhibitions)

    # bulk update
    def update(self, instance, validated_data):
        # Maps for id->instance and id->data item.
        inhibition_mapping = {inhibition.id: inhibition for inhibition in instance}
        data_mapping = {item['id']: item for item in validated_data}

        # Perform updates but ignore insertions
        ret = []
        for inhibition_id, data in data_mapping.items():
            inhibition = inhibition_mapping.get(inhibition_id, None)
            if inhibition is not None:
                data['modified_by'] = self.context['request'].user
                ret.append(self.child.update(inhibition, data))

    class Meta:
        class Meta:
            model = Inhibition
            fields = ('id', 'sample', 'extraction_batch', 'inhibition_date', 'nucleic_acid_type', 'dilution_factor',
                      'created_date', 'created_by', 'modified_date', 'modified_by',)


class InhibitionSerializer(serializers.ModelSerializer):
    created_by = serializers.StringRelatedField()
    modified_by = serializers.StringRelatedField()

    def validate_dilution_factor(self, value):
        """
        Ensure dilution factor is only ever 1, 5, or 10 (or null)
        """
        if value not in (1, 5, 10, None):
            raise serializers.ValidationError("dilution_factor can only have a value of 1, 5, 10, or null")
        return value

    class Meta:
        model = Inhibition
        fields = ('id', 'sample', 'extraction_batch', 'inhibition_date', 'nucleic_acid_type', 'dilution_factor',
                  'created_date', 'created_by', 'modified_date', 'modified_by',)
        list_serializer_class = InhibitionListSerializer


class SampleInhibitionSerializer(serializers.ModelSerializer):
    created_by = serializers.StringRelatedField()
    modified_by = serializers.StringRelatedField()
    inhibitions = InhibitionSerializer(many=True, read_only=True)

    class Meta:
        model = Sample
        fields = ('id', 'sample_type', 'sample_description', 'inhibitions',
                  'created_date', 'created_by', 'modified_date', 'modified_by',)


class InhibitionCalculateDilutionFactorSerializer(serializers.ModelSerializer):

    def validate(self, data):
        """
        Ensure inhibition_positive_control_cq_value and inhibitions are included in request data.
        """
        if 'inh_pos_cq_value' not in data:
            raise serializers.ValidationError("inh_pos_cq_value is required")
        if 'inhibitions' not in data:
            raise serializers.ValidationError("inhibitions is required")
        ab = data['analysis_batch']
        en = data['extraction_number']
        na = data['nucleic_acid_type']
        eb = ExtractionBatch.objects.filter(analysis_batch=ab, extraction_number=en).first()
        is_valid = True
        details = []
        for inhibition in data['inhibitions']:
            sample = inhibition['sample']
            inhib = Inhibition.objects.filter(sample=sample, extraction_batch=eb.id, nucleic_acid_type=na.id).first()
            if not inhib:
                is_valid = False
                message = "An inhibition with analysis_batch_id of (" + str(ab) + ") "
                message += "and sample_id of (" + str(sample) + ") "
                message += "and nucleic_acid_type of (" + str(na) + ") does not exist in the database"
                details.append(message)
            elif inhib.nucleic_acid_type != na:
                is_valid = False
                message = "Sample " + str(sample) + ": "
                message += "The submitted nucleic_acid_type (" + str(inhib.nucleic_acid_type) + ") "
                message += "does not match the existing value (" + str(na) + ") in the database"
                details.append(message)
        if not is_valid:
            raise serializers.ValidationError(details)
        return data

    created_by = serializers.StringRelatedField()
    modified_by = serializers.StringRelatedField()
    analysis_batch = serializers.IntegerField(write_only=True)
    extraction_number = serializers.IntegerField(write_only=True)
    inh_pos_cq_value = serializers.FloatField(write_only=True)
    inhibitions = serializers.ListField(write_only=True)
    sample = serializers.IntegerField(read_only=True)
    suggested_dilution_factor = serializers.FloatField(read_only=True)

    class Meta:
        model = Inhibition
        fields = ('id', 'sample', 'analysis_batch', 'extraction_number', 'inhibition_date', 'nucleic_acid_type',
                  'dilution_factor', 'inh_pos_cq_value', 'inhibitions', 'suggested_dilution_factor',
                  'created_date', 'created_by', 'modified_date', 'modified_by',)


class TargetSerializer(serializers.ModelSerializer):
    created_by = serializers.StringRelatedField()
    modified_by = serializers.StringRelatedField()

    class Meta:
        model = Target
        fields = ('id', 'name', 'code', 'nucleic_acid_type', 'notes',
                  'created_date', 'created_by', 'modified_date', 'modified_by',)


######
#
#  Misc
#
######


class FieldUnitSerializer(serializers.ModelSerializer):
    created_by = serializers.StringRelatedField()
    modified_by = serializers.StringRelatedField()

    class Meta:
        model = FieldUnit
        fields = ('id', 'table', 'field', 'unit', 'created_date', 'created_by', 'modified_date', 'modified_by',)


class OtherAnalysisSerializer(serializers.ModelSerializer):
    created_by = serializers.StringRelatedField()
    modified_by = serializers.StringRelatedField()

    class Meta:
        model = OtherAnalysis
        fields = ('id', 'description', 'data', 'created_date', 'created_by', 'modified_date', 'modified_by',)


######
#
#  Users
#
######


class UserSerializer(serializers.ModelSerializer):

    class Meta:
        model = User
        fields = ('id', 'username', 'first_name', 'last_name', 'email', 'groups', 'user_permissions',
                  'is_superuser', 'is_staff', 'is_active',)


######
#
#  Special
#
######


class SimpleSampleSerializer(serializers.ModelSerializer):
    # sample_type
    def get_sample_type(self, obj):
        sample_type_id = obj.sample_type_id
        sample_type = SampleType.objects.get(id=sample_type_id)
        sample_type_name = sample_type.name
        data = {"id": sample_type_id, "name": sample_type_name}
        return data

    # matrix
    def get_matrix(self, obj):
        matrix_id = obj.matrix_id
        matrix = Matrix.objects.get(id=matrix_id)
        matrix_name = matrix.name
        data = {"id": matrix_id, "name": matrix_name}
        return data

    # study
    def get_study(self, obj):
        study_id = obj.study_id
        study = Study.objects.get(id=study_id)
        study_name = study.name
        data = {"id": study_id, "name": study_name}
        return data

    created_by = serializers.StringRelatedField()
    modified_by = serializers.StringRelatedField()
    sample_type = serializers.SerializerMethodField()
    matrix = serializers.SerializerMethodField()
    study = serializers.SerializerMethodField()

    class Meta:
        model = Sample
        fields = ('id', 'sample_type', 'matrix', 'study', 'collaborator_sample_id', 'sample_description',
                  'created_date', 'created_by', 'modified_date', 'modified_by',)


class ExtractionBatchSummarySerializer(serializers.ModelSerializer):
    created_by = serializers.StringRelatedField()
    modified_by = serializers.StringRelatedField()

    def get_inhibitions(self, obj):
        inhibitions = {}
        sample_extractions = obj.sampleextractions.values()

        if sample_extractions is not None:
            for sample_extraction in sample_extractions:
                sample_id = sample_extraction.get('sample_id')
                if sample_id is not None:
                    sample = Sample.objects.get(id=sample_id)
                    sample_inhibitions = sample.inhibitions.values()
                    if sample_inhibitions is not None:
                        for inhibition in sample_inhibitions:
                            creator = User.objects.get(id=inhibition['created_by_id'])
                            modifier = User.objects.get(id=inhibition['modified_by_id'])
                            data = {"id": inhibition['id'], "sample": inhibition['sample_id'],
                                    "extraction_batch": inhibition['extraction_batch_id'],
                                    "inhibition_date": inhibition['inhibition_date'],
                                    "nucleic_acid_type_id": inhibition['nucleic_acid_type_id'],
                                    "dilution_factor": inhibition['dilution_factor'],
                                    "created_date": inhibition['created_date'],
                                    "created_by": creator.username if creator is not None else None,
                                    "modified_date": inhibition['modified_date'],
                                    "modified_by": modifier.username if modifier is not None else None}
                            inhibitions[inhibition['id']] = data

        return inhibitions.values()

    def get_reverse_transcriptions(self, obj):
        reverse_transcriptions = {}
        reversetranscriptions = obj.reversetranscriptions.values()

        if reversetranscriptions is not None:
            for reversetranscription in reversetranscriptions:
                reverse_transcription_id = reversetranscription.get('id')
                rt = ReverseTranscription.objects.get(id=reverse_transcription_id)
                data = {"id": reverse_transcription_id, "extraction_batch": rt.extraction_batch.id,
                        "template_volume": rt.template_volume, "reaction_volume": rt.reaction_volume,
                        "rt_date": rt.rt_date, "re_rt": rt.re_rt, "created_date": rt.created_date,
                        "created_by": rt.created_by.username if rt.created_by is not None else None,
                        "modified_date": rt.modified_date,
                        "modified_by": rt.modified_by.username if rt.modified_by is not None else None}
                reverse_transcriptions[reverse_transcription_id] = data

        return reverse_transcriptions.values()

    def get_targets(self, obj):
        targets = {}
        pcrrep_batches = obj.pcrreplicatebatches.values()

        if pcrrep_batches is not None:
            for pcrrep_batch in pcrrep_batches:
                target_id = pcrrep_batch.get('target_id')
                pcrreps = PCRReplicate.objects.filter(pcrreplicate_batch=pcrrep_batch['id'])

                # count the number of replicates associated with each target
                # if the target is already included in our local dict, increment the rep counter
                if targets.get(target_id, None) is not None:
                    data = targets[target_id]
                    data['replicates'] += len(pcrreps)
                # otherwise, add the target to our local dict and 'initialize' its rep counter
                else:
                    target = Target.objects.get(id=target_id)
                    data = {"id": target_id, "code": target.code,
                            "nucleic_acid_type": target.nucleic_acid_type.id, "replicates": len(pcrreps)}
                targets[target_id] = data

        return targets.values()

    # extraction_method
    def get_extraction_method(self, obj):
        extraction_method_id = obj.extraction_method_id
        extraction_method = ExtractionMethod.objects.get(id=extraction_method_id)
        extraction_method_name = extraction_method.name
        data = {"id": extraction_method_id, "name": extraction_method_name}
        return data

    sampleextractions = SampleExtractionSerializer(many=True, read_only=True)
    inhibitions = serializers.SerializerMethodField()
    reverse_transcriptions = serializers.SerializerMethodField()
    targets = serializers.SerializerMethodField()
    extraction_method = serializers.SerializerMethodField()

    class Meta:
        model = ExtractionBatch
        fields = ('id', 'extraction_string', 'analysis_batch', 'extraction_method', 're_extraction',
                  're_extraction_notes', 'extraction_number', 'extraction_volume', 'extraction_date', 'pcr_date',
                  'qpcr_template_volume', 'elution_volume', 'sample_dilution_factor', 'qpcr_reaction_volume',
                  'sampleextractions', 'inhibitions', 'reverse_transcriptions', 'targets',
                  'created_date', 'created_by', 'modified_date', 'modified_by',)


class AnalysisBatchDetailSerializer(serializers.ModelSerializer):
    created_by = serializers.StringRelatedField()
    modified_by = serializers.StringRelatedField()

    # studies
    def get_studies(self, obj):
        studies = []
        vals = obj.samples.values()
        if vals is not None:
            for val in vals:
                study_id = val.get('study_id')
                study = Study.objects.get(id=study_id)
                study_name = study.name
                study_description = study.description
                data = {"id": study_id, "name": study_name, "description": study_description}
                studies.append(data)
        return studies

    extractionbatches = ExtractionBatchSummarySerializer(many=True, read_only=True)
    samples = SimpleSampleSerializer(many=True, read_only=True)
    studies = serializers.SerializerMethodField()

    class Meta:
        model = AnalysisBatch
        fields = ('id', 'analysis_batch_description', 'analysis_batch_notes', 'samples', 'studies',
                  'extractionbatches', 'created_date', 'created_by', 'modified_date', 'modified_by',)


class AnalysisBatchSummarySerializer(serializers.ModelSerializer):
    created_by = serializers.StringRelatedField()
    modified_by = serializers.StringRelatedField()

    # studies
    def get_studies(self, obj):
        studies = []
        vals = obj.samples.values()
        if vals is not None:
            for val in vals:
                study_id = val.get('study_id')
                study = Study.objects.get(id=study_id)
                study_name = study.name
                data = {"id": study_id, "name": study_name}
                studies.append(data)
        return studies

    # summary: sample_extraction count, inhibition count, reverse transcription count, target count
    def get_summary(self, obj):
        summary = {}
        sample_extraction_count = 0
        inhibition_count = 0
        reverse_transcription_count = 0
        targets = []

        # samples_extraction and reverse_transcription count
        extraction_batches = obj.extractionbatches.values()
        if extraction_batches is not None:
            for extraction_batch in extraction_batches:
                extraction_batch_id = extraction_batch.get('id')

                sample_extractions = SampleExtraction.objects.filter(extraction_batch__exact=extraction_batch_id)
                sample_extraction_count += len(sample_extractions)

                reversetranscriptions = ReverseTranscription.objects.filter(extraction_batch__exact=extraction_batch_id)
                reverse_transcription_count += len(reversetranscriptions)

                inhibitions = Inhibition.objects.filter(extraction_batch__exact=extraction_batch_id)
                inhibition_count += len(inhibitions)

                pcrreplicatebatches = PCRReplicateBatch.objects.filter(extraction_batch__exact=extraction_batch_id)

                # target count
                if pcrreplicatebatches is not None:
                    for pcrreplicatebatch in pcrreplicatebatches:
                        target = pcrreplicatebatch.target
                        if target not in targets:
                            targets.append(target)

        summary['sample_extraction_count'] = sample_extraction_count
        summary['inhibition_count'] = inhibition_count
        summary['reverse_transcription_count'] = reverse_transcription_count
        summary['target_count'] = len(targets)

        return summary

    studies = serializers.SerializerMethodField()
    summary = serializers.SerializerMethodField()

    class Meta:
        model = AnalysisBatch
        fields = ('id', 'analysis_batch_description', 'analysis_batch_notes', 'studies', 'summary',
                  'created_date', 'created_by', 'modified_date', 'modified_by',)
