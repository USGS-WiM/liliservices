from rest_framework import serializers
from lideservices.models import *


######
#
#  Samples
#
######


class SampleSerializer(serializers.ModelSerializer):

    final_concentrated_sample_volume = serializers.FloatField(
        source='final_concentrated_sample_volumes.final_concentrated_sample_volume', read_only=True)
    final_concentrated_sample_volume_type = serializers.StringRelatedField(
        source='final_concentrated_sample_volumes.concentration_type', read_only=True)
    final_concentrated_sample_volume_notes = serializers.CharField(
        source='final_concentrated_sample_volumes.final_concentrated_sample_volume_notes', read_only=True)

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
                  'final_concentrated_sample_volume_notes',)


class AliquotSerializer(serializers.ModelSerializer):

    class Meta:
        model = Aliquot
        fields = ('id', 'sample', 'aliquot', 'frozen', 'freezer_location',)


class SampleTypeSerializer(serializers.ModelSerializer):

    class Meta:
        model = SampleType
        fields = ('id', 'name', 'code',)


class MatrixTypeSerializer(serializers.ModelSerializer):

    class Meta:
        model = MatrixType
        fields = ('id', 'name', 'code',)


class FilterTypeSerializer(serializers.ModelSerializer):

    class Meta:
        model = FilterType
        fields = ('id', 'name', 'matrix',)


class StudySerializer(serializers.ModelSerializer):

    class Meta:
        model = Study
        fields = ('id', 'name', 'description',)


class UnitTypeSerializer(serializers.ModelSerializer):

    class Meta:
        model = UnitType
        fields = ('id', 'name', 'description',)


######
#
#  Freezer Locations
#
######


class FreezerLocationSerializer(serializers.ModelSerializer):

    class Meta:
        model = FreezerLocation
        fields = ('id', 'freezer', 'rack', 'box', 'row', 'spot',)


class FreezerSerializer(serializers.ModelSerializer):

    class Meta:
        model = Freezer
        fields = ('id', 'racks', 'boxes', 'rows', 'spots',)


######
#
#  Concentrated Sample Volumes
#
######


class FinalConcentratedSampleVolumeSerializer(serializers.ModelSerializer):

    class Meta:
        model = FinalConcentratedSampleVolume
        fields = ('id', 'name', 'description',)


class ConcentrationTypeSerializer(serializers.ModelSerializer):

    class Meta:
        model = ConcentrationType
        fields = ('id', 'name', 'description',)


######
#
#  Sample Groups
#
######


class SampleSampleGroupSerializer(serializers.ModelSerializer):

    class Meta:
        model = UnitType
        fields = ('id', 'sample', 'samplegroup',)


class SampleGroupSerializer(serializers.ModelSerializer):

    class Meta:
        model = UnitType
        fields = ('id', 'name', 'description',)


######
#
#  Analyses
#
######


class AnalysisBatchSerializer(serializers.ModelSerializer):

    class Meta:
        model = AnalysisBatch
        fields = ('id', 'some_field', 'samples',)


class AnalysisBatchTemplateSerializer(serializers.ModelSerializer):

    class Meta:
        model = AnalysisBatchTemplate
        fields = ('id', 'description', 'extraction_volume', 'elution_volume', 'target',)


class ExtractionSerializer(serializers.ModelSerializer):

    class Meta:
        model = Extraction
        fields = ('id', 'sample', 'analysis_batch', 'extraction_number', 'extraction_volume', 'elution_volume',
                  'inhibition',)


class InhibitionSerializer(serializers.ModelSerializer):

    class Meta:
        model = Inhibition
        fields = ('id', 'name', 'type', 'dilution', 'extraction',)


class ReverseTranscriptionSerializer(serializers.ModelSerializer):

    class Meta:
        model = ReverseTranscription
        fields = ('id', 'name', 'extraction', 'volume_in', 'volume_out', 'cycle_of_quantification',
                  'reverse_transcription_date',)


class PCRReplicateSerializer(serializers.ModelSerializer):

    class Meta:
        model = PCRReplicate
        fields = ('id', 'extraction', 'inhibition', 'reverse_transcription', 'target', 'replicate',
                  'cycle_of_quantification', 'guanine_cytosine_content_reaction', 'concentration',
                  'concentration_unit',)


class StandardCurveSerializer(serializers.ModelSerializer):

    class Meta:
        model = StandardCurve
        fields = ('id', 'r_value', 'slope', 'efficiency',)


class TargetSerializer(serializers.ModelSerializer):

    class Meta:
        model = Target
        fields = ('id', 'abbreviation', 'type')


######
#
#  Controls
#
######


class ControlTypeSerializer(serializers.ModelSerializer):

    class Meta:
        model = ControlType
        fields = ('id', 'name', 'abbreviation')


class ControlSerializer(serializers.ModelSerializer):

    class Meta:
        model = Control
        fields = ('id', 'type', 'sample', 'target', 'qc_value', 'qc_flag',)


######
#
#  Misc
#
######


class OtherAnalysisSerializer(serializers.ModelSerializer):

    class Meta:
        model = OtherAnalysis
        fields = ('id', 'description', 'data',)


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
