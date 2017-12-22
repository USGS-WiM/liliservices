from django.conf.urls import url, include
from lideservices import views
from rest_framework.routers import DefaultRouter


router = DefaultRouter()

router.register(r'samples', views.SampleViewSet, 'samples')
router.register(r'aliquots', views.AliquotViewSet, 'aliquots')
router.register(r'sampletypes', views.SampleTypeViewSet, 'sampletypes')
router.register(r'matrixtypes', views.MatrixTypeViewSet, 'matrixtypes')
router.register(r'filtertypes', views.FilterTypeViewSet, 'filtertypes')
router.register(r'studies', views.StudyViewSet, 'studies')
router.register(r'units', views.UnitViewSet, 'units')
router.register(r'freezerlocations', views.FreezerLocationViewSet, 'freezerlocations')
router.register(r'freezers', views.FreezerViewSet, 'freezers')
router.register(r'finalconcentratedsamplevolumes', views.FinalConcentratedSampleVolumeViewSet,
                'finalconcentratedsamplevolumes')
router.register(r'concentrationtype', views.ConcentrationTypeViewSet, 'concentrationtype')
router.register(r'samplegroups', views.SampleGroupViewSet, 'samplegroups')
router.register(r'sampleinhibitions', views.SampleInhibitionViewSet, 'sampleinhibitions')
router.register(r'sampleanalysisbatches', views.SampleAnalysisBatchViewSet, 'sampleanalysisbatches')
router.register(r'analysisbatches', views.AnalysisBatchViewSet, 'analysisbatches')
router.register(r'analysisbatchdetail', views.AnalysisBatchDetailViewSet, 'analysisbatchdetail')
router.register(r'analysisbatchsummary', views.AnalysisBatchSummaryViewSet, 'analysisbatchsummary')
router.register(r'analysisbatchtemplates', views.AnalysisBatchTemplateViewSet, 'analysisbatchtemplates')
router.register(r'inhibitions', views.InhibitionViewSet, 'inhibitions')
router.register(r'extractionmethods', views.ExtractionMethodViewSet, 'extractionmethods')
router.register(r'extractionbatches', views.ExtractionBatchViewSet, 'extractionbatches')
router.register(r'extractions', views.ExtractionViewSet, 'extractions')
router.register(r'pcrreplicates', views.PCRReplicateViewSet, 'pcrreplicates')
router.register(r'reversetranscriptions', views.ReverseTranscriptionViewSet, 'reversetranscriptions')
router.register(r'standardcurves', views.StandardCurveViewSet, 'standardcurves')
router.register(r'targets', views.TargetViewSet, 'targets')
router.register(r'results', views.ResultViewSet, 'results')
router.register(r'controltypes', views.ControlTypeViewSet, 'controltypes')
router.register(r'fieldunits', views.FieldUnitViewSet, 'fieldunits')
router.register(r'otheranalyses', views.OtherAnalysisViewSet, 'otheranalyses')
router.register(r'users', views.UserViewSet, 'users')

urlpatterns = [
    url(r'^', include(router.urls)),
    url(r'^api-auth/', include('rest_framework.urls', namespace='rest_framework')),
    url(r'^auth/$', views.AuthView.as_view(), name='authenticate'),
    url(r'^inhibitionscalculatedilutionfactor/$', views.InhibitionCalculateDilutionFactorView.as_view(),
        name='inhibitionscalculatedilutionfactor'),
    url(r'^pcrreplicateresultsupload/$', views.PCRReplicateResultsUploadView.as_view(),
        name='pcrreplicateresultsupload'),
]