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
        if 'data' in kwargs:
            data = kwargs['data']

            # check if many is required
            if isinstance(data, list) and 'aliquot_count' in data[0]:
                kwargs['many'] = True

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
        if 'data' in kwargs:
            data = kwargs['data']

            # check if many is required
            if isinstance(data, list):
                kwargs['many'] = True

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


class ExtractionViewSet(HistoryViewSet):
    queryset = Extraction.objects.all()
    serializer_class = ExtractionSerializer


class PCRReplicateViewSet(HistoryViewSet):
    queryset = PCRReplicate.objects.all()
    serializer_class = PCRReplicateSerializer


class PCRReplicateControlViewSet(HistoryViewSet):
    queryset = PCRReplicateControl.objects.all()
    serializer_class = PCRReplicateControlSerializer


class PCRReplicateResultsUploadView(views.APIView):
    permission_classes = (permissions.IsAuthenticated,)

    def post(self, request):
        request_data = JSONParser().parse(request)
        serializer = PCRReplicateResultsUploadSerializer(data=request_data)
        if serializer.is_valid():
            is_valid = True
            response_data = []
            valid_data = []
            response_errors = []
            target = request_data.get('target', None)
            ab = request_data.get('analysis_batch', None)
            en = request_data.get('extraction_number', None)
            rn = request_data.get('replicate_number', None)
            sc = request_data.get('standard_curve', None)
            extneg_cq = request_data.get('ext_neg_cq_value', None)
            extneg_conc = request_data.get('ext_neg_concentration', None)
            rtneg_cq = request_data.get('rt_neg_cq_value', None)
            rtneg_conc = request_data.get('rt_neg_concentration', None)
            pcrneg_cq = request_data.get('pcr_neg_cq_value', None)
            pcrneg_conc = request_data.get('pcr_neg_concentration', None)
            pcrpos_cq = request_data.get('pcr_pos_cq_value', None)
            pcrpos_conc = request_data.get('pcr_pos_concentration', None)
            pcrreplicates = request_data.get('pcrreplicates', None)
            eb = ExtractionBatch.objects.filter(analysis_batch=ab, extraction_number=en).first()
            if eb:
                # TODO: also save control data (extneg, rtneg, pcrneg, pcrpos)
                for control in ['ext_neg', 'rt_neg', 'pcr_neg', 'pcr_pos']:
                    control_type = ControlType.objects.get(name=control)
                    pcrrepcontrol = PCRReplicateControl.objects.filter(extraction_batch=eb.id, target=target,
                                                       replicate_number=rn, control_type=control_type.id).first()
                    if pcrrepcontrol:
                        data = {}
                        flag = False
                        if (control + '_cq_value') in request_data or (control + '_gc_reaction') in request_data:
                            if request_data[control + '_cq_value'] > 0 or request_data[control + '_gc_reaction'] > 0:
                                flag = True
                        if control == 'ext_neg':
                            data = {'cq_value': extneg_cq, 'gc_reaction': extneg_conc, 'bad_result_flag': flag}
                        elif control == 'rt_neg':
                            data = {'cq_value': rtneg_cq, 'gc_reaction': rtneg_conc, 'bad_result_flag': flag}
                        elif control == 'pcr_neg':
                            data = {'cq_value': pcrneg_cq, 'gc_reaction': pcrneg_conc, 'bad_result_flag': flag}
                        elif control == 'pcr_pos':
                            data = {'cq_value': pcrpos_cq, 'gc_reaction': pcrpos_conc, 'bad_result_flag': flag}
                        serializer = PCRReplicateControlSerializer(pcrrepcontrol, data=data, partial=True)
                        if serializer.is_valid():
                            valid_data.append(serializer)
                        else:
                            is_valid = False
                            response_errors.append(serializer.errors)
                    else:
                        is_valid = False
                        message = "No PCRReplicate Control exists with Extraction Batch ID: " + eb.id + ", "
                        message += "Target ID: " + target + ", Replicate Number: " + rn + ", "
                        message += "Control Type: " + control_type
                        response_errors.append({"pcrreplicate": message})
                for pcrreplicate in pcrreplicates:
                    sample = pcrreplicate.get('sample', None)
                    extraction = Extraction.objects.filter(extraction_batch=eb.id, sample=sample).first()
                    if extraction:
                        cq_value = pcrreplicate.get('cq_value', 0)
                        gc_reaction = pcrreplicate.get('gene_copies_per_reaction', 0)
                        pcrrep = PCRReplicate.objects.filter(extraction=extraction.id, target=target,
                                                             replicate_number=rn).first()
                        if pcrrep:
                            bad_result_flag = False
                            if cq_value > 0:
                                if rtneg_cq is not None:
                                    if extneg_conc > 0 or rtneg_conc > 0 or pcrneg_conc > 0 or gc_reaction < 0:
                                        bad_result_flag = True
                                else:
                                    if extneg_conc > 0 or pcrneg_conc > 0 or gc_reaction < 0:
                                        bad_result_flag = True
                            target = Target.objects.get(id=target)
                            nucleic_acid_type = target.nucleic_acid_type
                            replicate_concentration = self.calculate_replicate_concentration(gc_reaction, nucleic_acid_type, extraction, eb, sample)
                            new_data = {'cq_value': cq_value, 'gc_reaction': gc_reaction,
                                        'bad_result_flag': bad_result_flag}
                            serializer = PCRReplicateSerializer(pcrrep, data=new_data, partial=True)
                            if serializer.is_valid():
                                valid_data.append(serializer)
                            else:
                                is_valid = False
                                response_errors.append(serializer.errors)
                        else:
                            is_valid = False
                            message = "No PCRReplicate exists with Extraction ID: " + extraction.id + ", "
                            message += "Target ID: " + target + ", Replicate Number: " + rn
                            response_errors.append({"pcrreplicate": message})
                    else:
                        is_valid = False
                        message = "No Extraction exists with Extraction Batch ID: " + eb.id + ", "
                        message += "Sample ID: " + sample
                        response_errors.append({"extraction": message})
            else:
                is_valid = False
                message = "No Extraction Batch exists with Analysis Batch ID: " + ab + ", "
                message += "Extraction Number: " + en
                response_errors.append({"extraction_batch": message})
            if is_valid:
                # now that all items are proven valid, save and return them to the user
                for item in valid_data:
                    item.save()
                    response_data.append(item.data)
                return JsonResponse(response_data, safe=False, status=200)
            else:
                return JsonResponse(response_errors, safe=False, status=400)
        return Response(serializer.errors, status=400)

    def calculate_replicate_concentration(self, gc_reaction, nucleic_acid_type, extraction, eb, sample):
        fcsv = FinalConcentratedSampleVolume.objects.get(sample=sample.id)
        if sample.matrix == 'water':
            if nucleic_acid_type == 'DNA':
                return (gc_reaction / eb.reaction_volume) * (eb.reaction_volume / eb.template_volume) * (
                        eb.elution_volume / eb.extraction_volume) * (1000 microL / 1 mL) * (
                        fcsv / sample.sample_volume) * eb.dilution_factor * extraction.inhibition.dilution_factor


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
                    response_errors.append({"id":"This field is required."})
                else:
                    inhib = item.pop('id')
                    inhibition = Inhibition.objects.filter(id=inhib).first()
                    if inhibition:
                        serializer = self.serializer_class(inhibition, data=item, partial=True)
                        # if this item is valid, temporarily hold it until all items are proven valid, then save them all
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
                        new_data = {"id": inhib.id, "sample": sample, "suggested_dilution_factor": suggested_dilution_factor}
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
