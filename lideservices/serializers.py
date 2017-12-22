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
        d = data[0]
        if 'freezer_location' not in d:
            if 'freezer' not in d or 'rack' not in d or 'box' not in d or 'row' not in d or 'spot' not in d:
                message = "Either a freezer_location ID or coordinates (freezer, rack, box, row, spot) is required."
                raise serializers.ValidationError(message)
        return data

    # bulk create
    def create(self, validated_data):
        validated_data = validated_data[0]

        # pull out the freezer location fields from the request
        if 'freezer_location' in validated_data:
            freezer_location = FreezerLocation.objects.get(id=validated_data['freezer_location'].id)
            freezer = freezer_location.freezer.id
            rack = freezer_location.rack
            box = freezer_location.box
            row = freezer_location.row
            spot = freezer_location.spot
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

        aliquots = []
        for count_num in range(0, aliquot_count):
            # first determine if any aliquots exist for the parent sample
            prev_aliquots = Aliquot.objects.filter(sample=validated_data['sample'].id)
            if prev_aliquots:
                max_aliquot_number = max(prev_aliquot.aliquot_number for prev_aliquot in prev_aliquots)
            else:
                max_aliquot_number = 0
            # then assign the proper aliquot_number
            validated_data['aliquot_number'] = max_aliquot_number + 1

            # next create the freezer location for this aliquot to use
            # use the existing freezer location if it was submitted and the aliquot count is exactly 1
            if 'freezer_location' in validated_data and aliquot_count == 1:
                validated_data['freezer_location'] = freezer_location
            # otherwise create a new freezer location for all other aliquots
            # TODO: this needs to be properly implemented in conjunction with the Freezer Location serializer to ensure that locations are real (i.e., no spot 10 when there can only be 9 spots)
            else:
                freezer_object = Freezer.objects.get(id=freezer)
                freezer_location = FreezerLocation.objects.create(
                    freezer=freezer_object, rack=rack, box=box, row=row, spot=(spot+max_aliquot_number-1))
                validated_data['freezer_location'] = freezer_location

            aliquot = Aliquot.objects.create(**validated_data)
            aliquots.append(aliquot)

        return aliquots

    # ignore submitted data in the case of an update
    def update(self, instance, validated_data):
        return instance

    created_by = serializers.StringRelatedField()
    modified_by = serializers.StringRelatedField()
    aliquot_number = serializers.IntegerField(read_only=True, default=0)
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
                  'aliquot_count', 'freezer', 'rack', 'box', 'row', 'spot',)
        extra_kwargs = {
            'freezer_location': {'required': False}
        }


class AliquotCustomSerializer(serializers.ModelSerializer):
    created_by = serializers.StringRelatedField()
    modified_by = serializers.StringRelatedField()
    freezer_location = FreezerLocationSerializer()
    aliquot_number = serializers.IntegerField(read_only=True, default=0)
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
                  'aliquot_count', 'freezer', 'rack', 'box', 'row', 'spot',)
        extra_kwargs = {
            'freezer_location': {'required': False}
        }
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
    # sample_type
    def get_sample_type(self, obj):
        sample_type_id = obj.sample_type_id
        sample_type = SampleType.objects.get(id=sample_type_id)
        sample_type_name = sample_type.name
        data = {"id": sample_type_id, "name": sample_type_name}
        return data

    # matrix_type
    def get_matrix_type(self, obj):
        matrix_type_id = obj.matrix_type_id
        matrix_type = MatrixType.objects.get(id=matrix_type_id)
        matrix_type_name = matrix_type.name
        data = {"id": matrix_type_id, "name": matrix_type_name}
        return data

    # filter type
    def get_filter_type(self, obj):
        filter_type_id = obj.filter_type_id
        filter_type = FilterType.objects.get(id=filter_type_id)
        filter_type_name = filter_type.name
        data = {"id": filter_type_id, "name": filter_type_name}
        return data

    # study
    def get_study(self, obj):
            study_id = obj.study_id
            study = Study.objects.get(id=study_id)
            study_name = study.name
            data = {"id": study_id, "name": study_name}
            return data

    # sampler name
    def get_sampler_name(self, obj):
        if obj.sampler_name_id is not None:
            sampler_name_id = obj.sampler_name_id
            sampler_name = User.objects.get(id=sampler_name_id)
            sampler_name_name = sampler_name.username if sampler_name is not None else 'Does Not Exist'
            data = {"id": sampler_name_id, "name": sampler_name_name}
        else:
            data = None
        return data

    # peg_neg_targets_extracted
    def get_peg_neg_targets_extracted(self, obj):
        targets_extracted = []
        peg_neg = obj.peg_neg
        if peg_neg is not None:
            peg_neg_id = peg_neg.id
            extractions = peg_neg.extractions.values()

            if extractions is not None:
                for extraction in extractions:
                    replicates = extraction.get('pcrreplicates')
                    if replicates is not None:
                        for replicate in replicates:
                            target_id = replicate.get('target_id')

                            # get the unique target IDs for this peg neg
                            if target_id not in targets_extracted:
                                targets_extracted.append(target_id)

        else:
            peg_neg_id = None

        data = {"id": peg_neg_id, "targets_extracted": targets_extracted}
        return data

    created_by = serializers.StringRelatedField()
    modified_by = serializers.StringRelatedField()
    sample_type = serializers.SerializerMethodField()
    matrix_type = serializers.SerializerMethodField()
    filter_type = serializers.SerializerMethodField()
    study = serializers.SerializerMethodField()
    sampler_name = serializers.SerializerMethodField()
    aliquots = AliquotSerializer(many=True, read_only=True)
    peg_neg_targets_extracted = serializers.SerializerMethodField()
    final_concentrated_sample_volume = serializers.FloatField(
        source='final_concentrated_sample_volume.final_concentrated_sample_volume', read_only=True)
    final_concentrated_sample_volume_type = serializers.StringRelatedField(
        source='final_concentrated_sample_volume.concentration_type.name', read_only=True)
    final_concentrated_sample_volume_notes = serializers.CharField(
        source='final_concentrated_sample_volume.final_concentrated_sample_volume_notes', read_only=True)

    class Meta:
        model = Sample
        fields = ('id', 'sample_type', 'matrix_type', 'filter_type', 'study', 'study_site_name',
                  'collaborator_sample_id', 'sampler_name', 'sample_notes', 'sample_description', 'arrival_date',
                  'arrival_notes', 'collection_start_date', 'collection_start_time', 'collection_end_date',
                  'collection_end_time', 'meter_reading_initial', 'meter_reading_final', 'meter_reading_unit',
                  'total_volume_sampled_initial', 'total_volume_sampled_unit_initial', 'total_volume_or_mass_sampled',
                  'sample_volume_initial', 'sample_volume_filtered', 'filter_born_on_date', 'filter_flag',
                  'secondary_concentration_flag', 'elution_notes', 'technician_initials', 'dissolution_volume',
                  'post_dilution_volume', 'analysisbatches', 'samplegroups', 'peg_neg', 'peg_neg_targets_extracted',
                  'final_concentrated_sample_volume', 'final_concentrated_sample_volume_type',
                  'final_concentrated_sample_volume_notes', 'aliquots',
                  'created_date', 'created_by', 'modified_date', 'modified_by',)


class SampleTypeSerializer(serializers.ModelSerializer):
    created_by = serializers.StringRelatedField()
    modified_by = serializers.StringRelatedField()

    class Meta:
        model = SampleType
        fields = ('id', 'name', 'code', 'created_date', 'created_by', 'modified_date', 'modified_by',)


class MatrixTypeSerializer(serializers.ModelSerializer):
    created_by = serializers.StringRelatedField()
    modified_by = serializers.StringRelatedField()

    class Meta:
        model = MatrixType
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
        fields = ('id', 'name', 'description', 'created_date', 'created_by', 'modified_date', 'modified_by',)


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

    # ignore submitted data in the case of an update
    def update(self, instance, validated_data):
        return instance

    class Meta:
        model = FinalConcentratedSampleVolume
        fields = ('id', 'sample', 'concentration_type', 'final_concentrated_sample_volume',
                  'final_concentrated_sample_volume_notes',
                  'created_date', 'created_by', 'modified_date', 'modified_by',)


class FinalConcentratedSampleVolumeSerializer(serializers.ModelSerializer):
    created_by = serializers.StringRelatedField()
    modified_by = serializers.StringRelatedField()

    class Meta:
        model = FinalConcentratedSampleVolume
        fields = ('id', 'sample', 'concentration_type', 'final_concentrated_sample_volume',
                  'final_concentrated_sample_volume_notes',
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

    # on create, also create child objects (sample-analysisbacth M:M relates)
    def create(self, validated_data):
        # pull out sample ID list from the request
        if 'samples' in validated_data:
            samples = validated_data.pop('samples')
        else:
            samples = []

        # create the Analysis Batch object
        analysis_batch = AnalysisBatch.objects.create(**validated_data)

        # create a Sample Analysis Batch object for each sample ID submitted
        if samples:
            for sample in samples:
                SampleAnalysisBatch.objects.create(analysis_batch=analysis_batch, **sample)

        return analysis_batch

    # on update, also update child objects (sample-analysisbacth M:M relates), including additions and deletions
    def update(self, instance, validated_data):
        # get the old (current) sample ID list for this Analysis Batch
        old_samples = Sample.objects.filter(analysisbatches=instance.id)

        # pull out sample ID list from the request
        if 'samples' in self.initial_data:
            new_sample_ids = self.initial_data['samples']
            new_samples = Sample.objects.filter(id__in=new_sample_ids)
        else:
            new_samples = []

        # update the Analysis Batch object
        instance.analysis_batch_description = validated_data.get('analysis_batch_description',
                                                                 instance.analysis_batch_description)
        instance.analysis_batch_notes = validated_data.get('analysis_batch_notes', instance.analysis_batch_notes)
        instance.save()

        # identify and delete relates where sample IDs are present in old list but not new list
        delete_samples = list(set(old_samples) - set(new_samples))
        for sample_id in delete_samples:
            delete_sample = SampleAnalysisBatch.objects.filter(analysis_batch=instance, sample=sample_id)
            delete_sample.delete()

        # identify and create relates where sample IDs are present in new list but not old list
        add_samples = list(set(new_samples) - set(old_samples))
        for sample_id in add_samples:
            SampleAnalysisBatch.objects.create(analysis_batch=instance, sample=sample_id)

        return instance

    class Meta:
        model = AnalysisBatch
        fields = ('id', 'samples', 'analysis_batch_description', 'analysis_batch_notes',
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
    # TODO: implement control records creation (ext_pos_dna, ext_pos_rna, ext_neg, rt_pos, rt_neg, pcr_pos, pcr_neg)
    created_by = serializers.StringRelatedField()
    modified_by = serializers.StringRelatedField()
    extraction_number = serializers.IntegerField(read_only=True, default=0)
    extractions = serializers.PrimaryKeyRelatedField(read_only=True, many=True)
    inhibitions = serializers.PrimaryKeyRelatedField(read_only=True, many=True)
    new_rt = serializers.JSONField(write_only=True)
    new_replicates = serializers.ListField(write_only=True)
    new_extractions = serializers.ListField(write_only=True)

    def validate(self, data):
        if self.context['request'].method == 'POST':
            if 'new_rt' not in data:
                raise serializers.ValidationError('new_rt is a required field')
            if 'new_extractions' not in data:
                raise serializers.ValidationError('new_extractions is a required field')
            if 'new_replicates' not in data:
                raise serializers.ValidationError('new_replicates is a required field')
            if 'new_extractions' in data:
                is_valid = True
                details = []
                for item in data['new_extractions']:
                    if 'inhibition_dna' not in item and 'inhibition_rna' not in item:
                        is_valid = False
                        message = ''
                        if 'sample' in item:
                            message += 'new extraction with sample_id ' + item['sample'] + ' is missing an inhibition; '
                        message += 'inhibition_dna or inhibition_rna is a required field within new_extractions'
                        details.append(message)
                if not is_valid:
                    raise serializers.ValidationError(details)
            if 'new_replicates' in data:
                is_valid = True
                details = []
                for item in data['new_replicates']:
                    if 'count' not in item:
                        message = 'count is a required field within new_replicates'
                        details.append(message)
                    if 'target' not in item:
                        message = 'target is a required field within new_replicates'
                        details.append(message)
                if not is_valid:
                    raise serializers.ValidationError(details)
        if self.context['request'].method == 'PUT':
            if 'extraction_number' not in data or data['extraction_number'] == 0:
                message = 'extraction_number is a required field'
                raise serializers.ValidationError(message)
        return data

    # on create, also create child objects (extractions and replicates)
    def create(self, validated_data):
        # pull out child reverse transcription definition from the request
        rt = validated_data.pop('new_rt')

        # pull out child extractions list from the request
        extractions = validated_data.pop('new_extractions')

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
        extraction_batch = ExtractionBatch.objects.create(**validated_data)

        # create the child extractions
        if extractions is not None:
            for extraction in extractions:
                extraction['sample'] = Sample.objects.get(id=extraction['sample'])
                sample = extraction['sample']
                if 'inhibition_dna' in extraction:
                    inhib_dna = extraction['inhibition_dna']
                    user = self.context['request'].user
                    # if inhib_dna is an integer, assume it is an existing Inhibition ID
                    if isinstance(inhib_dna, int):
                        extraction['inhibition_dna'] = Inhibition.objects.get(id=inhib_dna)
                    else:
                        # otherwise assume inhib_dna is a date string
                        dna = NucleicAcidType.objects.get(id=1)
                        try:
                            datetime.strptime(inhib_dna, '%Y-%m-%d')

                            extraction['inhibition_dna'] = Inhibition.objects.create(extraction_batch=extraction_batch,
                                                                                     sample=sample,
                                                                                     inhibition_date=inhib_dna,
                                                                                     nucleic_acid_type=dna,
                                                                                     created_by=user,
                                                                                     modified_by=user)
                        # if inhib_dna is not a date string, assign it today's date
                        except ValueError:
                            today = datetime.today().strftime('%Y-%m-%d')
                            extraction['inhibition_dna'] = Inhibition.objects.create(extraction_batch=extraction_batch,
                                                                                     sample=sample,
                                                                                     inhibition_date=today,
                                                                                     nucleic_acid_type=dna,
                                                                                     created_by=user,
                                                                                     modified_by=user)
                if 'inhibition_rna' in extraction:
                    inhib_rna = extraction['inhibition_rna']
                    # if inhib_rna is an integer, assume it is an existing Inhibition ID
                    if isinstance(inhib_rna, int):
                        extraction['inhibition_rna'] = Inhibition.objects.get(id=inhib_rna)
                    else:
                        # otherwise assume inhib_rna is a date string
                        rna = NucleicAcidType.objects.get(id=1)
                        try:
                            datetime.strptime(inhib_rna, '%Y-%m-%d')
                            extraction['inhibition_rna'] = Inhibition.objects.create(extraction_batch=extraction_batch,
                                                                                     sample=sample,
                                                                                     inhibition_date=inhib_rna,
                                                                                     nucleic_acid_type=rna,
                                                                                     created_by=user,
                                                                                     modified_by=user)
                        # if inhib_rna is not a date string, assign it today's date
                        except ValueError:
                            today = datetime.today().strftime('%Y-%m-%d')
                            extraction['inhibition_rna'] = Inhibition.objects.create(extraction_batch=extraction_batch,
                                                                                     sample=sample,
                                                                                     inhibition_date=today,
                                                                                     nucleic_acid_type=rna,
                                                                                     created_by=user,
                                                                                     modified_by=user)

                new_extraction = Extraction.objects.create(extraction_batch=extraction_batch, **extraction)
                # create the child replicates
                if replicates is not None:
                    for replicate in replicates:
                        for x in range(1, replicate['count']):
                            target = Target.objects.get(id=replicate['target'])
                            PCRReplicate.objects.create(extraction=new_extraction, target=target, replicate_number=x)

        # create the child reverse transcription if present
        if rt is not None:
            ReverseTranscription.objects.create(extraction_batch=extraction_batch, **rt)

        return extraction_batch

    # on update, any submitted nested objects (extractions, replicates) will be ignored
    def update(self, instance, validated_data):
        # remove child reverse transcription definition from the request
        if 'new_rt' in validated_data:
            validated_data.pop('new_rt')

        # remove child extractions list from the request
        if 'new_extractions' in validated_data:
            validated_data.pop('new_extractions')

        # remove child replicates list from the request
        if 'new_replicates' in validated_data:
            validated_data.pop('new_replicates')

        # ensure extraction_number is never zero
        if 'extraction_number' in validated_data and validated_data['extraction_number'] == 0:
            validated_data['extraction_number'] = instance.extraction_number

        # update the Extraction Batch object
        # extraction_batch = ExtractionBatch.objects.update(**validated_data)
        instance.analysis_batch = validated_data.get('analysis_batch', instance.analysis_batch)
        instance.extraction_method = validated_data.get('extraction_method', instance.extraction_method)
        instance.reextraction = validated_data.get('reextraction', instance.reextraction)
        instance.reextraction_note = validated_data.get('reextraction_note', instance.reextraction_note)
        instance.extraction_number = validated_data.get('extraction_number', instance.extraction_number)
        instance.extraction_volume = validated_data.get('extraction_volume', instance.extraction_volume)
        instance.extraction_date = validated_data.get('extraction_date', instance.extraction_date)
        instance.pcr_date = validated_data.get('pcr_date', instance.pcr_date)
        instance.template_volume = validated_data.get('template_volume', instance.template_volume)
        instance.elution_volume = validated_data.get('elution_volume', instance.elution_volume)
        instance.sample_dilution_factor = validated_data.get('sample_dilution_factor', instance.sample_dilution_factor)
        instance.reaction_volume = validated_data.get('reaction_volume', instance.reaction_volume)
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
        fields = ('id', 'extraction_string', 'analysis_batch', 'extraction_method', 'reextraction', 'reextraction_note',
                  'extraction_number', 'extraction_volume', 'extraction_date', 'pcr_date', 'template_volume',
                  'elution_volume', 'sample_dilution_factor', 'reaction_volume', 'extractions', 'inhibitions',
                  'created_date', 'created_by', 'modified_date', 'modified_by',
                  'new_rt', 'new_replicates', 'new_extractions')


class ReverseTranscriptionSerializer(serializers.ModelSerializer):
    created_by = serializers.StringRelatedField()
    modified_by = serializers.StringRelatedField()

    class Meta:
        model = ReverseTranscription
        fields = ('id', 'extraction_batch', 'template_volume', 'reaction_volume', 'rt_date', 're_rt', 're_rt_note',
                  'created_date', 'created_by', 'modified_date', 'modified_by',)


class ExtractionSerializer(serializers.ModelSerializer):
    created_by = serializers.StringRelatedField()
    modified_by = serializers.StringRelatedField()

    class Meta:
        model = Extraction
        fields = ('id', 'sample', 'extraction_batch', 'inhibition_dna', 'inhibition_rna', 'pcrreplicates',
                  'created_date', 'created_by', 'modified_date', 'modified_by',)


class PCRReplicateSerializer(serializers.ModelSerializer):
    created_by = serializers.StringRelatedField()
    modified_by = serializers.StringRelatedField()

    class Meta:
        model = PCRReplicate
        fields = ('id', 'extraction', 'target', 'replicate_number', 'record_type', 'cq_value', 'gc_reaction',
                  'replicate_concentration', 'concentration_unit', 'bad_result_flag', 'control_type', 're_pcr',
                  'created_date', 'created_by', 'modified_date', 'modified_by',)


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

        # if isinstance(validated_data, list):
        #     print("is list")
        #     inhibitions = []
        #     for item in validated_data:
        #         print(item)
        #         print(type(item))
        #         inhibition = Inhibition.objects.create(**item)
        #         inhibitions.append(inhibition)
        #     return inhibitions
        # else:
        #     return Inhibition.objects.create(**validated_data)

    # ignore submitted data in the case of an update
    def update(self, instance, validated_data):
        return instance

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
        if 'inhibition_positive_control_cq_value' not in data:
            raise serializers.ValidationError("inhibition_positive_control_cq_value is required.")
        if 'inhibitions' not in data:
            raise serializers.ValidationError("inhibitions is required.")
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
                message = 'An inhibition with analysis_batch_id of (' + ab + ') '
                message += 'and sample_id of (' + sample + ') '
                message += 'and nucleic_acid_type of (' + na + ') does not exist in the database.'
                details.append(message)
            elif inhib.nucleic_acid_type != na:
                is_valid = False
                message = 'Sample ' + sample + ': '
                message += 'The submitted nucleic_acid_type (' + inhib.nucleic_acid_type + ') '
                message += 'does not match the existing value (' + na + ') in the database.'
                details.append(message)
        if not is_valid:
            raise serializers.ValidationError(details)
        return data

    created_by = serializers.StringRelatedField()
    modified_by = serializers.StringRelatedField()
    analysis_batch = serializers.IntegerField(write_only=True)
    extraction_number = serializers.IntegerField(write_only=True)
    inhibition_positive_control_cq_value = serializers.FloatField(write_only=True)
    inhibitions = serializers.ListField(write_only=True)
    sample = serializers.IntegerField(read_only=True)
    suggested_dilution_factor = serializers.FloatField(read_only=True)

    class Meta:
        model = Inhibition
        fields = ('id', 'sample', 'analysis_batch', 'extraction_number', 'inhibition_date', 'nucleic_acid_type', 'dilution_factor',
                  'inhibition_positive_control_cq_value', 'inhibitions', 'suggested_dilution_factor',
                  'created_date', 'created_by', 'modified_date', 'modified_by',)


class ControlTypeSerializer(serializers.ModelSerializer):
    created_by = serializers.StringRelatedField()
    modified_by = serializers.StringRelatedField()

    class Meta:
        model = ControlType
        fields = ('id', 'name', 'abbreviation', 'created_date', 'created_by', 'modified_date', 'modified_by',)


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

    # matrix_type
    def get_matrix_type(self, obj):
        matrix_type_id = obj.matrix_type_id
        matrix_type = MatrixType.objects.get(id=matrix_type_id)
        matrix_type_name = matrix_type.name
        data = {"id": matrix_type_id, "name": matrix_type_name}
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
    matrix_type = serializers.SerializerMethodField()
    study = serializers.SerializerMethodField()

    class Meta:
        model = Sample
        fields = ('id', 'sample_type', 'matrix_type', 'study', 'collaborator_sample_id', 'sample_description',
                  'created_date', 'created_by', 'modified_date', 'modified_by',)


class AnalysisBatchExtractionBatchSerializer(serializers.ModelSerializer):
    created_by = serializers.StringRelatedField()
    modified_by = serializers.StringRelatedField()

    def get_inhibitions(self, obj):
        inhibitions = {}
        extractions = obj.extractions.values()

        if extractions is not None:
            for extraction in extractions:
                sample_id = extraction.get('sample_id')
                if sample_id is not None:
                    sample = Sample.objects.get(id=sample_id)
                    sample_inhibitions = sample.inhibitions.values()
                    if sample_inhibitions is not None:
                        for inhibition in sample_inhibitions:
                            creator = User.objects.get(id=inhibition['created_by_id'])
                            modifier = User.objects.get(id=inhibition['modified_by_id'])
                            data = {'id': inhibition['id'], 'sample': inhibition['sample_id'],
                                    'extraction_batch': inhibition['extraction_batch_id'],
                                    'inhibition_date': inhibition['inhibition_date'],
                                    'nucleic_acid_type_id': inhibition['nucleic_acid_type_id'],
                                    'dilution_factor': inhibition['dilution_factor'],
                                    'created_date': inhibition['created_date'],
                                    'created_by': creator.username if creator is not None else None,
                                    'modified_date': inhibition['modified_date'],
                                    'modified_by': modifier.username if modifier is not None else None}
                            inhibitions[inhibition['id']] = data

        return inhibitions.values()

    def get_reverse_transcriptions(self, obj):
        reverse_transcriptions = {}
        reversetranscriptions = obj.reversetranscriptions.values()

        if reversetranscriptions is not None:
            for reversetranscription in reversetranscriptions:
                reverse_transcription_id = reversetranscription.get('id')
                rt = ReverseTranscription.objects.get(id=reverse_transcription_id)
                data = {'id': reverse_transcription_id, 'extraction_batch': rt.extraction_batch.id,
                        'template_volume': rt.template_volume, 'reaction_volume': rt.reaction_volume,
                        'rt_date': rt.rt_date, 're_rt': rt.re_rt, 'created_date': rt.created_date,
                        'created_by': rt.created_by.username if rt.created_by is not None else None,
                        'modified_date': rt.modified_date,
                        'modified_by': rt.modified_by.username if rt.modified_by is not None else None}
                reverse_transcriptions[reverse_transcription_id] = data

        return reverse_transcriptions.values()

    def get_targets(self, obj):
        targets = {}
        extractions = obj.extractions.values()

        if extractions is not None:
            for extraction in extractions:
                replicates = extraction.get('pcrreplicates')
                if replicates is not None:
                    for replicate in replicates:
                        target_id = replicate.get('target_id')

                        # count the number of replicates associated with each target
                        if targets.get(target_id, None) is not None:
                            data = targets[target_id]
                            data['replicates'] += 1
                        else:
                            target = Target.objects.get(id=target_id)
                            data = {'id': target_id, 'name': target.name, 'abbrevation': target.abbreviation,
                                    'type': target.type, 'replicates': 1}
                        targets[target_id] = data

        return targets.values()

    # extraction_method
    def get_extraction_method(self, obj):
        extraction_method_id = obj.extraction_method_id
        extraction_method = ExtractionMethod.objects.get(id=extraction_method_id)
        extraction_method_name = extraction_method.name
        data = {"id": extraction_method_id, "name": extraction_method_name}
        return data

    extractions = ExtractionSerializer(many=True, read_only=True)
    inhibitions = serializers.SerializerMethodField()
    reverse_transcriptions = serializers.SerializerMethodField()
    targets = serializers.SerializerMethodField()
    extraction_method = serializers.SerializerMethodField()

    class Meta:
        model = ExtractionBatch
        fields = ('id', 'extraction_method', 'reextraction', 'reextraction_note',
                  'extraction_number', 'extraction_volume', 'elution_volume', 'extraction_date',
                  'extractions', 'inhibitions', 'reverse_transcriptions', 'targets',
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

    extractionbatches = AnalysisBatchExtractionBatchSerializer(many=True, read_only=True)
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

    # summary: extraction count, inhibition count, reverse transcription count, target count
    def get_summary(self, obj):
        summary = {}
        extraction_count = 0
        inhibition_count = 0
        reverse_transcription_count = 0
        targets = []

        # extraction and reverse_transcription count
        extraction_batches = obj.extractionbatches.values()
        if extraction_batches is not None:
            for extraction_batch in extraction_batches:
                extraction_batch_id = extraction_batch.get('id')

                extractions = Extraction.objects.filter(extraction_batch__exact=extraction_batch_id)
                extraction_count += len(extractions)

                reversetranscriptions = ReverseTranscription.objects.filter(extraction_batch__exact=extraction_batch_id)
                reverse_transcription_count += len(reversetranscriptions)

                inhibitions = Inhibition.objects.filter(extraction_batch__exact=extraction_batch_id)
                inhibition_count += len(inhibitions)

                # target count
                if extractions is not None:
                    for extraction in extractions:
                        replicates = PCRReplicate.objects.filter(extraction__exact=extraction.id)
                        if replicates is not None:
                            for replicate in replicates:
                                target = replicate.target
                                if target not in targets:
                                    targets.append(replicate.target)

        summary['extraction_count'] = extraction_count
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
