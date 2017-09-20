from django.contrib.auth import authenticate, login, logout
from rest_framework import views, viewsets, generics, permissions, authentication, status
from rest_framework.response import Response
from lideservices.serializers import *
from lideservices.models import *
from lideservices.permissions import *


########################################################################################################################
#
#  copyright: 2017 WiM - USGS
#  authors: Aaron Stephenson USGS WiM (Web Informatics and Mapping)
#
#  In Django, a view is what takes a Web request and returns a Web response. The response can be many things, but most
#  of the time it will be a Web page, a redirect, or a document. In this case, the response will almost always be data
#  in JSON format.
#
#  All these views are written as Class-Based Views (https://docs.djangoproject.com/en/1.11/topics/class-based-views/)
#  because that is the paradigm used by Django Rest Framework (http://www.django-rest-framework.org/api-guide/views/)
#  which is the toolkit we used to create web services in Django.
#
#
########################################################################################################################


######
#
#  Abstract Base Classes
#
######


class HistoryViewSet(viewsets.ModelViewSet):
    """
    This class will automatically assign the User ID to the created_by and modified_by history fields when appropriate
    """

    permission_classes = (permissions.IsAuthenticated,)

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)
        serializer.save(modified_by=self.request.user)

    def perform_update(self, serializer):
        serializer.save(modified_by=self.request.user)


######
#
#  Samples
#
######


class SampleViewSet(HistoryViewSet):
    queryset = Sample.objects.all()
    serializer_class = SampleSerializer


class AliquotViewSet(HistoryViewSet):
    queryset = Aliquot.objects.all()
    serializer_class = AliquotSerializer


class SampleTypeViewSet(HistoryViewSet):
    queryset = SampleType.objects.all()
    serializer_class = SampleTypeSerializer


class MatrixTypeViewSet(HistoryViewSet):
    queryset = MatrixType.objects.all()
    serializer_class = MatrixTypeSerializer


class FilterTypeViewSet(HistoryViewSet):
    queryset = FilterType.objects.all()
    serializer_class = FilterTypeSerializer


class StudyViewSet(HistoryViewSet):
    queryset = Study.objects.all()
    serializer_class = StudySerializer


class UnitTypeViewSet(HistoryViewSet):
    queryset = UnitType.objects.all()
    serializer_class = UnitTypeSerializer


######
#
#  Freezer Locations
#
######


class FreezerLocationViewSet(HistoryViewSet):
    queryset = FreezerLocation.objects.all()
    serializer_class = FreezerLocationSerializer


class FreezerViewSet(HistoryViewSet):
    queryset = Freezer.objects.all()
    serializer_class = FreezerSerializer


######
#
#  Concentrated Sample Volumes
#
######


class FinalConcentratedSampleVolumeViewSet(HistoryViewSet):
    queryset = FinalConcentratedSampleVolume.objects.all()
    serializer_class = FinalConcentratedSampleVolumeSerializer


class ConcentrationTypeViewSet(HistoryViewSet):
    queryset = ConcentrationType.objects.all()
    serializer_class = ConcentrationTypeSerializer


######
#
#  Sample Groups
#
######


class SampleSampleGroupViewSet(HistoryViewSet):
    queryset = SampleSampleGroup.objects.all()
    serializer_class = SampleSampleGroupSerializer


class SampleGroupViewSet(HistoryViewSet):
    queryset = SampleGroup.objects.all()
    serializer_class = SampleGroupSerializer


######
#
#  Analyses
#
######


class AnalysisBatchViewSet(HistoryViewSet):
    queryset = AnalysisBatch.objects.all()
    serializer_class = AnalysisBatchSerializer
	
class AnalysisBatchDetailViewSet(HistoryViewSet):
    queryset = AnalysisBatch.objects.all()
    serializer_class = AnalysisBatchDetailSerializer

	# override the default queryset to allow filtering by URL arguments
    def get_queryset(self):
        queryset = AnalysisBatch.objects.all()
        batch = self.request.query_params.get('id', None)
        if batch is not None:
        	queryset = queryset.filter(id__exact=batch)
        return queryset	


class AnalysisBatchTemplateViewSet(HistoryViewSet):
    queryset = AnalysisBatchTemplate.objects.all()
    serializer_class = AnalysisBatchTemplateSerializer


class ExtractionViewSet(HistoryViewSet):
    queryset = Extraction.objects.all()
    serializer_class = ExtractionSerializer
	
class ExtractionMethodViewSet(HistoryViewSet):
    queryset = ExtractionMethod.objects.all()
    serializer_class = ExtractionMethodSerializer		


class InhibitionViewSet(HistoryViewSet):
    queryset = Inhibition.objects.all()
    serializer_class = InhibitionSerializer


class ReverseTranscriptionViewSet(HistoryViewSet):
    queryset = ReverseTranscription.objects.all()
    serializer_class = ReverseTranscriptionSerializer


class PCRReplicateViewSet(HistoryViewSet):
    queryset = PCRReplicate.objects.all()
    serializer_class = PCRReplicateSerializer


class StandardCurveViewSet(HistoryViewSet):
    queryset = StandardCurve.objects.all()
    serializer_class = StandardCurveSerializer


class TargetViewSet(HistoryViewSet):
    queryset = Target.objects.all()
    serializer_class = TargetSerializer


######
#
#  Controls
#
######


class ControlTypeViewSet(HistoryViewSet):
    queryset = ControlType.objects.all()
    serializer_class = ControlTypeSerializer


class ControlViewSet(HistoryViewSet):
    queryset = Control.objects.all()
    serializer_class = ControlSerializer


######
#
#  Misc
#
######


class OtherAnalysisViewSet(HistoryViewSet):
    queryset = OtherAnalysis.objects.all()
    serializer_class = OtherAnalysisSerializer


######
#
#  Users
#
######


class UserViewSet(HistoryViewSet):
    serializer_class = UserSerializer

    def get_queryset(self):
        # do not return the admin and public users
        queryset = User.objects.all().exclude(id__in=[1])
        # filter by username, exact
        username = self.request.query_params.get('username', None)
        if username is not None:
            queryset = queryset.filter(username__exact=username)
        return queryset


class AuthView(views.APIView):
    authentication_classes = (authentication.BasicAuthentication,)
    serializer_class = UserSerializer

    def post(self, request):
        return Response(self.serializer_class(request.user).data)