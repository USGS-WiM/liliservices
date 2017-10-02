from rest_framework import serializers
from lideservices.models import *
from enumchoicefield import ChoiceEnum, EnumChoiceField


######
#
#  Samples
#
######


class SampleSerializer(serializers.ModelSerializer):

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
                  'final_concentrated_sample_volume_notes',
                  'created_date', 'created_by', 'modified_date', 'modified_by',)


class AliquotSerializer(serializers.ModelSerializer):

    class Meta:
        model = Aliquot
        fields = ('id', 'sample', 'freezer_location', 'aliquot', 'frozen',
                  'created_date', 'created_by', 'modified_date', 'modified_by',)


class SampleTypeSerializer(serializers.ModelSerializer):

    class Meta:
        model = SampleType
        fields = ('id', 'name', 'code', 'created_date', 'created_by', 'modified_date', 'modified_by',)


class MatrixTypeSerializer(serializers.ModelSerializer):

    class Meta:
        model = MatrixType
        fields = ('id', 'name', 'code', 'created_date', 'created_by', 'modified_date', 'modified_by',)


class FilterTypeSerializer(serializers.ModelSerializer):

    class Meta:
        model = FilterType
        fields = ('id', 'name', 'matrix',  'created_date', 'created_by', 'modified_date', 'modified_by',)


class StudySerializer(serializers.ModelSerializer):

    class Meta:
        model = Study
        fields = ('id', 'name', 'description', 'created_date', 'created_by', 'modified_date', 'modified_by',)


class UnitTypeSerializer(serializers.ModelSerializer):

    class Meta:
        model = UnitType
        fields = ('id', 'name', 'description', 'created_date', 'created_by', 'modified_date', 'modified_by',)


######
#
#  Freezer Locations
#
######


class FreezerLocationSerializer(serializers.ModelSerializer):

    class Meta:
        model = FreezerLocation
        fields = ('id', 'freezer', 'rack', 'box', 'row', 'spot',
                  'created_date', 'created_by', 'modified_date', 'modified_by',)


class FreezerSerializer(serializers.ModelSerializer):

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

    class Meta:
        model = FinalConcentratedSampleVolume
        fields = ('id', 'sample', 'concentration_type', 'final_concentrated_sample_volume',
                  'final_concentrated_sample_volume_notes',
                  'created_date', 'created_by', 'modified_date', 'modified_by',)


class ConcentrationTypeSerializer(serializers.ModelSerializer):

    class Meta:
        model = ConcentrationType
        fields = ('id', 'name', 'created_date', 'created_by', 'modified_date', 'modified_by',)


######
#
#  Sample Groups
#
######


class SampleSampleGroupSerializer(serializers.ModelSerializer):

    class Meta:
        model = UnitType
        fields = ('id', 'sample', 'samplegroup', 'created_date', 'created_by', 'modified_date', 'modified_by',)


class SampleGroupSerializer(serializers.ModelSerializer):

    class Meta:
        model = UnitType
        fields = ('id', 'name', 'description', 'created_date', 'created_by', 'modified_date', 'modified_by',)


######
#
#  Analyses
#
######


class AnalysisBatchSerializer(serializers.ModelSerializer):

    class Meta:
        model = AnalysisBatch
        fields = ('id', 'samples', 'analysis_batch_description', 'analysis_batch_notes',
                  'created_date', 'created_by', 'modified_date', 'modified_by',)


class AnalysisBatchTemplateSerializer(serializers.ModelSerializer):

    class Meta:
        model = AnalysisBatchTemplate
        fields = ('id', 'name', 'target', 'description', 'extraction_volume', 'elution_volume',
                  'created_date', 'created_by', 'modified_date', 'modified_by',)


class InhibitionBatchSerializer(serializers.ModelSerializer):
    type = EnumChoiceField(enum_class=NucleicAcidType)

    class Meta:
        model = InhibitionBatch
        fields = ('id', 'analysis_batch', 'inhibition_number', 'type', 'inhibition_date', 'inhibitions',
                  'created_date', 'created_by', 'modified_date', 'modified_by',)


class InhibitionSerializer(serializers.ModelSerializer):

    class Meta:
        model = Inhibition
        fields = ('id', 'sample', 'inhibition_batch', 'dilution_factor',
                  'created_date', 'created_by', 'modified_date', 'modified_by',)


class ExtractionMethodSerializer(serializers.ModelSerializer):

    class Meta:
        model = ExtractionMethod
        fields = ('id', 'name',)


class ExtractionBatchSerializer(serializers.ModelSerializer):

    class Meta:
        model = Extraction
        fields = ('id', 'analysis_batch', 'extraction_method', 'reextraction', 'reextraction_note', 'extraction_number',
                  'extraction_volume', 'elution_volume', 'extraction_date', 'extractions',
                  'created_date', 'created_by', 'modified_date', 'modified_by',)


class ExtractionSerializer(serializers.ModelSerializer):

    class Meta:
        model = Extraction
        fields = ('id', 'sample', 'extraction_batch', 'inhibition', 'reverse_transcription', 'dilution_factor',
                  'created_date', 'created_by', 'modified_date', 'modified_by',)


class PCRReplicateSerializer(serializers.ModelSerializer):

    class Meta:
        model = PCRReplicate
        fields = ('id', 'extraction', 'target', 'cq_value', 'gc_reaction', 'concentration', 'sample_mean_concentration',
                  'concentration_unit', 'bad_result_flag', 'pcr_date', 'template_volume',
                  'created_date', 'created_by', 'modified_date', 'modified_by',)


class ReverseTranscriptionSerializer(serializers.ModelSerializer):

    class Meta:
        model = ReverseTranscription
        fields = ('id', 'analysis_batch', 'rt_number', 'template_volume', 'reaction_volume', 'cq_value', 'rt_date',
                  'created_date', 'created_by', 'modified_date', 'modified_by',)


class StandardCurveSerializer(serializers.ModelSerializer):

    class Meta:
        model = StandardCurve
        fields = ('id', 'r_value', 'slope', 'efficiency', 'created_date', 'created_by', 'modified_date', 'modified_by',)


class TargetSerializer(serializers.ModelSerializer):
    type = EnumChoiceField(enum_class=NucleicAcidType)

    class Meta:
        model = Target
        fields = ('id', 'name', 'medium', 'code', 'type', 'created_date', 'created_by', 'modified_date', 'modified_by',)


class TargetMediumSerializer(serializers.ModelSerializer):

    class Meta:
        model = TargetMedium
        fields = ('id', 'name')


######
#
#  Controls
#
######


class ControlTypeSerializer(serializers.ModelSerializer):

    class Meta:
        model = ControlType
        fields = ('id', 'name', 'abbreviation', 'created_date', 'created_by', 'modified_date', 'modified_by',)


class ControlSerializer(serializers.ModelSerializer):

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

    class Meta:
        model = Sample
        fields = ('id', 'sample_type', 'sample_description')


class SampleInhibitionSerializer(serializers.ModelSerializer):
    inhibitions = InhibitionSerializer(many=True, read_only=True)

    class Meta:
        model = Sample
        fields = ('id', 'sample_type', 'sample_description', 'inhibitions',)


class AnalysisBatchExtractionSerializer(serializers.ModelSerializer):
    # targets
    def get_targets(self, obj):
        targets = {}
        vals = obj.pcrreplicates.values()

        for val in vals:
            target_id = val.get('target_id')
            target = Target.objects.get(id=target_id)
            target_name = target.name
            target_abbreviation = target.abbreviation
            target_type = target.type

            # count the number of replicates associated with each target
            if targets.get(target_id, None) is not None:
                data = targets[target_id]
                data['replicates'] += 1
            else:
                data = {'id': target_id, 'name': target_name, 'abbrevation': target_abbreviation,
                        'type': target_type, 'replicates': 1}
            targets[target_id] = data

        return targets.values()

    inhibitions = InhibitionSerializer(many=True, read_only=True)
    reverse_transcriptions = ReverseTranscriptionSerializer(many=True, read_only=True)
    targets = serializers.SerializerMethodField()

    class Meta:
        model = Extraction
        fields = ('id', 'extraction_number', 'extraction_volume', 'elution_volume', 'extraction_method',
                  'inhibitions', 'reverse_transcriptions', 'targets', 'extraction_date',
                  'created_date', 'created_by', 'modified_date', 'modified_by',)


class AnalysisBatchDetailSerializer(serializers.ModelSerializer):
    # studies
    def get_studies(self, obj):
        studies = []
        vals = obj.samples.values()
        for val in vals:
            study_id = val.get('study_id')
            study = Study.objects.get(id=study_id)
            study_name = study.name
            study_description = study.description
            data = {'id': study_id, 'name': study_name, 'description': study_description}
            studies.append(data)
        return studies

    extractions = AnalysisBatchExtractionSerializer(many=True, read_only=True)
    samples = SimpleSampleSerializer(many=True, read_only=True)
    studies = serializers.SerializerMethodField()
    created_by = serializers.StringRelatedField()
    modified_by = serializers.StringRelatedField()

    class Meta:
        model = AnalysisBatch
        fields = ('id', 'analysis_batch_description', 'analysis_batch_notes', 'samples', 'studies', 'extractions',
                  'created_date', 'created_by', 'modified_date', 'modified_by',)


class AnalysisBatchSummarySerializer(serializers.ModelSerializer):
    # studies
    def get_studies(self, obj):
        studies = []
        vals = obj.samples.values()
        for val in vals:
            study_id = val.get('study_id')
            studies.append(study_id)
        return studies

    # summary: extraction count, inhibition count, reverse transcription count, target count
    def get_summary(self, obj):
        summary = {}
        inhibition_count = 0
        reverse_transcription_count = 0
        targets = []

        extractions = obj.extractions.values()

        # extraction count
        extraction_count = len(extractions)

        for val in extractions:
            extraction_id = val.get('id')

            # inhibition count
            inhibition_count += len(Inhibition.objects.filter(extraction=extraction_id))

            # reverse transcription count
            reverse_transcription_count += len(ReverseTranscription.objects.filter(extraction=extraction_id))

            # target count
            replicates = PCRReplicate.objects.filter(extraction=extraction_id)
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
    created_by = serializers.StringRelatedField()
    modified_by = serializers.StringRelatedField()

    class Meta:
        model = AnalysisBatch
        fields = ('id', 'analysis_batch_description', 'analysis_batch_notes', 'studies', 'summary',
                  'created_date', 'created_by', 'modified_date', 'modified_by',)


class AnalysisBatchSampleInhibitionSerializer(serializers.ModelSerializer):
    samples = SampleInhibitionSerializer(many=True, read_only=True)

    class Meta:
        model = AnalysisBatch
        fields = ('samples',)
