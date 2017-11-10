from rest_framework import serializers
from lideservices.models import *
from enumchoicefield import ChoiceEnum, EnumChoiceField


######
#
#  Samples
#
######


class AliquotSerializer(serializers.ModelSerializer):
    created_by = serializers.StringRelatedField()
    modified_by = serializers.StringRelatedField()

    # bulk create
    def create(self, validated_data):
        # aliquots = [Aliquot(**item) for item in validated_data]
        # return Aliquot.objects.bulk_create(aliquots)

        # pull out the freezer location fields from the request
        freezer = validated_data.pop('freezer')
        rack = validated_data.pop('rack')
        box = validated_data.pop('box')
        row = validated_data.pop('row')
        spot = validated_data.pop('spot')

        # pull out sample ID list from the request
        if 'aliquot_count' in validated_data:
            aliquot_count = validated_data.pop('aliquot_count')
        else:
            aliquot_count = 1

        aliquots = []
        for count_num in range(0, aliquot_count):
            # first determine if any aliquots exist for the parent sample
            prev_aliquots = Aliquot.objects.filter(sample=validated_data['sample'])
            if prev_aliquots:
                max_aliquot_number = max(prev_aliquot.aliquot_number for prev_aliquot in prev_aliquots)
            else:
                max_aliquot_number = 0
            validated_data['aliquot_number'] = max_aliquot_number + 1

            # then create the freezer location for this aliquot to use
            # TODO: this needs to be properly implemented in conjunction with the Freezer Location serializer
            freezer_location = FreezerLocation.objects.create(
                freezer=freezer, rack=rack, box=box, row=row, spot=(spot+max_aliquot_number-1))
            validated_data['freezer_location'] = freezer_location

            aliquot = Aliquot.objects.create(**validated_data)
            aliquots.append(aliquot)

        if aliquot_count == 1:
            return aliquots[0]
        else:
            return aliquots

    # ordinary update
    def update(self, instance, validated_data):
        return instance

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
    aliquots = AliquotSerializer(many=True, read_only=True)
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
                  'post_dilution_volume', 'analysisbatches', 'samplegroups', 'peg_neg',
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


class FinalConcentratedSampleVolumeListSerializer(serializers.ListSerializer):
    created_by = serializers.StringRelatedField()
    modified_by = serializers.StringRelatedField()

    def create(self, validated_data):
        fcsvs = [FinalConcentratedSampleVolume(**item) for item in validated_data]
        return FinalConcentratedSampleVolume.objects.bulk_create(fcsvs)

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


class InhibitionSerializer(serializers.ModelSerializer):
    created_by = serializers.StringRelatedField()
    modified_by = serializers.StringRelatedField()

    class Meta:
        model = Inhibition
        fields = ('id', 'sample', 'analysis_batch', 'inhibition_date', 'type', 'dilution_factor',
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
        # pull out child reverse transcription definition from the request
        rt = validated_data.pop('rt')

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
        if extractions is not None:
            for extraction in extractions:
                new_extraction = Extraction.objects.create(extraction_batch=extraction_batch, **extraction)
                # create the child replicates
                if replicates is not None:
                    for replicate in replicates:
                        for x in range(1, replicate.count):
                            PCRReplicate.objects.create(extraction=new_extraction, target=replicate.target)

        # create the child reverse transcription if present
        if rt is not None:
            ReverseTranscription.objects.create(extraction_batch=extraction_batch, **rt)

        return extraction_batch

    # on update, any submitted nested objects (extractions, replicates) will be ignored
    def update(self, instance, validated_data):
        # remove child reverse transcription definition from the request
        if hasattr(validated_data, 'rt'):
            validated_data.remove('rt')

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
                  'elution_volume', 'sample_dilution_factor', 'reaction_volume', 'extractions',
                  'created_date', 'created_by', 'modified_date', 'modified_by',)


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
        fields = ('id', 'sample', 'extraction_batch', 'inhibition', 'pcrreplicates',
                  'created_date', 'created_by', 'modified_date', 'modified_by',)


class PCRReplicateSerializer(serializers.ModelSerializer):
    created_by = serializers.StringRelatedField()
    modified_by = serializers.StringRelatedField()

    class Meta:
        model = PCRReplicate
        fields = ('id', 'extraction', 'target', 'cq_value', 'gc_reaction', 'replicate_concentration',
                  'concentration_unit', 'bad_result_flag', 'control_type', 're_pcr', 'replicate_type',
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


class TargetSerializer(serializers.ModelSerializer):
    created_by = serializers.StringRelatedField()
    modified_by = serializers.StringRelatedField()
    type = EnumChoiceField(enum_class=NucleicAcidType)

    class Meta:
        model = Target
        fields = ('id', 'name', 'code', 'type', 'notes', 'created_date', 'created_by', 'modified_date', 'modified_by',)


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

        if extractions is not None:
            for extraction in extractions:
                inhibition_id = extraction.get('inhibition_id')
                inhibition = Inhibition.objects.get(id=inhibition_id)
                data = {'id': inhibition_id, 'sample': inhibition.sample.id,
                        'analysis_batch': inhibition.analysis_batch.id, 'inhibition_date': inhibition.inhibition_date,
                        'type': str(inhibition.type), 'dilution_factor': inhibition.dilution_factor,
                        'created_date': inhibition.created_date, 'created_by': inhibition.created_by.username,
                        'modified_date': inhibition.modified_date, 'modified_by': inhibition.modified_by.username}
                inhibitions[inhibition_id] = data

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
                        'created_by': rt.created_by.username, 'modified_date': rt.modified_date,
                        'modified_by': rt.modified_by.username}
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

                # target count
                if extractions is not None:
                    for extraction in extractions:
                        replicates = PCRReplicate.objects.filter(extraction__exact=extraction.id)
                        if replicates is not None:
                            for replicate in replicates:
                                target = replicate.target
                                if target not in targets:
                                    targets.append(replicate.target)

        # inhibition count
        inhibitions = obj.inhibitions.values()
        inhibition_count += len(inhibitions)

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
