from rest_framework import serializers
from lideservices.models import *


######
#
#  Samples
#
######


class SampleSerializer(serializers.ModelSerializer):

    class Meta:
        model = Sample
        fields = ('id', 'sample_type', 'sample_environment', 'sample_location', 'water_type',
        'filter_type', 'study', 'study_site_name', 'study_site_id', 'collaborator_sample_id',
        'sampler_name', 'notes', 'description', 'collect_start_date', 'collect_end_date', 
        'collect_start_time', 'collect_end_time', 'meter_reading_initial', 'meter_reading_final',
        'meter_reading_unit', 'total_volume_sampled_initial', 'total_volume_sampled_unit_initial',
        'total_volume_sampled', 'filtered_volume', 'filter_born_on_date', 'matrix', 'filter_flag',
        'secondary_concentration_flag', 'analysisbatches',)


class SampleTypeSerializer(serializers.ModelSerializer):

    class Meta:
        model = SampleType
        fields = ('id', 'name',)


class SampleEnvironmentSerializer(serializers.ModelSerializer):

    class Meta:
        model = SampleEnvironment
        fields = ('id', 'name',)


class SampleLocationSerializer(serializers.ModelSerializer):

    class Meta:
        model = SampleLocation
        fields = ('id', 'name',)


class FilterTypeSerializer(serializers.ModelSerializer):

    class Meta:
        model = FilterType
        fields = ('id', 'name',)


class WaterTypeSerializer(serializers.ModelSerializer):

    class Meta:
        model = WaterType
        fields = ('id', 'name',)


class StudySerializer(serializers.ModelSerializer):

    class Meta:
        model = Study
        fields = ('id', 'name',)


######
#
#  Analyses
#
######


class AnalysisBatchSerializer(serializers.ModelSerializer):

    class Meta:
        model = AnalysisBatch
        fields = ('id', 'some_field', 'samples',)


class ExtractionSerializer(serializers.ModelSerializer):

    class Meta:
        model = Extraction
        fields = ('id', 'analysis_batch', 'extraction_code', 'extraction_date',)


class InhibitionSerializer(serializers.ModelSerializer):

    class Meta:
        model = Inhibition
        fields = ('id', 'name', 'type', 'dilution')


class ReverseTranscriptionSerializer(serializers.ModelSerializer):

    class Meta:
        model = ReverseTranscription
        fields = ('id', 'name', 'extraction', 'volume_in', 'volume_out', 'cycle_of_quantification',
        'reverse_transcription_date',)


class PCRReplicateSerializer(serializers.ModelSerializer):

    class Meta:
        model = PCRReplicate
        fields = ('id', 'sample', 'extraction', 'inhibition', 'reverse_transcription', 'target',
        'replicate', 'pcr_date', 'cycle_of_quantification', 'gc_rxn', 'concentration',
        'sample_mean_concentration', 'concentration_unit',)


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
        fields = ('id', 'type', 'sample', 'target', 'cycle_of_quantification', 'control_date',)


######
#
#  Misc
#
######


class OtherAnalysisSerializer(serializers.ModelSerializer):

    class Meta:
        model = OtherAnalysis
        fields = ('id', 'description', 'data', 'other_analysis_date',)


######
#
#  Users
#
######


class UserSerializer(serializers.ModelSerializer):

    class Meta:
        model = User
        fields = ('id', 'username', 'first_name', 'last_name', 'email',
                  'groups', 'user_permissions', 'is_superuser', 'is_staff', 'is_active',)
