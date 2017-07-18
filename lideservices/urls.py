from django.conf.urls import url, include
from lideservices import views
from rest_framework.routers import DefaultRouter


router = DefaultRouter()

router.register(r'samples', views.SampleViewSet, 'samples')
router.register(r'sampletypes', views.SampleTypeViewSet, 'sampletypes')
router.register(r'matrixtypes', views.MatrixTypeViewSet, 'matrixtypes')
router.register(r'filtertypes', views.FilterTypeViewSet, 'filtertypes')
router.register(r'studies', views.StudyViewSet, 'studies')
router.register(r'unittypes', views.UnitTypeViewSet, 'unittypes')
router.register(r'samplegroups', views.SampleGroupViewSet, 'samplegroups')
router.register(r'analysisbatches', views.AnalysisBatchViewSet, 'analysisbatches')
router.register(r'extractions', views.ExtractionViewSet, 'extractions')
router.register(r'inhibitions', views.InhibitionViewSet, 'inhibitions')
router.register(r'reversetranscriptions', views.ReverseTranscriptionViewSet, 'reversetranscriptions')
router.register(r'pcrreplicates', views.PCRReplicateViewSet, 'pcrreplicates')
router.register(r'standardcurves', views.StandardCurveViewSet, 'standardcurves')
router.register(r'targets', views.TargetViewSet, 'targets')
router.register(r'controltypes', views.ControlTypeViewSet, 'controltypes')
router.register(r'controls', views.ControlViewSet, 'controls')
router.register(r'otheranalyses', views.OtherAnalysisViewSet, 'otheranalyses')
router.register(r'users', views.UserViewSet, 'users')

urlpatterns = [
    url(r'^', include(router.urls)),
    url(r'^api-auth/', include('rest_framework.urls', namespace='rest_framework')),
    url(r'^auth/$', views.AuthView.as_view(), name='authenticate')
]