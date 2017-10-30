from rest_framework import serializers
from lideservices.models import *
from enumchoicefield import ChoiceEnum, EnumChoiceField


######
#
#  Samples
#
######


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
        sampler_name_id = obj.sampler_name_id
        sampler_name = User.objects.get(id=sampler_name_id)
        sampler_name_name = sampler_name.username
        data = {"id": sampler_name_id, "name": sampler_name_name}
        return data

    created_by = serializers.StringRelatedField()
    modified_by = serializers.StringRelatedField()
    sample_type = serializers.SerializerMethodField()
    matrix_type = serializers.SerializerMethodField()
    filter_type = serializers.SerializerMethodField()
    study = serializers.SerializerMethodField()
    sampler_name = serializers.SerializerMethodField()
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
                  'total_volume_sampled_initial', 'total_volume_sampled_unit_initial', 'total_volume_sampled',
                  'sample_volume_initial', 'sample_volume_filtered', 'filter_born_on_date', 'filter_flag',
                  'secondary_concentration_flag', 'elution_date', 'elution_notes', 'technician_initials',
                  'air_subsample_volume', 'post_dilution_volume', 'pump_flow_rate', 'analysisbatches',
                  'final_concentrated_sample_volume', 'final_concentrated_sample_volume_type',
                  'final_concentrated_sample_volume_notes', 'aliquots',
                  'created_date', 'created_by', 'modified_date', 'modified_by',)


class AliquotSerializer(serializers.ModelSerializer):
    created_by = serializers.StringRelatedField()
    modified_by = serializers.StringRelatedField()

    def create(self, validated_data):
        # create the Aliquot object
        # but first determine if any aliquots exist for the parent sample
        prev_aliquots = Aliquot.objects.filter(sample=validated_data['sample'])
        if prev_aliquots:
            max_aliquot_number = max(prev_aliquot.aliquot_number for prev_aliquot in prev_aliquots)
        else:
            max_aliquot_number = 0
        validated_data['aliquot_number'] = max_aliquot_number + 1
        aliquot = Aliquot.objects.create(**validated_data)

        return aliquot

    class Meta:
        model = Aliquot
        fields = ('id', 'aliquot_string', 'sample', 'freezer_location', 'aliquot_number', 'frozen',
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


class UnitTypeSerializer(serializers.ModelSerializer):
    created_by = serializers.StringRelatedField()
    modified_by = serializers.StringRelatedField()

    class Meta:
        model = UnitType
        fields = ('id', 'name', 'description', 'created_date', 'created_by', 'modified_date', 'modified_by',)


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
#  Concentrated Sample Volumes
#
######


class FinalConcentratedSampleVolumeSerializer(serializers.ModelSerializer):
    created_by = serializers.StringRelatedField()
    modified_by = serializers.StringRelatedField()

    class Meta:
        model = FinalConcentratedSampleVolume
        fields = ('id', 'sample', 'concentration_type', 'final_concentrated_sample_volume',
                  'final_concentrated_sample_volume_notes',
                  'created_date', 'created_by', 'modified_date', 'modified_by',)


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
        model = UnitType
        fields = ('id', 'sample', 'samplegroup', 'created_date', 'created_by', 'modified_date', 'modified_by',)


class SampleGroupSerializer(serializers.ModelSerializer):
    created_by = serializers.StringRelatedField()
    modified_by = serializers.StringRelatedField()

    class Meta:
        model = UnitType
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
        samples = validated_data.pop('samples')

        # create the Analysis Batch object
        analysis_batch = AnalysisBatch.objects.create(**validated_data)

        # create a Sample Analysis Batch object for each sample ID submitted
        for sample in samples:
            SampleAnalysisBatch.objects.create(analysis_batch=analysis_batch, **sample)

        return analysis_batch

    # on update, also update child objects (sample-analysisbacth M:M relates), including additions and deletions
    def update(self, instance, validated_data):
        # get the old (current) sample ID list for this Analysis Batch
        old_samples = Sample.objects.filter(analysisbatches=instance.id)

        # pull out sample ID list from the request
        new_samples = validated_data.pop('samples')

        # update the Analysis Batch object
        analysis_batch = AnalysisBatch.objects.update(**validated_data)

        # identify and delete relates where sample IDs are present in old list but not new list
        delete_samples = list(set(old_samples) - set(new_samples))
        for sample in delete_samples:
            delete_sample = SampleAnalysisBatch.objects.filter(analysis_batch=analysis_batch, **sample)
            delete_sample.delete()

        # identify and create relates where sample IDs are present in new list but not old list
        add_samples = list(set(new_samples) - set(old_samples))
        for sample in add_samples:
            SampleAnalysisBatch.objects.create(analysis_batch=analysis_batch, **sample)

        return analysis_batch

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


class InhibitionBatchSerializer(serializers.ModelSerializer):
    created_by = serializers.StringRelatedField()
    modified_by = serializers.StringRelatedField()
    type = EnumChoiceField(enum_class=NucleicAcidType)

    # on create, also create child objects (inhibitions)
    def create(self, validated_data):
        # pull out child inhibitions list from the request
        inhibitions = validated_data.pop('inhibitions')

        # create the Inhibition Batch object
        # but first determine if any inhibition batches exist for the parent analysis batch
        prev_inhib_batches = InhibitionBatch.objects.filter(analysis_batch=validated_data['analysis_batch'])
        if prev_inhib_batches:
            max_inhibition_number = max(prev_inhib_batch.inhibition_number for prev_inhib_batch in prev_inhib_batches)
        else:
            max_inhibition_number = 0
        validated_data['inhibition_number'] = max_inhibition_number + 1
        inhibition_batch = InhibitionBatch.objects.create(**validated_data)

        # create the child inhibitions
        for inhibition in inhibitions:
            Inhibition.objects.create(inhibition_batch=inhibition_batch, **inhibition)

        return inhibition_batch

    # on update, any submitted nested objects (inhibitions) will be ignored
    def update(self, instance, validated_data):
        # remove child inhibitions list from the request
        if hasattr(validated_data, 'inhibitions'):
            validated_data.remove('inhibitions')

        # update the Inhibition Batch object
        inhibition_batch = InhibitionBatch.objects.update(**validated_data)

        return inhibition_batch

    class Meta:
        model = InhibitionBatch
        fields = ('id', 'inhibition_string', 'analysis_batch', 'inhibition_number', 'type', 'inhibition_date',
                  'inhibitions', 'created_date', 'created_by', 'modified_date', 'modified_by',)


class InhibitionSerializer(serializers.ModelSerializer):
    created_by = serializers.StringRelatedField()
    modified_by = serializers.StringRelatedField()

    class Meta:
        model = Inhibition
        fields = ('id', 'sample', 'inhibition_batch', 'dilution_factor',
                  'created_date', 'created_by', 'modified_date', 'modified_by',)


class ExtractionMethodSerializer(serializers.ModelSerializer):

    class Meta:
        model = ExtractionMethod
        fields = ('id', 'name', 'created_date', 'created_by', 'modified_date', 'modified_by',)


class ExtractionBatchSerializer(serializers.ModelSerializer):
    created_by = serializers.StringRelatedField()
    modified_by = serializers.StringRelatedField()

    # on create, also create child objects (extractions and replicates)
    def create(self, validated_data):
        # pull out child extractions list from the request
        extractions = validated_data.pop('extractions')

        # pull out child replicates list from the request
        replicates = validated_data.pop('replicates')

        # create the Extraction Batch object
        # but first determine if any extraction batches exist for the parent analysis batch
        prev_extr_batches = ExtractionBatch.objects.filter(analysis_batch=validated_data['analysis_batch'])
        if prev_extr_batches:
            max_extraction_number = max(prev_extr_batch.inhibition_number for prev_extr_batch in prev_extr_batches)
        else:
            max_extraction_number = 0
        validated_data['extraction_number'] = max_extraction_number + 1
        extraction_batch = ExtractionBatch.objects.create(**validated_data)

        # create the child extractions
        for extraction in extractions:
            new_extraction = Extraction.objects.create(extraction_batch=extraction_batch, **extraction)
            # create the child replicates
            for replicate in replicates:
                for x in range(1, replicate.count):
                    PCRReplicate.objects.create(extraction=new_extraction, target=replicate.target)

        return extraction_batch

    # on update, any submitted nested objects (extractions, replicates) will be ignored
    def update(self, instance, validated_data):
        # remove child extractions list from the request
        if hasattr(validated_data, 'extractions'):
            validated_data.remove('extractions')

        # remove child replicates list from the request
        if hasattr(validated_data, 'replicates'):
            validated_data.remove('replicates')

        # update the Extraction Batch object
        extraction_batch = ExtractionBatch.objects.update(**validated_data)

        return extraction_batch

    # extraction_method
    def get_extraction_method(self, obj):
        extraction_method_id = obj.extraction_method_id
        extraction_method = ExtractionMethod.objects.get(id=extraction_method_id)
        extraction_method_name = extraction_method.name
        data = {"id": extraction_method_id, "name": extraction_method_name}
        return data

    class Meta:
        model = ExtractionBatch
        fields = ('id', 'extraction_string', 'analysis_batch', 'extraction_method', 'reextraction', 'reextraction_note',
                  'extraction_number', 'extraction_volume', 'extraction_date', 'pcr_date', 'template_volume',
                  'elution_volume', 'dilution_factor', 'extractions',
                  'created_date', 'created_by', 'modified_date', 'modified_by',)


class ExtractionSerializer(serializers.ModelSerializer):
    created_by = serializers.StringRelatedField()
    modified_by = serializers.StringRelatedField()

    class Meta:
        model = Extraction
        fields = ('id', 'sample', 'extraction_batch', 'inhibition', 'reverse_transcription',
                  'created_date', 'created_by', 'modified_date', 'modified_by',)


class PCRReplicateSerializer(serializers.ModelSerializer):
    created_by = serializers.StringRelatedField()
    modified_by = serializers.StringRelatedField()

    class Meta:
        model = PCRReplicate
        fields = ('id', 'extraction', 'target', 'cq_value', 'gc_reaction', 'concentration', 'sample_mean_concentration',
                  'concentration_unit', 'bad_result_flag',
                  'created_date', 'created_by', 'modified_date', 'modified_by',)


class ReverseTranscriptionSerializer(serializers.ModelSerializer):
    created_by = serializers.StringRelatedField()
    modified_by = serializers.StringRelatedField()

    def create(self, validated_data):
        # create the Reverse Transcription object
        # but first determine if any reverse transcriptions exist for the parent analysis batch
        prev_rts = ReverseTranscription.objects.filter(analysis_batch=validated_data['analysis_batch'])
        if prev_rts:
            max_rt_number = max(prev_rt.inhibition_number for prev_rt in prev_rts)
        else:
            max_rt_number = 0
        validated_data['rt_number'] = max_rt_number + 1
        extraction_batch = ReverseTranscription.objects.create(**validated_data)

        return extraction_batch

    class Meta:
        model = ReverseTranscription
        fields = ('id', 'rt_string', 'analysis_batch', 'rt_number', 'template_volume', 'reaction_volume', 'rt_date',
                  'created_date', 'created_by', 'modified_date', 'modified_by',)


class StandardCurveSerializer(serializers.ModelSerializer):
    created_by = serializers.StringRelatedField()
    modified_by = serializers.StringRelatedField()

    class Meta:
        model = StandardCurve
        fields = ('id', 'r_value', 'slope', 'efficiency', 'created_date', 'created_by', 'modified_date', 'modified_by',)


class TargetSerializer(serializers.ModelSerializer):
    # medium
    def get_medium(self, obj):
        medium_id = obj.medium_id
        medium = TargetMedium.objects.get(id=medium_id)
        medium_name = medium.name
        data = {"id": medium_id, "name": medium_name}
        return data

    created_by = serializers.StringRelatedField()
    modified_by = serializers.StringRelatedField()
    type = EnumChoiceField(enum_class=NucleicAcidType)
    medium = serializers.SerializerMethodField()

    class Meta:
        model = Target
        fields = ('id', 'name', 'medium', 'code', 'type', 'created_date', 'created_by', 'modified_date', 'modified_by',)


class TargetMediumSerializer(serializers.ModelSerializer):
    created_by = serializers.StringRelatedField()
    modified_by = serializers.StringRelatedField()

    class Meta:
        model = TargetMedium
        fields = ('id', 'name', 'created_date', 'created_by', 'modified_date', 'modified_by',)


######
#
#  Controls
#
######


class ControlTypeSerializer(serializers.ModelSerializer):
    created_by = serializers.StringRelatedField()
    modified_by = serializers.StringRelatedField()

    class Meta:
        model = ControlType
        fields = ('id', 'name', 'abbreviation', 'created_date', 'created_by', 'modified_date', 'modified_by',)


class ControlSerializer(serializers.ModelSerializer):
    created_by = serializers.StringRelatedField()
    modified_by = serializers.StringRelatedField()

    class Meta:
        model = Control
        fields = ('id', 'type', 'extraction', 'target', 'qc_value', 'qc_flag',
                  'created_date', 'created_by', 'modified_date', 'modified_by',)


######
#
#  Misc
#
######


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


class SampleInhibitionSerializer(serializers.ModelSerializer):
    created_by = serializers.StringRelatedField()
    modified_by = serializers.StringRelatedField()
    inhibitions = InhibitionSerializer(many=True, read_only=True)

    class Meta:
        model = Sample
        fields = ('id', 'sample_type', 'sample_description', 'inhibitions',
                  'created_date', 'created_by', 'modified_date', 'modified_by',)


class AnalysisBatchExtractionBatchSerializer(serializers.ModelSerializer):
    created_by = serializers.StringRelatedField()
    modified_by = serializers.StringRelatedField()

    def get_inhibitions(self, obj):
        inhibitions = {}
        extractions = obj.extractions.values()

        for extraction in extractions:
            inhibition_id = extraction.get('inhibition_id')
            inhibition = Inhibition.objects.get(id=inhibition_id)
            inhibitions[inhibition_id] = inhibition

        return inhibitions.values()

    def get_reverse_transcriptions(self, obj):
        reverse_transcriptions = {}
        extractions = obj.extractions.values()

        for extraction in extractions:
            reverse_transcription_id = extraction.get('reverse_transcription_id')
            reverse_transcription = ReverseTranscription.objects.get(id=reverse_transcription_id)
            reverse_transcriptions[reverse_transcription_id] = reverse_transcription

        return reverse_transcriptions.values()

    def get_targets(self, obj):
        targets = {}
        extractions = obj.extractions.values()

        for extraction in extractions:
            replicates = extraction.get('pcrreplicates')
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

    extractions = ExtractionSerializer(many=True, read_only=True)
    inhibitions = serializers.SerializerMethodField()
    reverse_transcriptions = serializers.SerializerMethodField()
    targets = serializers.SerializerMethodField()

    # extraction_method
    def get_extraction_method(self, obj):
        extraction_method_id = obj.extraction_method_id
        extraction_method = ExtractionMethod.objects.get(id=extraction_method_id)
        extraction_method_name = extraction_method.name
        data = {"id": extraction_method_id, "name": extraction_method_name}
        return data

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
        for val in vals:
            study_id = val.get('study_id')
            study = Study.objects.get(id=study_id)
            study_name = study.name
            study_description = study.description
            data = {"id": study_id, "name": study_name, "description": study_description}
            studies.append(data)
        return studies

    extraction_batches = AnalysisBatchExtractionBatchSerializer(many=True, read_only=True)
    samples = SimpleSampleSerializer(many=True, read_only=True)
    studies = serializers.SerializerMethodField()

    class Meta:
        model = AnalysisBatch
        fields = ('id', 'analysis_batch_description', 'analysis_batch_notes', 'samples', 'studies',
                  'extraction_batches', 'created_date', 'created_by', 'modified_date', 'modified_by',)


class AnalysisBatchSummarySerializer(serializers.ModelSerializer):
    created_by = serializers.StringRelatedField()
    modified_by = serializers.StringRelatedField()

    # studies
    def get_studies(self, obj):
        studies = []
        vals = obj.samples.values()
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
        targets = []

        # extraction count
        extraction_batches = obj.extractionbatches.values()
        for extraction_batch in extraction_batches:
            extraction_batch_id = extraction_batch.get('id')

            extractions = Extraction.objects.filter(extraction_batch__exact=extraction_batch_id)
            extraction_count += len(extractions)

            # target count
            for extraction in extractions:
                replicates = PCRReplicate.objects.filter(extraction__exact=extraction.id)
                for replicate in replicates:
                    target = replicate.target
                    if target not in targets:
                        targets.append(replicate.target)

        # inhibition count
        inhibition_batches = obj.inhibitionbatches.values()
        for inhibition_batch in inhibition_batches:
            inhibition_batch_id = inhibition_batch.get('id')

            inhibitions = Inhibition.objects.filter(inhibition_batch__exact=inhibition_batch_id)
            inhibition_count += len(inhibitions)

        # reverse transcription count
        reverse_transcription_count = len(obj.reversetranscriptions.values())

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
