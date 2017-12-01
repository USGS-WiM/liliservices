from django.contrib import admin
from lideservices.models import *
from simple_history.admin import SimpleHistoryAdmin


admin.site.register(Sample, SimpleHistoryAdmin)
admin.site.register(SampleType, SimpleHistoryAdmin)
admin.site.register(MatrixType, SimpleHistoryAdmin)
admin.site.register(FilterType, SimpleHistoryAdmin)
admin.site.register(Study, SimpleHistoryAdmin)
admin.site.register(Unit, SimpleHistoryAdmin)
admin.site.register(SampleAnalysisBatch, SimpleHistoryAdmin)
admin.site.register(AnalysisBatch, SimpleHistoryAdmin)
admin.site.register(Extraction, SimpleHistoryAdmin)
admin.site.register(ExtractionBatch, SimpleHistoryAdmin)
admin.site.register(Inhibition, SimpleHistoryAdmin)
admin.site.register(ReverseTranscription, SimpleHistoryAdmin)
admin.site.register(PCRReplicate, SimpleHistoryAdmin)
admin.site.register(StandardCurve, SimpleHistoryAdmin)
admin.site.register(Target, SimpleHistoryAdmin)
admin.site.register(Result, SimpleHistoryAdmin)
admin.site.register(ControlType, SimpleHistoryAdmin)
admin.site.register(OtherAnalysis, SimpleHistoryAdmin)