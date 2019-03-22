from django.http import JsonResponse
from rest_framework import views, viewsets, generics, permissions, authentication, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.parsers import JSONParser
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


LIST_DELIMETER = ','


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

    @action(detail=False)
    def get_count(self, request):
        # Sample.objects.filter(matrix__in=matrix_list).count()
        query_params = self.request.query_params
        return Response({"count": self.build_queryset(query_params).count()})

    @action(detail=False)
    def get_sampler_names(self, request):
        sampler_names = set(list(Sample.objects.values_list('sampler_name', flat=True)))
        return Response({"sampler_names": sampler_names})

    @action(detail=False)
    def get_recent_pegnegs(self, request):
        pegneg_record_type = RecordType.objects.filter(id=2).first()
        recent_pegnegs = Sample.objects.filter(record_type=pegneg_record_type).order_by('-id')[:20]
        return Response(self.serializer_class(recent_pegnegs, many=True).data)

    # override the default queryset to allow filtering by URL arguments
    def get_queryset(self):
        query_params = self.request.query_params
        return self.build_queryset(query_params)

    # build a queryset using query_params
    # NOTE: this is being done in its own method to adhere to the DRY Principle
    def build_queryset(self, query_params):
        queryset = Sample.objects.all()
        # filter by sample IDs, exact list
        sample = query_params.get('id', None)
        if sample is not None:
            if LIST_DELIMETER in sample:
                sample_list = sample.split(LIST_DELIMETER)
                queryset = queryset.filter(id__in=sample_list)
            else:
                queryset = queryset.filter(id__exact=sample)
        # filter by sample ID, range
        from_sample = query_params.get('from_id', None)
        to_sample = query_params.get('to_id', None)
        if from_sample is not None and to_sample is not None:
            # the filter below using __range is value-inclusive
            queryset = queryset.filter(id__range=(from_sample, to_sample))
        elif to_sample is not None:
            queryset = queryset.filter(id__lte=to_sample)
        elif from_sample is not None:
            queryset = queryset.filter(id__gte=from_sample)
        # filter by study ID, exact list
        study = query_params.get('study', None)
        if study is not None:
            if LIST_DELIMETER in study:
                study_list = study.split(LIST_DELIMETER)
                queryset = queryset.filter(study__in=study_list)
            else:
                queryset = queryset.filter(study__exact=study)
        # filter by collection_start_date, range
        from_collection_start_date = query_params.get('from_collection_start_date', None)
        to_collection_start_date = query_params.get('to_collection_start_date', None)
        if from_collection_start_date is not None and to_collection_start_date is not None:
            # the filter below using __range is value-inclusive
            queryset = queryset.filter(collection_start_date__range=(
                from_collection_start_date, to_collection_start_date))
        elif to_collection_start_date is not None:
            queryset = queryset.filter(collection_start_date__lte=to_collection_start_date)
        elif from_collection_start_date is not None:
            queryset = queryset.filter(collection_start_date__gte=from_collection_start_date)
        # filter by collaborator_sample_id, exact list
        collaborator_sample_id = query_params.get('collaborator_sample_id', None)
        if collaborator_sample_id is not None:
            if LIST_DELIMETER in collaborator_sample_id:
                collaborator_sample_id_list = collaborator_sample_id.split(LIST_DELIMETER)
                queryset = queryset.filter(collaborator_sample_id__in=collaborator_sample_id_list)
            else:
                queryset = queryset.filter(collaborator_sample_id__exact=collaborator_sample_id)
        # filter by sample type, exact list
        sample_type = query_params.get('sample_type', None)
        if sample_type is not None:
            if LIST_DELIMETER in sample_type:
                sample_type_list = sample_type.split(LIST_DELIMETER)
                queryset = queryset.filter(sample_type__in=sample_type_list)
            else:
                queryset = queryset.filter(sample_type__exact=sample_type)
        # filter by matrix, exact list
        matrix = query_params.get('matrix', None)
        if matrix is not None:
            if LIST_DELIMETER in matrix:
                matrix_list = matrix.split(LIST_DELIMETER)
                queryset = queryset.filter(matrix__in=matrix_list)
            else:
                queryset = queryset.filter(matrix__exact=matrix)
        # filter by record_type, exact list
        record_type = query_params.get('record_type', None)
        if record_type is not None:
            if LIST_DELIMETER in record_type:
                record_type_list = record_type.split(LIST_DELIMETER)
                queryset = queryset.filter(record_type__in=record_type_list)
            else:
                queryset = queryset.filter(record_type__exact=record_type)
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
    queryset = FreezerLocation.objects.all()
    serializer_class = FreezerLocationSerializer

    @action(methods=['get'], detail=False)
    def get_next_available(self, request):
        # get the next empty box in the any freezer
        next_empty_box = FreezerLocation.objects.get_next_empty_box()
        if next_empty_box is None:
            next_empty_box = "There are no more empty boxes in this freezer!"
        # get the study_id from the request query
        study_id = request.query_params.get('study', None)
        last_spot = FreezerLocation.objects.get_last_occupied_spot(study_id)
        # if a last spot is found look up the next available spot
        if last_spot is not None:
            next_spot = FreezerLocation.objects.get_next_available_spot(last_spot)
            # if there is a next spot
            if next_spot is not None:
                # start building the full response object
                resp = next_spot
                # if the next spot is not simply the next empty box
                if next_spot != next_empty_box:
                    # then add the next empty box to the response object
                    resp.update({"next_empty_box": next_empty_box})
                # otherwise the next spot is in fact just the next empty box,
                # so attempt to find the next empty box after this one
                else:
                    # start building the next empty box object
                    next_empty_box = {"freezer": last_spot.freezer.id}
                    # check if adding another box will exceed the number of boxes allowed per rack in this freezer
                    if next_spot['box'] + 1 > last_spot.freezer.boxes:
                        # check if there is still room for another rack in this freezer,
                        # and if so just increment the rack number
                        if next_spot['rack'] + 1 <= last_spot.freezer.racks:
                            next_empty_box['rack'] = next_spot['rack'] + 1
                            next_empty_box['box'] = 1
                            next_empty_box['row'] = 1
                            next_empty_box['spot'] = 1
                            next_empty_box['available_spots_in_box'] = last_spot.freezer.rows * last_spot.freezer.spots
                        # otherwise adding another rack will exceed the number of racks allowed in this freezer,
                        # so check if there is another freezer,
                        else:
                            next_freezer = Freezer.objects.filter(id=(last_spot.freezer.id + 1)).first()
                            # if there is another freezer, return the first location in that entire freezer
                            if next_freezer is not None:
                                next_empty_box['freezer'] = next_freezer.id
                                next_empty_box['rack'] = 1
                                next_empty_box['box'] = 1
                                next_empty_box['row'] = 1
                                next_empty_box['spot'] = 1
                                next_empty_box['available_spots_in_box'] = next_freezer.rows * next_freezer.spots
                            # otherwise adding another rack will exceed the number of racks allowed in any freezer
                            else:
                                next_empty_box = "There are no more empty boxes after this box in any freezer!"
                    # there is still room for another box in this rack, so just increment the box number
                    else:
                        next_empty_box['rack'] = next_spot['rack']
                        next_empty_box['box'] = next_spot['box'] + 1
                        next_empty_box['row'] = 1
                        next_empty_box['spot'] = 1
                        next_empty_box['available_spots_in_box'] = last_spot.freezer.rows * last_spot.freezer.spots
                    resp.update({"next_empty_box": next_empty_box})
            # no next spot was found
            else:
                resp = {"not_found": "There are no more empty boxes in this freezer!"}
        # otherwise no last spot has been found
        else:
            # if a study_id was included in the query, mention it in the response
            if study_id is not None:
                study = Study.objects.filter(id=study_id).first()
                message = "No aliquots for "
                if study is not None:
                    message += study.name + " "
                message += "(Study ID #" + str(study_id) + ") are stored in any freezer."
            # otherwise inform the user that no freezer locations have been used
            else:
                message = "No aliquots are stored in any freezer."
            resp = {"not_found": message}
            resp.update({"next_empty_box": next_empty_box})
        return Response(resp)

        # study_id = request.query_params.get('study', None)
        # last_spot = FreezerLocation.objects.get_last_occupied_spot(study_id)
        # # a last spot has been found
        # if last_spot is not None:
        #     avail_spots = FreezerLocation.objects.get_available_spots_in_box(last_spot)
        #     spots_in_row = last_spot.freezer.spots
        #     if avail_spots > 0:
        #         next_spot = {"freezer": last_spot.freezer.id}
        #         next_spot['rack'] = last_spot.rack
        #         next_spot['box'] = last_spot.box
        #         next_spot['row'] = last_spot.row if last_spot.spot < spots_in_row else last_spot.row + 1
        #         next_spot['spot'] = last_spot.spot + 1 if last_spot.spot < spots_in_row else 1
        #         resp = next_spot
        #         resp.update({"available_spots_in_box": avail_spots})
        #         next_empty_box = FreezerLocation.objects.get_next_empty_box()
        #         if next_empty_box is None:
        #             next_empty_box = "There are no more empty boxes in this freezer!"
        #         resp.update({"next_empty_box": next_empty_box})
        #     else:
        #         next_spot = FreezerLocation.objects.get_next_empty_box()
        #         if next_spot is None:
        #             next_spot = {"not_found": "There are no more empty boxes in this freezer!"}
        #         resp = next_spot
        #         resp.update({"available_spots_in_box": last_spot.freezer.rows * spots_in_row})
        # # no spot has been found
        # else:
        #     if study_id is not None:
        #         study = Study.objects.filter(id=study_id).first()
        #         message = "No aliquots for "
        #         if study is not None:
        #             message += study.name + " "
        #         message += "(Study ID #" + str(study_id) + ") are stored in any freezer."
        #         resp = {"not_found": message}
        #         resp.update({"next_empty_box": FreezerLocation.objects.get_next_empty_box()})
        #     else:
        #         message = "No aliquots are stored in any freezer."
        #         resp = {"not_found": message}
        #         resp.update({"next_empty_box": FreezerLocation.objects.get_next_empty_box()})
        # return Response(resp)


class FreezerViewSet(HistoryViewSet):
    queryset = Freezer.objects.all()
    serializer_class = FreezerSerializer


######
#
#  Final Sample Values
#
######


class FinalConcentratedSampleVolumeViewSet(HistoryViewSet):
    serializer_class = FinalConcentratedSampleVolumeSerializer

    # override the default queryset to allow filtering by URL arguments
    def get_queryset(self):
        queryset = FinalConcentratedSampleVolume.objects.all()
        # filter by sample ID, exact list
        sample = self.request.query_params.get('sample', None)
        if sample is not None:
            sample_list = sample.split(',')
            queryset = queryset.filter(sample__in=sample_list)
        return queryset

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
        if target is not None:
            target_list = target.split(',')
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
            if LIST_DELIMETER in batch:
                batch_list = batch.split(',')
                queryset = queryset.filter(id__in=batch_list)
            else:
                queryset = queryset.filter(id__exact=batch)
        return queryset


class AnalysisBatchSummaryViewSet(HistoryViewSet):
    serializer_class = AnalysisBatchSummarySerializer

    @action(detail=False)
    def get_count(self, request):
        query_params = self.request.query_params
        return Response({"count": self.build_queryset(query_params).count()})

    # override the default queryset to allow filtering by URL arguments
    def get_queryset(self):
        query_params = self.request.query_params
        return self.build_queryset(query_params)

    # build a queryset using query_params
    # NOTE: this is being done in its own method to adhere to the DRY Principle
    def build_queryset(self, query_params):
        study = self.request.query_params.get('study', None)
        if study is not None:
            queryset = AnalysisBatch.objects.prefetch_related('samples').all()
        else:
            queryset = AnalysisBatch.objects.all()
        # filter by batch ID, exact list
        batch = self.request.query_params.get('id', None)
        if batch is not None:
            if LIST_DELIMETER in batch:
                batch_list = batch.split(',')
                queryset = queryset.filter(id__in=batch_list)
            else:
                queryset = queryset.filter(id__exact=batch)
        # filter by batch ID, range
        from_batch = query_params.get('from_id', None)
        to_batch = query_params.get('to_id', None)
        if from_batch is not None and to_batch is not None:
            # the filter below using __range is value-inclusive
            queryset = queryset.filter(id__range=(from_batch, to_batch))
        elif to_batch is not None:
            queryset = queryset.filter(id__lte=to_batch)
        elif from_batch is not None:
            queryset = queryset.filter(id__gte=from_batch)
        # filter by study ID, exact list
        if study is not None:
            if LIST_DELIMETER in study:
                study_list = study.split(',')
                queryset = queryset.filter(samples__study__in=study_list).distinct()
            else:
                queryset = queryset.filter(samples__study__exact=study).distinct()
        return queryset


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
    # serializer_class = ExtractionBatchSerializer

    # override the default serializer_class if summary fields are requested
    def get_serializer_class(self):
        include_summary_fields = self.request.query_params.get('includeSummaryFields', None)
        if include_summary_fields is not None and include_summary_fields.lower() == 'true':
            return ExtractionBatchSummarySerializer
        else:
            return ExtractionBatchSerializer

    def get_serializer(self, *args, **kwargs):
        if 'data' in kwargs:
            data = kwargs['data']

            # check if many is required
            if isinstance(data, list):
                kwargs['many'] = True

        return super(ExtractionBatchViewSet, self).get_serializer(*args, **kwargs)

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
                    eb_id = item.pop('id')
                    eb = ExtractionBatch.objects.filter(id=eb_id).first()
                    item['modified_by'] = request.user
                    if eb:
                        serializer = self.get_serializer(eb, data=item, partial=True)
                        # if this item is valid, temporarily hold it until all items are proven valid, then save all
                        # if even one item is invalid, none will be saved, and the user will be returned the error(s)
                        if serializer.is_valid():
                            valid_data.append(serializer)
                        else:
                            is_valid = False
                            response_errors.append(serializer.errors)
                    else:
                        is_valid = False
                        message = "No ExtractionBatch exists with this ID: " + str(eb_id)
                        response_errors.append({"extractionbatch": message})
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
            rep = ExtractionBatch.objects.filter(id=pk).first()
            if rep:
                serializer = self.serializer_class(rep, data=request_data, partial=True)
                if serializer.is_valid():
                    serializer.save()
                    return Response(serializer.data, status=200)
                else:
                    return Response(serializer.errors, status=400)
            else:
                message = "No ExtractionBatch exists with this ID: " + str(pk)
                return JsonResponse({"extractionbatch": message}, status=400)


class ReverseTranscriptionViewSet(HistoryViewSet):
    queryset = ReverseTranscription.objects.all()
    serializer_class = ReverseTranscriptionSerializer

    def get_serializer(self, *args, **kwargs):
        if 'data' in kwargs:
            data = kwargs['data']

            # check if many is required
            if isinstance(data, list):
                kwargs['many'] = True

        return super(ReverseTranscriptionViewSet, self).get_serializer(*args, **kwargs)

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
                    rt_id = item.pop('id')
                    rt = ReverseTranscription.objects.filter(id=rt_id).first()
                    if rt:
                        serializer = self.serializer_class(rt, data=item, partial=True)
                        # if this item is valid, temporarily hold it until all items are proven valid, then save all
                        # if even one item is invalid, none will be saved, and the user will be returned the error(s)
                        if serializer.is_valid():
                            valid_data.append(serializer)
                        else:
                            is_valid = False
                            response_errors.append(serializer.errors)
                    else:
                        is_valid = False
                        response_errors.append(
                            {"reversetranscription": "No ReverseTranscription exists with this ID: " + str(rt_id)})
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
            rep = ReverseTranscription.objects.filter(id=pk).first()
            if rep:
                serializer = self.serializer_class(rep, data=request_data, partial=True)
                if serializer.is_valid():
                    serializer.save()
                    return Response(serializer.data, status=200)
                else:
                    return Response(serializer.errors, status=400)
            else:
                return JsonResponse(
                    {"reversetranscription": "No ReverseTranscription exists with this ID: " + str(pk)}, status=400)


class SampleExtractionViewSet(HistoryViewSet):
    queryset = SampleExtraction.objects.all()
    serializer_class = SampleExtractionSerializer


class PCRReplicateViewSet(HistoryViewSet):
    serializer_class = PCRReplicateSerializer

    def get_serializer(self, *args, **kwargs):
        if 'data' in kwargs:
            data = kwargs['data']

            # check if many is required
            if isinstance(data, list):
                kwargs['many'] = True

        return super(PCRReplicateViewSet, self).get_serializer(*args, **kwargs)

    def get_queryset(self):
        queryset = PCRReplicate.objects.all()
        id = self.request.query_params.get('id', None)
        if id is not None:
            if LIST_DELIMETER in id:
                id_list = id.split(',')
                queryset = queryset.filter(id__in=id_list)
            else:
                queryset = queryset.filter(id__exact=id)
        return queryset

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
                        new_invalid = item.get('invalid', None)
                        if new_invalid is not None and new_invalid != rep.invalid:
                            item['invalid_override'] = request.user.id
                        rep.replicate_concentration = rep.calc_rep_conc()
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
                        response_errors.append({"pcrreplicate": "No PCRReplicate exists with this ID: " + str(rep_id)})
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
                new_invalid = request_data.get('invalid', None)
                if new_invalid is not None and new_invalid != rep.invalid:
                    if request_data.get('invalid_override', None) is None:
                        request_data['invalid_override'] = request.user.id
                serializer = self.serializer_class(rep, data=request_data, partial=True)
                if serializer.is_valid():
                    serializer.save()
                    return Response(serializer.data, status=200)
                else:
                    return Response(serializer.errors, status=400)
            else:
                return JsonResponse({"pcrreplicate": "No PCRReplicate exists with this ID: " + str(pk)}, status=400)


class PCRReplicateBatchViewSet(HistoryViewSet):
    serializer_class = PCRReplicateBatchSerializer

    def isnumber(self, val):
        try:
            return True if float(val) == 0 else float(val)
        except ValueError:
            return False

    def err_obj(self, field, message, severity):
        return {"field": field, "message": message, "severity": severity}

    def validate_controls(self, field):
        synonym = " ('cp')" if 'cq_value' in field else " ('concentration')" if 'gc_reaction' in field else ''
        invalid_reason = None
        if field not in self.request.data:
            invalid_reason = self.err_obj(field, field + synonym + " is missing", 2)
        elif self.request.data[field] is not None:
            if not self.isnumber(self.request.data[field]):
                invalid_reason = self.err_obj(field, field + synonym + " is not a number", 1)
            elif self.request.data[field] > 0 and field not in ['pcr_pos_cq_value', 'pcr_pos_gc_reaction']:
                # TODO: eventually we will also validate pcr_pos_cq_value by testing if it is >0.5 cylces from expected
                invalid_reason = self.err_obj(field, field + synonym + " is positive", 1)
        return invalid_reason

    @action(methods=['post'], detail=False)
    def bulk_load_negatives(self, request):

        is_valid = True
        valid_data = []
        response_errors = []
        for item in request.data:
            item_validation_errors = []
            if 'extraction_batch' not in item:
                item_validation_errors.append("extraction_batch is required")
            if 'target' not in item:
                item_validation_errors.append("target is required")
            if 'replicate_number' not in item:
                item_validation_errors.append("replicate_number is required")
            if 'pcr_pos_cq_value' not in item:
                item_validation_errors.append("pcr_pos_cq_value is required")
            if len(item_validation_errors) > 0:
                is_valid = False
                response_errors.append(item_validation_errors)
                continue

            pcrreplicate_batch = PCRReplicateBatch.objects.filter(
                extraction_batch=item['extraction_batch'], target=item['target'],
                replicate_number=item['replicate_number']).first()

            if pcrreplicate_batch:
                item.pop('extraction_batch')
                item.pop('target')
                item.pop('replicate_number')
                item['ext_neg_cq_value'] = 0
                item['ext_neg_gc_reaction'] = 0
                item['rt_neg_cq_value'] = 0
                item['rt_neg_gc_reaction'] = 0
                item['pcr_neg_cq_value'] = 0
                item['pcr_neg_gc_reaction'] = 0
                item['pcr_pos_gc_reaction'] = 0
                serializer = PCRReplicateBatchBaseSerializer(pcrreplicate_batch, data=item, partial=True)
                # if this item is valid, temporarily hold it until all items are proven valid, then save all
                # if even one item is invalid, none will be saved, and the user will be returned the error(s)
                if serializer.is_valid():
                    valid_data.append(serializer)
                else:
                    is_valid = False
                    response_errors.append(serializer.errors)
            else:
                message = "No PCR replicate batch was found with extraction batch of " + str(item['extraction_batch'])
                message += " and target of " + str(item['target'])
                message += " and replicate number of " + str(item['replicate_number'])
                is_valid = False
                response_errors.append({"pcrreplicatebatch": message})

        if is_valid:
            # now that all items are proven valid, save and return them to the user
            response_data = []
            for item in valid_data:
                item.save()
                response_data.append(item.data)
            return JsonResponse(response_data, safe=False, status=200)
        else:
            return JsonResponse(response_errors, safe=False, status=400)

    @action(methods=['post'], detail=False)
    def validate(self, request):
        validation_errors = []
        if 'analysis_batch' not in request.data:
            validation_errors.append("analysis_batch is required")
        if 'extraction_number' not in request.data:
            validation_errors.append("extraction_number is required")
        if 'target' not in request.data:
            validation_errors.append("target is required")
        if 'replicate_number' not in request.data:
            validation_errors.append("replicate_number is required")
        if len(validation_errors) > 0:
            return Response(validation_errors)

        extraction_batch = ExtractionBatch.objects.filter(
            analysis_batch=request.data['analysis_batch'],
            extraction_number=request.data['extraction_number']
        ).first()

        if not extraction_batch:
            message = "No extraction batch was found with analysis batch of " + str(request.data['analysis_batch'])
            message += " and extraction number of " + str(request.data['extraction_number'])
            return Response({"extraction_batch": message})

        pcrreplicate_batch = PCRReplicateBatch.objects.filter(
            extraction_batch=extraction_batch.id,
            target=request.data['target'],
            replicate_number=request.data['replicate_number']
        ).first()

        if not pcrreplicate_batch:
            message = "No PCR replicate batch was found with extraction batch of " + str(extraction_batch.id)
            message += " and target of " + str(request.data['target'])
            message += " and replicate number of " + str(request.data['replicate_number'])
            return Response({"pcrreplicate_batch": message}, status=400)

        rt = ReverseTranscription.objects.filter(extraction_batch=extraction_batch.id, re_rt=None).first()

        # start building up the response object
        field_validations = {"id": pcrreplicate_batch.id}

        # populate the response object with the submitted control values and the control validations
        control_fields = ['ext_neg_cq_value', 'ext_neg_gc_reaction', 'rt_neg_cq_value', 'rt_neg_gc_reaction',
                          'pcr_neg_cq_value', 'pcr_neg_gc_reaction', 'pcr_pos_cq_value', 'pcr_pos_gc_reaction']
        control_validations = []
        for field in control_fields:
                field_validations[field] = request.data[field] if field in request.data else None
                # exclude RT fields if there are no RTs related to this extraction batch
                if 'rt' not in field or rt:
                    validation_error = self.validate_controls(field)
                    if validation_error:
                        control_validations.append(validation_error)
        field_validations["validation_errors"] = control_validations

        # check that pcrreplicates have been submitted
        if 'updated_pcrreplicates' not in request.data or not request.data['updated_pcrreplicates']:
            field_validations["updated_pcrreplicates"] = [("updated_pcrreplicates is missing", 2)]
        else:
            # validate pcrreplicates
            existing_pcrreplicates = PCRReplicate.objects.filter(pcrreplicate_batch=pcrreplicate_batch.id)
            all_pcrreplicates_validations = []
            updated_pcrreplicates = request.data.get('updated_pcrreplicates')
            updated_pcrreplicates_sample_ids = [rep['sample'] for rep in updated_pcrreplicates]

            for existing_rep in existing_pcrreplicates:
                sample_id = existing_rep.sample_extraction.sample.id
                rep_validations = []

                # attempt to find the matching updated rep
                try:
                    rep_index = updated_pcrreplicates_sample_ids.index(sample_id)
                    # pop the matching updated rep from its list so that we eventually end up with an empty list,
                    # or a list of extraneous reps
                    updated_rep = updated_pcrreplicates.pop(rep_index)
                    # also remove the parallel sample ID so that the two lists continue to have matching indexes
                    del updated_pcrreplicates_sample_ids[rep_index]

                    # start building up the response object
                    response_rep = {"sample": sample_id}

                    rep_validations = []

                    # check if this rep has already been uploaded
                    if existing_rep.cq_value is not None:
                        message = "sample " + str(sample_id) + " has already been uploaded for this PCR replicate batch"
                        rep_validations.append(self.err_obj("cq_value", message, 1))

                    # validate cq_value
                    # remember that null is an acceptable value
                    if 'cq_value' not in updated_rep:
                        rep_validations.append(self.err_obj("cq_value", "cq_value ('cp') is missing", 2))
                    else:
                        rep_cq_value = updated_rep['cq_value']
                        response_rep['cq_value'] = rep_cq_value
                        if rep_cq_value is not None:
                            if not self.isnumber(rep_cq_value):
                                rep_validations.append(self.err_obj("cq_value", "cq_value ('cp') is not a number", 1))
                            elif rep_cq_value < Decimal('0'):
                                rep_validations.append(self.err_obj("cq_value", "cq_value ('cp') is less than zero", 2))

                    # validate gc_reaction
                    # remember that null is an acceptable value
                    if 'gc_reaction' not in updated_rep:
                        message = "gc_reaction ('concentration') is missing"
                        rep_validations.append(self.err_obj("gc_reaction", message, 2))
                    else:
                        rep_gc_reaction = updated_rep['gc_reaction']
                        response_rep['gc_reaction'] = rep_gc_reaction
                        if rep_gc_reaction is not None:
                            if not self.isnumber(rep_gc_reaction):
                                message = "gc_reaction ('concentration') is not a number"
                                rep_validations.append(self.err_obj("gc_reaction", message, 1))
                                response_rep['gc_reaction_sci'] = ''
                            elif rep_gc_reaction < Decimal('0'):
                                message = "gc_reaction ('concentration') is less than zero"
                                rep_validations.append(self.err_obj("gc_reaction", message, 2))
                                response_rep['gc_reaction_sci'] = get_sci_val(rep_gc_reaction)
                            else:
                                response_rep['gc_reaction_sci'] = get_sci_val(rep_gc_reaction)
                        else:
                            response_rep['gc_reaction'] = None
                            response_rep['gc_reaction_sci'] = ''

                    response_rep['validation_errors'] = rep_validations
                    all_pcrreplicates_validations.append(response_rep)

                # no matching updated_rep was found
                except ValueError:
                    # start building up the response object
                    response_rep = {"sample": sample_id}

                    message = "sample " + str(sample_id) + " expected but not found in submission"
                    rep_validations.append(self.err_obj("sample", message, 2))

                    response_rep['validation_errors'] = rep_validations
                    all_pcrreplicates_validations.append(response_rep)

            # now list out the other updated reps that were submitted but do not belong to this batch
            for extraneous_rep in updated_pcrreplicates:
                rep_validations = []
                sample_id = "(No Sample ID)"
                if 'sample' not in extraneous_rep or extraneous_rep['sample'] is None:
                    validation_error = self.err_obj("sample", "sample is a required field", 1)
                else:
                    sample_id = str(extraneous_rep.get('sample'))
                    message = "sample " + sample_id + " is not in this PCR replicate batch"
                    validation_error = self.err_obj("sample", message, 1)

                # start building up the response object
                response_rep = {"sample": sample_id}
                if 'cq_value' not in extraneous_rep:
                    continue
                else:
                    rep_cq_value = extraneous_rep['cq_value']
                    response_rep['cq_value'] = rep_cq_value
                if 'gc_reaction' not in extraneous_rep:
                    continue
                else:
                    rep_gc_reaction = extraneous_rep['gc_reaction']
                    response_rep['gc_reaction'] = rep_gc_reaction
                    if not self.isnumber(rep_gc_reaction):
                        response_rep['gc_reaction_sci'] = ''
                    else:
                        response_rep['gc_reaction_sci'] = get_sci_val(rep_gc_reaction)

                rep_validations.append(validation_error)
                response_rep['validation_errors'] = rep_validations
                all_pcrreplicates_validations.append(response_rep)

            field_validations["updated_pcrreplicates"] = all_pcrreplicates_validations

        return JsonResponse(field_validations, safe=False, status=200)

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
                        response_errors.append({"inhibition": "No Inhibition exists with this ID: " + str(inhib)})
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
                return JsonResponse({"inhibition": "No Inhibition exists with this ID: " + str(pk)}, status=400)


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
                        diff = abs(pos - cq)
                        # If INH CONT Cq minus Sample Cq<2 cycles, then dilution factor = 1 (no dilution)
                        # If INH CONT Cq minus Sample Cq>=2 cycles AND Sample Cq<36, then dilution factor = 5
                        # If INH CONT Cq minus Sample Cq>2 cycles AND Sample Cq>36 or no Cq, then dilution factor = 10
                        if 0.0 <= diff < 2.0:
                            suggested_dilution_factor = 1
                        elif diff >= 2.0 and cq < 36.0:
                            suggested_dilution_factor = 5
                        elif diff > 2.0 and cq > 36.0:
                            suggested_dilution_factor = 10
                        # if 0.0 <= diff <= 1.0:
                        #     suggested_dilution_factor = 1
                        # if cq > pos and diff < 2.0:
                        #     suggested_dilution_factor = 1
                        # if diff >= 2.0 and cq <= 36.0:
                        #     suggested_dilution_factor = 5
                        # if cq > 36.0 or cq is None:
                        #     suggested_dilution_factor = 10
                        new_data = {"id": inhib.id, "sample": sample,
                                    "suggested_dilution_factor": suggested_dilution_factor}
                        response_data.append(new_data)
                    else:
                        is_valid = False
                        message = "No Inhibition exists with Sample ID: " + str(sample)
                        message += ", Extraction Batch ID: " + str(eb) + ", Nucleic Acid Type ID: " + str(na)
                        response_errors.append({"inhibition": message})
                if is_valid:
                    return JsonResponse(response_data, safe=False, status=200)
                else:
                    return JsonResponse(response_errors, safe=False, status=400)
            return Response(serializer.errors, status=400)
        else:
            message = "No Extraction Batch exists with Analysis Batch ID: " + str(ab)
            message += " and Extraction Number: " + str(en)
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
