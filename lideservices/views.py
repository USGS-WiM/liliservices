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
        serializer.save(created_by=self.request.user, modified_by=self.request.user)

    def perform_update(self, serializer):
        serializer.save(modified_by=self.request.user)


######
#
#  Samples
#
######


class SampleViewSet(HistoryViewSet):
    serializer_class = SampleSerializer

    # override the default queryset to allow filtering by URL arguments
    def get_queryset(self):
        queryset = Sample.objects.all()
        # filter by sample IDs, exact list
        sample = self.request.query_params.get('id', None)
        if sample is not None:
            sample_list = sample.split(',')
            queryset = queryset.filter(id__in=sample_list)
        return queryset


class AliquotViewSet(HistoryViewSet):
    queryset = Aliquot.objects.all()
    serializer_class = AliquotCustomSerializer

    def get_serializer_class(self):
        if not isinstance(self.request.data, list):
            return AliquotSerializer
        else:
            return self.serializer_class

    def get_serializer(self, *args, **kwargs):
        if 'data' in kwargs:
            data = kwargs['data']

            # check if many is required
            if isinstance(data, list) and 'aliquot_count' in data[0]:
                kwargs['many'] = True

        return super(AliquotViewSet, self).get_serializer(*args, **kwargs)


class SampleTypeViewSet(HistoryViewSet):
    queryset = SampleType.objects.all()
    serializer_class = SampleTypeSerializer


class MatrixViewSet(HistoryViewSet):
    queryset = Matrix.objects.all()
    serializer_class = MatrixSerializer


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
            box__exact=max_box['box__max'], row__exact=max_row['row__max'], spot__exact=max_spot['spot__max']).first()
        return last_occupied.id if last_occupied is not None else 0

    def get_queryset(self):
        queryset = FreezerLocation.objects.all()
        last_occupied = self.request.query_params.get('last_occupied', None)
        if last_occupied is not None:
            if last_occupied == 'True' or last_occupied == 'true':
                if self.get_last_occupied_id() != 0:
                    queryset = queryset.filter(id__exact=self.get_last_occupied_id())
        return queryset


class FreezerViewSet(HistoryViewSet):
    queryset = Freezer.objects.all()
    serializer_class = FreezerSerializer


######
#
#  Final Sample Values
#
######


class FinalConcentratedSampleVolumeViewSet(HistoryViewSet):
    queryset = FinalConcentratedSampleVolume.objects.all()
    serializer_class = FinalConcentratedSampleVolumeSerializer

    def get_serializer(self, *args, **kwargs):
        if 'data' in kwargs:
            data = kwargs['data']

            # check if many is required
            if isinstance(data, list):
                kwargs['many'] = True

        return super(FinalConcentratedSampleVolumeViewSet, self).get_serializer(*args, **kwargs)


class ConcentrationTypeViewSet(HistoryViewSet):
    queryset = ConcentrationType.objects.all()
    serializer_class = ConcentrationTypeSerializer


class FinalSampleMeanConcentrationViewSet(HistoryViewSet):
    serializer_class = FinalSampleMeanConcentrationSerializer

    # override the default queryset to allow filtering by URL arguments
    def get_queryset(self):
        queryset = FinalSampleMeanConcentration.objects.all()
        # filter by sample ID, exact list
        sample = self.request.query_params.get('sample', None)
        if sample is not None:
            sample_list = sample.split(',')
            queryset = queryset.filter(sample__in=sample_list)
        # filter by target ID, exact list
        target = self.request.query_params.get('target', None)
        if sample is not None:
            target_list = sample.split(',')
            queryset = queryset.filter(target__in=target_list)
        # filter by study ID, exact list
        study = self.request.query_params.get('study', None)
        if study is not None:
            study_list = sample.split(',')
            queryset = queryset.filter(sample__study__in=study_list)
        # filter by collection_start_date, exact list
        collection_start_date = self.request.query_params.get('collection_start_date', None)
        if collection_start_date is not None:
            collection_start_date_list = sample.split(',')
            queryset = queryset.filter(sample__collection_start_date__in=collection_start_date_list)
        # filter by collaborator_sample_id, exact list
        collaborator_sample_id = self.request.query_params.get('collaborator_sample_id', None)
        if collaborator_sample_id is not None:
            collaborator_sample_id_list = sample.split(',')
            queryset = queryset.filter(sample__collaborator_sample_id__in=collaborator_sample_id_list)
        return queryset


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

    # override the default serializer_class if summary fields are requested
    def get_serializer_class(self):
        include_summary_fields = self.request.query_params.get('includeSummaryFields', None)
        if include_summary_fields is not None and include_summary_fields.lower() == 'true':
            return ExtractionBatchSummarySerializer
        else:
            return ExtractionBatchSerializer


class ReverseTranscriptionViewSet(HistoryViewSet):
    queryset = ReverseTranscription.objects.all()
    serializer_class = ReverseTranscriptionSerializer


class SampleExtractionViewSet(HistoryViewSet):
    queryset = SampleExtraction.objects.all()
    serializer_class = SampleExtractionSerializer


class PCRReplicateViewSet(HistoryViewSet):
    queryset = PCRReplicate.objects.all()
    serializer_class = PCRReplicateSerializer

    def get_serializer(self, *args, **kwargs):
        if 'data' in kwargs:
            data = kwargs['data']

            # check if many is required
            if isinstance(data, list):
                kwargs['many'] = True

        return super(PCRReplicateViewSet, self).get_serializer(*args, **kwargs)

    # override the default PATCH method to allow bulk processing
    def patch(self, request, pk=None):
        request_data = JSONParser().parse(request)
        # if there is no pk, assume this is a bulk request
        if not pk:
            is_valid = True
            response_data = []
            valid_data = []
            response_errors = []
            for item in request_data:
                # ensure the id field is present, otherwise nothing can be updated
                if not item.get('id'):
                    is_valid = False
                    response_errors.append({"id": "This field is required."})
                else:
                    rep_id = item.pop('id')
                    rep = PCRReplicate.objects.filter(id=rep_id).first()
                    if rep:
                        serializer = self.serializer_class(rep, data=item, partial=True)
                        # if this item is valid, temporarily hold it until all items are proven valid, then save all
                        # if even one item is invalid, none will be saved, and the user will be returned the error(s)
                        if serializer.is_valid():
                            valid_data.append(serializer)
                        else:
                            is_valid = False
                            response_errors.append(serializer.errors)
                    else:
                        is_valid = False
                        response_errors.append({"pcrreplicate": "No PCRReplicate exists with this ID: " + rep_id})
            if is_valid:
                # now that all items are proven valid, save and return them to the user
                for item in valid_data:
                    item.save()
                    response_data.append(item.data)
                return JsonResponse(response_data, safe=False, status=200)
            else:
                return JsonResponse(response_errors, safe=False, status=400)
        # otherwise, if there is a pk, update the instance indicated by the pk
        else:
            rep = PCRReplicate.objects.filter(id=pk).first()
            if rep:
                serializer = self.serializer_class(rep, data=request_data, partial=True)
                if serializer.is_valid():
                    serializer.save()
                    return Response(serializer.data, status=200)
                else:
                    return Response(serializer.errors, status=400)
            else:
                return JsonResponse({"pcrreplicate": "No PCRReplicate exists with this ID: " + pk}, status=400)


class PCRReplicateBatchViewSet(HistoryViewSet):
    serializer_class = PCRReplicateBatchSerializer

    # override the default queryset to allow filtering by URL arguments
    def get_queryset(self):
        queryset = PCRReplicateBatch.objects.all()
        # if ID is in query, only search by ID and ignore other params
        batch = self.request.query_params.get('id', None)
        if batch is not None:
            queryset = queryset.filter(id__exact=batch)
        # else, search by other params (that don't include ID)
        else:
            analysis_batch = self.request.query_params.get('analysis_batch', None)
            extraction_number = self.request.query_params.get('extraction_number', None)
            if analysis_batch is not None and extraction_number is not None:
                queryset = queryset.filter(extraction_batch__analysis_batch__exact=analysis_batch,
                                           extraction_batch__extraction_number__exact=extraction_number)
            target = self.request.query_params.get('target', None)
            if target is not None:
                queryset = queryset.filter(target__exact=target)
            replicate_number = self.request.query_params.get('replicate_number', None)
            if replicate_number is not None:
                queryset = queryset.filter(replicate_number__exact=replicate_number)
        return queryset


class StandardCurveViewSet(HistoryViewSet):
    queryset = StandardCurve.objects.all()
    serializer_class = StandardCurveSerializer


class InhibitionViewSet(HistoryViewSet):
    queryset = Inhibition.objects.all()
    serializer_class = InhibitionSerializer

    def get_serializer(self, *args, **kwargs):
        if 'data' in kwargs:
            data = kwargs['data']

            # check if many is required
            if isinstance(data, list):
                kwargs['many'] = True

        return super(InhibitionViewSet, self).get_serializer(*args, **kwargs)

    # override the default PATCH method to allow bulk processing
    def patch(self, request, pk=None):
        request_data = JSONParser().parse(request)
        # if there is no pk, assume this is a bulk request
        if not pk:
            is_valid = True
            response_data = []
            valid_data = []
            response_errors = []
            for item in request_data:
                # ensure the id field is present, otherwise nothing can be updated
                if not item.get('id'):
                    is_valid = False
                    response_errors.append({"id": "This field is required."})
                else:
                    inhib = item.pop('id')
                    inhibition = Inhibition.objects.filter(id=inhib).first()
                    if inhibition:
                        serializer = self.serializer_class(inhibition, data=item, partial=True)
                        # if this item is valid, temporarily hold it until all items are proven valid, then save all
                        # if even one item is invalid, none will be saved, and the user will be returned the error(s)
                        if serializer.is_valid():
                            valid_data.append(serializer)
                        else:
                            is_valid = False
                            response_errors.append(serializer.errors)
                    else:
                        is_valid = False
                        response_errors.append({"inhibition": "No Inhibition exists with this ID: " + inhib})
            if is_valid:
                # now that all items are proven valid, save and return them to the user
                for item in valid_data:
                    item.save()
                    response_data.append(item.data)
                return JsonResponse(response_data, safe=False, status=200)
            else:
                return JsonResponse(response_errors, safe=False, status=400)
        # otherwise, if there is a pk, update the instance indicated by the pk
        else:
            inhibition = Inhibition.objects.filter(id=pk).first()
            if inhibition:
                serializer = self.serializer_class(inhibition, data=request_data, partial=True)
                if serializer.is_valid():
                    serializer.save()
                    return Response(serializer.data, status=200)
                else:
                    return Response(serializer.errors, status=400)
            else:
                return JsonResponse({"inhibition": "No Inhibition exists with this ID: " + pk}, status=400)


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


class InhibitionCalculateDilutionFactorView(views.APIView):
    permission_classes = (permissions.IsAuthenticated,)

    def post(self, request):
        request_data = JSONParser().parse(request)
        ab = request_data.get('analysis_batch', None)
        en = request_data.get('extraction_number', None)
        na = request_data.get('nucleic_acid_type', None)
        eb = ExtractionBatch.objects.filter(analysis_batch=ab, extraction_number=en).first()
        if eb:
            serializer = InhibitionCalculateDilutionFactorSerializer(data=request_data)
            if serializer.is_valid():
                is_valid = True
                response_data = []
                response_errors = []
                pos = request_data.get('inh_pos_cq_value', None)
                inhibitions = request_data.get('inhibitions', None)
                for inhibition in inhibitions:
                    cq = inhibition.get('cq_value', None)
                    sample = inhibition.get('sample', None)
                    inhib = Inhibition.objects.filter(sample=sample, extraction_batch=eb, nucleic_acid_type=na).first()
                    if inhib:
                        suggested_dilution_factor = None
                        if 0 < pos - cq < 1:
                            suggested_dilution_factor = 1
                        if cq > pos and cq - pos < 2:
                            suggested_dilution_factor = 1
                        if cq - pos >= 2 and cq <= 36:
                            suggested_dilution_factor = 5
                        if cq > 36 or cq is None:
                            suggested_dilution_factor = 10
                        new_data = {"id": inhib.id, "sample": sample,
                                    "suggested_dilution_factor": suggested_dilution_factor}
                        response_data.append(new_data)
                    else:
                        is_valid = False
                        message = "No Inhibition exists with Sample ID: " + sample
                        message += ", Extraction Batch ID: " + eb + ", Nucleic Acid Type ID: " + na
                        response_errors.append({"inhibition": message})
                if is_valid:
                    return JsonResponse(response_data, safe=False, status=200)
                else:
                    return JsonResponse(response_errors, safe=False, status=400)
            return Response(serializer.errors, status=400)
        else:
            message = "No Extraction Batch exists with Analysis Batch ID: " + ab + " and Extraction Number: " + en
            return JsonResponse({"extraction_batch": message}, status=400)


class TargetViewSet(HistoryViewSet):
    queryset = Target.objects.all()
    serializer_class = TargetSerializer


######
#
#  Misc
#
######


class FieldUnitViewSet(HistoryViewSet):
    queryset = FieldUnit.objects.all()
    serializer_class = FieldUnitSerializer


class NucleicAcidTypeViewSet(HistoryViewSet):
    queryset = NucleicAcidType.objects.all()
    serializer_class = NucleicAcidTypeSerializer


class RecordTypeViewSet(HistoryViewSet):
    queryset = RecordType.objects.all()
    serializer_class = RecordTypeSerializer


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
