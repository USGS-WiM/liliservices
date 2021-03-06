from django.contrib import admin
from liliapi.models import *
from simple_history.admin import SimpleHistoryAdmin


admin.site.register(Sample, SimpleHistoryAdmin)
admin.site.register(Aliquot, SimpleHistoryAdmin)
admin.site.register(SampleType, SimpleHistoryAdmin)
admin.site.register(Matrix, SimpleHistoryAdmin)
admin.site.register(FilterType, SimpleHistoryAdmin)
admin.site.register(Study, SimpleHistoryAdmin)
admin.site.register(Unit, SimpleHistoryAdmin)
admin.site.register(FreezerLocation, SimpleHistoryAdmin)
admin.site.register(Freezer, SimpleHistoryAdmin)
admin.site.register(FinalConcentratedSampleVolume, SimpleHistoryAdmin)
admin.site.register(ConcentrationType, SimpleHistoryAdmin)
admin.site.register(FinalSampleMeanConcentration, SimpleHistoryAdmin)
admin.site.register(SampleSampleGroup, SimpleHistoryAdmin)
admin.site.register(SampleGroup, SimpleHistoryAdmin)
admin.site.register(SampleAnalysisBatch, SimpleHistoryAdmin)
admin.site.register(AnalysisBatch, SimpleHistoryAdmin)
admin.site.register(AnalysisBatchTemplate, SimpleHistoryAdmin)
admin.site.register(ExtractionMethod, SimpleHistoryAdmin)
admin.site.register(ExtractionBatch, SimpleHistoryAdmin)
admin.site.register(ReverseTranscription, SimpleHistoryAdmin)
admin.site.register(SampleExtraction, SimpleHistoryAdmin)
admin.site.register(PCRReplicateBatch, SimpleHistoryAdmin)
admin.site.register(PCRReplicate, SimpleHistoryAdmin)
admin.site.register(StandardCurve, SimpleHistoryAdmin)
admin.site.register(Inhibition, SimpleHistoryAdmin)
admin.site.register(Target, SimpleHistoryAdmin)
admin.site.register(FieldUnit, SimpleHistoryAdmin)
admin.site.register(NucleicAcidType, SimpleHistoryAdmin)
admin.site.register(RecordType, SimpleHistoryAdmin)
admin.site.register(OtherAnalysis, SimpleHistoryAdmin)
