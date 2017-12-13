import json
from django.http import HttpResponse, JsonResponse
from django.contrib.auth import authenticate, login, logout
from rest_framework import views, viewsets, generics, permissions, authentication, status
from rest_framework.response import Response
from rest_framework.parsers import JSONParser
from lideservices.serializers import *
from lideservices.models import *
from lideservices.permissions import *
from django.db.models import Max


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
    serializer_class = AliquotCustomSerializer

    # def get_serializer_class(self):
    #     if self.request.data:
    #         if "aliquot_count" in self.request.data:
    #             return AliquotListSerializer
    #     else:
    #         return AliquotSerializer

    def get_serializer(self, *args, **kwargs):
        if "data" in kwargs:
            data = kwargs["data"]

            # check if many is required
            if isinstance(data, list) and "aliquot_count" in data[0]:
                kwargs["many"] = True

        return super(AliquotViewSet, self).get_serializer(*args, **kwargs)


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


class UnitViewSet(HistoryViewSet):
    queryset = Unit.objects.all()
    serializer_class = UnitSerializer


######
#
#  Freezer Locations
#
######


class FreezerLocationViewSet(HistoryViewSet):
    serializer_class = FreezerLocationSerializer

    # get the last occupied location
    def get_last_occupied_id(self):
        max_freezer = FreezerLocation.objects.aggregate(Max('freezer'))
        max_rack = FreezerLocation.objects.filter(freezer__exact=max_freezer['freezer__max']).aggregate(Max('rack'))
        max_box = FreezerLocation.objects.filter(
            freezer__exact=max_freezer['freezer__max'], rack__exact=max_rack['rack__max']).aggregate(Max('box'))
        max_row = FreezerLocation.objects.filter(
            freezer__exact=max_freezer['freezer__max'], rack__exact=max_rack['rack__max'],
            box__exact=max_box['box__max']).aggregate(Max('row'))
        max_spot = FreezerLocation.objects.filter(
            freezer__exact=max_freezer['freezer__max'], rack__exact=max_rack['rack__max'],
            box__exact=max_box['box__max'], row__exact=max_row['row__max']).aggregate(Max('spot'))
        last_occupied = FreezerLocation.objects.filter(
            freezer__exact=max_freezer['freezer__max'], rack__exact=max_rack['rack__max'],
            box__exact=max_box['box__max'], row__exact=max_row['row__max'], spot__exact=max_spot['spot__max'])
        return last_occupied[0].id

    def get_queryset(self):
        queryset = FreezerLocation.objects.all()
        last_occupied = self.request.query_params.get('last_occupied', None)
        if last_occupied is not None:
            if last_occupied == 'True' or last_occupied == 'true':
                queryset = queryset.filter(id__exact=self.get_last_occupied_id())
        return queryset


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

    def get_serializer(self, *args, **kwargs):
        if "data" in kwargs:
            data = kwargs["data"]

            # check if many is required
            if isinstance(data, list):
                kwargs["many"] = True

        return super(FinalConcentratedSampleVolumeViewSet, self).get_serializer(*args, **kwargs)


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


class SampleAnalysisBatchViewSet(HistoryViewSet):
    queryset = SampleAnalysisBatch.objects.all()
    serializer_class = SampleAnalysisBatchSerializer


class AnalysisBatchViewSet(HistoryViewSet):
    queryset = AnalysisBatch.objects.all()
    serializer_class = AnalysisBatchSerializer


class AnalysisBatchDetailViewSet(HistoryViewSet):
    serializer_class = AnalysisBatchDetailSerializer

    # override the default queryset to allow filtering by URL arguments
    def get_queryset(self):
        queryset = AnalysisBatch.objects.all()
        batch = self.request.query_params.get('id', None)
        if batch is not None:
            queryset = queryset.filter(id__exact=batch)
        return queryset	


class AnalysisBatchSummaryViewSet(HistoryViewSet):
    queryset = AnalysisBatch.objects.all()
    serializer_class = AnalysisBatchSummarySerializer	


class AnalysisBatchTemplateViewSet(HistoryViewSet):
    queryset = AnalysisBatchTemplate.objects.all()
    serializer_class = AnalysisBatchTemplateSerializer


######
#
#  Extractions
#
######


class ExtractionMethodViewSet(HistoryViewSet):
    queryset = ExtractionMethod.objects.all()
    serializer_class = ExtractionMethodSerializer


class ExtractionBatchViewSet(HistoryViewSet):
    queryset = ExtractionBatch.objects.all()
    serializer_class = ExtractionBatchSerializer


class ReverseTranscriptionViewSet(HistoryViewSet):
    queryset = ReverseTranscription.objects.all()
    serializer_class = ReverseTranscriptionSerializer


class ExtractionViewSet(HistoryViewSet):
    queryset = Extraction.objects.all()
    serializer_class = ExtractionSerializer


class PCRReplicateViewSet(HistoryViewSet):
    queryset = PCRReplicate.objects.all()
    serializer_class = PCRReplicateSerializer


class ResultViewSet(HistoryViewSet):
    queryset = Result.objects.all()
    serializer_class = ResultSerializer


class StandardCurveViewSet(HistoryViewSet):
    queryset = StandardCurve.objects.all()
    serializer_class = StandardCurveSerializer


class InhibitionViewSet(HistoryViewSet):
    queryset = Inhibition.objects.all()
    serializer_class = InhibitionSerializer

    def get_serializer(self, *args, **kwargs):
        if "data" in kwargs:
            data = kwargs["data"]

            # check if many is required
            if isinstance(data, list):
                kwargs["many"] = True

        return super(InhibitionViewSet, self).get_serializer(*args, **kwargs)


class SampleInhibitionViewSet(HistoryViewSet):
    serializer_class = SampleInhibitionSerializer

    # override the default queryset to allow filtering by URL arguments
    # if sample ID is in query, only search by sample ID and ignore other params
    def get_queryset(self):
        queryset = Sample.objects.all()
        # filter by sample IDs, exact list
        sample = self.request.query_params.get('id', None)
        if sample is not None:
            sample_list = sample.split(',')
            queryset = queryset.filter(id__in=sample_list)
        # else, search by other params (that don't include sample ID)
        else:
            # filter by analysis batch ID, exact
            analysis_batch = self.request.query_params.get('analysis_batch', None)
            if analysis_batch is not None:
                queryset = queryset.filter(analysis_batches__in=analysis_batch)
        return queryset


class InhibitionCalculateDilutionFactorViewSet(views.APIView):
    permission_classes = (permissions.IsAuthenticated,)

    def post(self, request):
        response_data = []
        request_data = JSONParser().parse(request)
        serializer = InhibitionCalculateDilutionFactorSerializer(data=request_data)
        if serializer.is_valid():
            pos = request_data['inhibition_positive_control_cq_value']
            inhibitions = request_data['inhibitions']
            for inhibition in inhibitions:
                cq = inhibition['cq_value']
                suggested_dilution_factor = None
                if 0 < pos - cq < 1:
                    suggested_dilution_factor = 1
                if cq > pos and cq - pos < 2:
                    suggested_dilution_factor = 1
                if cq - pos >= 2 and cq <= 36:
                    suggested_dilution_factor = 5
                if cq > 36 or cq is None:
                    suggested_dilution_factor = 10
                new_data = {"sample": inhibition['sample'], "suggested_dilution_factor": suggested_dilution_factor}
                response_data.append(new_data)
            return JsonResponse(serializer.data, status=200)
        return JsonResponse(serializer.errors, status=400)


class TargetViewSet(HistoryViewSet):
    queryset = Target.objects.all()
    serializer_class = TargetSerializer


class ControlTypeViewSet(HistoryViewSet):
    queryset = ControlType.objects.all()
    serializer_class = ControlTypeSerializer


######
#
#  Misc
#
######


class FieldUnitViewSet(HistoryViewSet):
    queryset = FieldUnit.objects.all()
    serializer_class = FieldUnitSerializer


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
