from django.contrib import admin
from lideservices.models import *


admin.site.register(Sample, SimpleHistoryAdmin)
admin.site.register(SampleType, SimpleHistoryAdmin)
admin.site.register(SampleEnvironment, SimpleHistoryAdmin)
admin.site.register(SampleLocation, SimpleHistoryAdmin)
admin.site.register(FilterType, SimpleHistoryAdmin)
admin.site.register(WaterType, SimpleHistoryAdmin)
admin.site.register(Study, SimpleHistoryAdmin)
admin.site.register(AnalysisBatch, SimpleHistoryAdmin)
admin.site.register(Extraction, SimpleHistoryAdmin)
admin.site.register(Inhibition, SimpleHistoryAdmin)
admin.site.register(ReverseTranscription, SimpleHistoryAdmin)
admin.site.register(PCRReplicate, SimpleHistoryAdmin)
admin.site.register(StandardCurve, SimpleHistoryAdmin)
admin.site.register(Target, SimpleHistoryAdmin)
admin.site.register(ControlType, SimpleHistoryAdmin)
admin.site.register(Control, SimpleHistoryAdmin)
admin.site.register(OtherAnalysis, SimpleHistoryAdmin)