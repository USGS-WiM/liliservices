from collections import Counter, OrderedDict
from django.http import JsonResponse
from django.db.models import F, Q, Case, When, Value, Count, Sum, Min, Max, Avg, FloatField, CharField
from django.db.models.functions import Cast
from django.contrib.postgres.aggregates import StringAgg
from rest_framework import views, viewsets, permissions, authentication, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.parsers import JSONParser
from rest_framework.exceptions import APIException
from lideservices.serializers import *
from lideservices.models import *
from lideservices.permissions import *
from lideservices.aggregates import *


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
    def finalsamplemeanconcentrations(self, request):
        queryset = Sample.objects.prefetch_related('finalsamplemeanconcentrations').distinct()
        query_params = self.request.query_params
        # filter by sample IDs, exact list
        sample = query_params.get('sample', None)
        if sample is not None:
            if LIST_DELIMETER in sample:
                sample_list = sample.split(LIST_DELIMETER)
                queryset = queryset.filter(id__in=sample_list)
            else:
                queryset = queryset.filter(id__exact=sample)
        # filter by target IDs, exact list
        target = query_params.get('target', None)
        target_list = []
        if target is not None:
            if LIST_DELIMETER in target:
                target_list = target.split(LIST_DELIMETER)
                queryset = queryset.filter(finalsamplemeanconcentrations__target__in=target_list)
            else:
                target_list = [target]
                queryset = queryset.filter(finalsamplemeanconcentrations__target__exact=target)

        # recalc reps validity
        for sample in queryset:
            fsmcs = FinalSampleMeanConcentration.objects.filter(sample=sample.id, target__in=target_list)
            for fsmc in fsmcs:
                recalc_reps('FinalSampleMeanConcentration', sample.id, target=fsmc.target.id, recalc_rep_conc=False)

        # start building up the response object
        resp = []
        for sample in queryset:
            sample_target_list = [int(target) for target in target_list]
            item = {
                "id": sample.id,
                "collaborator_sample_id": sample.collaborator_sample_id,
                "collection_start_date": sample.collection_start_date,
                "final_sample_mean_concentrations": []
            }
            fsmcs = list(FinalSampleMeanConcentration.objects.filter(sample=sample.id))
            for fsmc in fsmcs:
                # attempt to find the matching target in the fsmc list
                try:
                    sample_target_index = sample_target_list.index(fsmc.target.id)
                    # pop the matching fsmc target from its list so that we eventually end up with an empty list,
                    # or a list of extraneous targets
                    sample_target_list.pop(sample_target_index)

                    # start building up the nested response object
                    item["final_sample_mean_concentrations"].append({
                        "target": fsmc.target.id,
                        "target_string": fsmc.target.name,
                        "final_sample_mean_concentration": fsmc.final_sample_mean_concentration
                    })
                # no matching target was found in the fsmc list
                except ValueError:
                    # do not include this fsmc in the response because its target was not requested
                    continue
            # now list out the other targets that were requested but do not exist for this sample
            for extraneous_target in sample_target_list:
                # start building up the nested response object
                target_name = list(Target.objects.filter(id=extraneous_target).values_list('name', flat=True))
                item["final_sample_mean_concentrations"].append({
                    "target": extraneous_target,
                    "target_string": target_name[0],
                    "final_sample_mean_concentration": "N/A"
                })
            resp.append(item)

        return Response(resp)

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
        # filter by peg_neg, exact list
        peg_neg = query_params.get('peg_neg', None)
        if peg_neg is not None:
            if LIST_DELIMETER in peg_neg:
                peg_neg_list = peg_neg.split(LIST_DELIMETER)
                queryset = queryset.filter(peg_neg__in=peg_neg_list)
            else:
                queryset = queryset.filter(peg_neg__exact=peg_neg)
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
        # get the first empty box in the any freezer
        first_empty_box = FreezerLocation.objects.get_first_empty_box()
        if first_empty_box is None:
            first_empty_box = "There are no more empty boxes in this freezer!"
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
                next_empty_box = FreezerLocation.objects.get_next_empty_box(last_spot)
                # then add the next empty box to the response object
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
            resp.update({"next_empty_box": first_empty_box})
        return Response(resp)


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

    @action(detail=False)
    def summary_statistics(self, request):

        STATISTICS = ['sample_count', 'positive_count', 'percent_positive', 'max_concentration', 'min_concentration',
                      'median_concentration', 'average_concentration', 'min_concentration_positive',
                      'median_concentration_positive', 'average_concentration_positive']

        queryset = FinalSampleMeanConcentration.objects.all()
        query_params = request.query_params
        # filter by sample IDs, exact list
        sample = query_params.get('sample', None)
        if sample is not None:
            if LIST_DELIMETER in sample:
                sample_list = sample.split(LIST_DELIMETER)
                queryset = queryset.filter(sample__in=sample_list)
            else:
                queryset = queryset.filter(sample__exact=sample)
        # filter by target IDs, exact list
        target = query_params.get('target', None)
        if target is not None:
            if LIST_DELIMETER in target:
                target_list = target.split(LIST_DELIMETER)
                queryset = queryset.filter(target__in=target_list)
            else:
                queryset = queryset.filter(target__exact=target)
        # get the requested statistics, exact list
        statistic = query_params.get('statistic', None)
        statistic_list = statistic.split(LIST_DELIMETER) if statistic is not None else STATISTICS

        # set aside a parallel query for totals
        totals_queryset = queryset

        # recalc reps validity
        for fsmc in queryset:
            recalc_reps('FinalSampleMeanConcentration', fsmc.sample.id, target=fsmc.target.id, recalc_rep_conc=False)

        # group by target name
        queryset = queryset.values(target_name=F('target__name')).order_by('target_name')

        # include the target id
        queryset = queryset.annotate(target_id=F('target__id'))

        # initialize the totals row and include the totals target id field to match the main queryset for later merging
        totals = {'target_name': 'All targets', 'target_id': None}

        # calculate the requested statistics per object
        if ('sample_count' in statistic_list
                or ('percent_positive' in statistic_list and 'sample_count' not in statistic_list)):
            # include the sample_count by target
            queryset = queryset.annotate(sample_count=Count('id'))
            # include the sample_count for all targets
            totals['sample_count'] = totals_queryset.aggregate(Count('sample_id', distinct=True))['sample_id__count']
        if ('positive_count' in statistic_list
                or ('percent_positive' in statistic_list and 'positive_count' not in statistic_list)):
            # include the positive_count by target
            queryset = queryset.annotate(positive_count=Count('id', filter=Q(final_sample_mean_concentration__gt=0)))
            # include the positive_count for all targets
            totals['positive_count'] = queryset.aggregate(Count('positive_count'))['positive_count__count']
        if 'percent_positive' in statistic_list:
            # include the percent_positive by target
            queryset = queryset.annotate(
                percent_positive=(Cast('positive_count', FloatField()) / Cast('sample_count', FloatField()) * 100))
            # include the percent_positive for all targets
            pos_count = queryset.aggregate(Count('positive_count'))['positive_count__count']
            samp_count = totals_queryset.aggregate(Count('sample_id', distinct=True))['sample_id__count']
            totals['percent_positive'] = (pos_count / samp_count) * 100 if pos_count else 0
        if 'max_concentration' in statistic_list:
            # include the max_concentration by target
            queryset = queryset.annotate(max_concentration=Max('final_sample_mean_concentration'))
            # include the max_concentration for all targets
            totals['max_concentration'] = totals_queryset.aggregate(
                Max('final_sample_mean_concentration'))['final_sample_mean_concentration__max']
        if 'min_concentration' in statistic_list:
            # include the min_concentration by target
            queryset = queryset.annotate(min_concentration=Min('final_sample_mean_concentration'))
            # include the min_concentration for all targets
            totals['min_concentration'] = totals_queryset.aggregate(
                Min('final_sample_mean_concentration'))['final_sample_mean_concentration__min']
        if 'median_concentration' in statistic_list:
            # include the median_concentration by target
            queryset = queryset.annotate(median_concentration=Median('final_sample_mean_concentration'))
            # include the median_concentration for all targets
            totals['median_concentration'] = totals_queryset.aggregate(
                Median('final_sample_mean_concentration'))['final_sample_mean_concentration__median']
        if 'average_concentration' in statistic_list:
            # include the average_concentration by target
            queryset = queryset.annotate(average_concentration=Avg('final_sample_mean_concentration'))
            # include the average_concentration for all targets
            totals['average_concentration'] = totals_queryset.aggregate(
                Avg('final_sample_mean_concentration'))['final_sample_mean_concentration__avg']
        if 'min_concentration_positive' in statistic_list:
            # include the min_concentration_positive by target
            queryset = queryset.annotate(
                min_concentration_positive=Min('final_sample_mean_concentration',
                                               filter=Q(final_sample_mean_concentration__gt=0)))
            # include the min_concentration_positive for all targets
            totals['min_concentration_positive'] = totals_queryset.aggregate(
                final_sample_mean_concentration__min=Min('final_sample_mean_concentration', filter=Q(
                    final_sample_mean_concentration__gt=0)))['final_sample_mean_concentration__min']
        if 'median_concentration_positive' in statistic_list:
            # include the median_concentration_positive by target
            queryset = queryset.annotate(median_concentration_positive=Median(
                'final_sample_mean_concentration', filter=Q(final_sample_mean_concentration__gt=0)))
            # include the median_concentration_positive for all targets
            totals['median_concentration_positive'] = totals_queryset.aggregate(
                final_sample_mean_concentration__median=Median('final_sample_mean_concentration', filter=Q(
                    final_sample_mean_concentration__gt=0)))['final_sample_mean_concentration__median']
        if 'average_concentration_positive' in statistic_list:
            # include the average_concentration_positive by target
            queryset = queryset.annotate(
                average_concentration_positive=Avg('final_sample_mean_concentration',
                                                   filter=Q(final_sample_mean_concentration__gt=0)))
            # include the average_concentration_positive for all targets
            totals['average_concentration_positive'] = totals_queryset.aggregate(
                final_sample_mean_concentration__avg=Avg('final_sample_mean_concentration', filter=Q(
                    final_sample_mean_concentration__gt=0)))['final_sample_mean_concentration__avg']

        resp = list(queryset)
        resp.append(totals)

        return Response(resp)

    @action(detail=False)
    def results(self, request):
        query_params = self.request.query_params
        data = FinalSampleMeanConcentrationResultsSerializer(self.build_queryset(query_params), many=True).data
        return Response(data)

    # override the default queryset to allow filtering by URL arguments
    def get_queryset(self):
        query_params = self.request.query_params
        return self.build_queryset(query_params)

    # build a queryset using query_params
    # NOTE: this is being done in its own method to adhere to the DRY Principle
    def build_queryset(self, query_params):
        queryset = FinalSampleMeanConcentration.objects.all()
        # filter by sample ID, exact list
        sample = query_params.get('sample', None)
        if sample is not None:
            sample_list = sample.split(',')
            queryset = queryset.filter(sample__in=sample_list)
        # filter by target ID, exact list
        target = query_params.get('target', None)
        if target is not None:
            target_list = target.split(',')
            queryset = queryset.filter(target__in=target_list)
        # filter by study ID, exact list
        study = query_params.get('study', None)
        if study is not None:
            study_list = sample.split(',')
            queryset = queryset.filter(sample__study__in=study_list)
        # filter by collection_start_date, exact list
        collection_start_date = query_params.get('collection_start_date', None)
        if collection_start_date is not None:
            collection_start_date_list = sample.split(',')
            queryset = queryset.filter(sample__collection_start_date__in=collection_start_date_list)
        # filter by collaborator_sample_id, exact list
        collaborator_sample_id = query_params.get('collaborator_sample_id', None)
        if collaborator_sample_id is not None:
            collaborator_sample_id_list = sample.split(',')
            queryset = queryset.filter(sample__collaborator_sample_id__in=collaborator_sample_id_list)

        # recalc reps validity
        for fsmc in queryset:
            recalc_reps('FinalSampleMeanConcentration', fsmc.sample.id, target=fsmc.target.id, recalc_rep_conc=False)

        return queryset

    # override the default GET method to recalc all child PCR Replicates first before the FSMC Select query
    def retrieve(self, request, *args, **kwargs):
        recalc_reps('FinalSampleMeanConcentration',
                    self.get_object().sample.id, target=self.get_object().target.id, recalc_rep_conc=False)
        return super(FinalSampleMeanConcentrationViewSet, self).retrieve(request, *args, **kwargs)


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

    # override the default DELETE method to prevent deletion of an AnalysisBatch with any results data entered
    def destroy(self, request, *args, **kwargs):
        nonnull_pcrreplicates = PCRReplicate.objects.filter(
            pcrreplicate_batch__extraction_batch__analysis_batch=self.get_object().id).exclude(cq_value__isnull=True)
        if any(nonnull_pcrreplicates):
            message = "An Analysis Batch may not be deleted if any related PCR Replicates have results data entered."
            raise APIException(message)
        return super(AnalysisBatchViewSet, self).destroy(request, *args, **kwargs)


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

    # override the default DELETE method to prevent deletion of an ExtractionBatch with any results data entered
    def destroy(self, request, *args, **kwargs):
        nonnull_pcrreplicates = PCRReplicate.objects.filter(
            pcrreplicate_batch__extraction_batch=self.get_object().id).exclude(cq_value__isnull=True)
        if any(nonnull_pcrreplicates):
            message = "An Extraction Batch may not be deleted if any related PCR Replicates have results data entered."
            raise APIException(message)
        return super(ExtractionBatchViewSet, self).destroy(request, *args, **kwargs)

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

                    # remove nulls coming from client (user not actually sending nulls, so no need to trigger recalcs)
                    if 'ext_pos_rna_rt_cq_value' in item and item['ext_pos_rna_rt_cq_value'] is None:
                        item.pop('ext_pos_rna_rt_cq_value')
                    if 'ext_pos_dna_cq_value' in item and item['ext_pos_dna_cq_value'] is None:
                        item.pop('ext_pos_dna_cq_value')

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

    # override the default DELETE method to prevent deletion of a ReverseTranscription with any results data entered
    def destroy(self, request, *args, **kwargs):
        nonnull_pcrreplicates = PCRReplicate.objects.filter(
            pcrreplicate_batch__extraction_batch__reversetranscriptions=self.get_object().id).exclude(
            cq_value__isnull=True)
        if any(nonnull_pcrreplicates):
            message = "A Reverse Transcription may not be deleted"
            message += " if any related PCR Replicates have results data entered."
            raise APIException(message)
        return super(ReverseTranscriptionViewSet, self).destroy(request, *args, **kwargs)

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

    @action(detail=False)
    def inhibition_report(self, request):
        queryset = SampleExtraction.objects.all()
        sample = request.query_params.get('sample', None)
        if sample is not None:
            if LIST_DELIMETER in sample:
                sample_list = sample.split(',')
                queryset = queryset.filter(sample__in=sample_list)
            else:
                queryset = queryset.filter(sample__exact=sample)
        # recalc not needed here because the report shows inhibition data, not PCR replicate data
        # # recalc reps validity
        # for sampleext in queryset:
        #     recalc_reps('SampleExtraction', sampleext.id, recalc_rep_conc=False)
        data = SampleExtractionReportSerializer(queryset, many=True).data
        return Response(data)

    # override the default DELETE method to prevent deletion of a SampleExtraction with any results data entered
    def destroy(self, request, *args, **kwargs):
        nonnull_pcrreplicates = PCRReplicate.objects.filter(
            sample_extraction=self.get_object().id).exclude(cq_value__isnull=True)
        if any(nonnull_pcrreplicates):
            message = "A Sample Extraction may not be deleted if any related PCR Replicates have results data entered."
            raise APIException(message)
        return super(SampleExtractionViewSet, self).destroy(request, *args, **kwargs)


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
            elif self.request.data[field] > Decimal('0') and field not in ['pcr_pos_cq_value', 'pcr_pos_gc_reaction']:
                # eventually we will also validate pcr_pos_cq_value by testing if it is >0.5 cylces from expected
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
                if not is_valid:
                    continue
                else:
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
                    item['updated_pcrreplicates'] = []

                    pcrreplicates = PCRReplicate.objects.filter(pcrreplicate_batch=pcrreplicate_batch.id)
                    for rep in pcrreplicates:
                        item['updated_pcrreplicates'].append(
                            {"sample": rep.sample_extraction.sample.id, "cq_value": 0, "gc_reaction": 0})

                    serializer = self.serializer_class(pcrreplicate_batch, data=item, partial=True)
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
                # recalc the child rep validity
                reps = PCRReplicate.objects.filter(pcrreplicate_batch=item.data['id'])
                for rep in reps:
                    rep.invalid = rep.calc_invalid()
                    rep.save()
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

        target = Target.objects.filter(id=request.data['target']).first()

        if not target:
            message = "No target was found with ID of " + str(request.data['target'])
            return Response({"target": message})

        pcrreplicate_batch = PCRReplicateBatch.objects.filter(
            extraction_batch=extraction_batch.id,
            target=target.id,
            replicate_number=request.data['replicate_number']
        ).first()

        if not pcrreplicate_batch:
            message = "No PCR replicate batch was found with extraction batch of " + str(extraction_batch.id)
            message += " and target of " + str(request.data['target'])
            message += " and replicate number of " + str(request.data['replicate_number'])
            return Response({"pcrreplicate_batch": message}, status=400)

        rna = True if target.nucleic_acid_type.name == 'RNA' else False

        # start building up the response object
        field_validations = {
            "id": pcrreplicate_batch.id,
            "ext_neg_invalid": False,
            "rt_neg_invalid": False,
            "pcr_neg_invalid": False,
            "pcr_pos_invalid": False
        }

        # populate the response object with the submitted control values and the control validations
        control_fields = ['ext_neg_cq_value', 'ext_neg_gc_reaction', 'rt_neg_cq_value', 'rt_neg_gc_reaction',
                          'pcr_neg_cq_value', 'pcr_neg_gc_reaction', 'pcr_pos_cq_value', 'pcr_pos_gc_reaction']
        control_validations = []
        for field in control_fields:
            field_validations[field] = request.data[field] if field in request.data else None
            # exclude RT fields if this is a DNA target
            if 'rt' not in field or rna:
                validation_error = self.validate_controls(field)
                if validation_error:
                    control_validations.append(validation_error)
                    if "ext_neg" in field:
                        field_validations["ext_neg_invalid"] = True
                    elif "rt_neg" in field:
                        field_validations["rt_neg_invalid"] = True
                    elif "pcr_neg" in field:
                        field_validations["pcr_neg_invalid"] = True
                    elif "pcr_pos" in field:
                        field_validations["pcr_pos_invalid"] = True
        field_validations["validation_errors"] = control_validations

        # check that pcrreplicates have been submitted
        if 'updated_pcrreplicates' not in request.data or not request.data['updated_pcrreplicates']:
            field_validations["updated_pcrreplicates"] = [("updated_pcrreplicates is missing", 2)]
        else:
            # validate pcrreplicates
            existing_pcrreplicates = PCRReplicate.objects.filter(
                pcrreplicate_batch=pcrreplicate_batch.id).order_by('sample_extraction__sample__id')
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

    # override the default DELETE method to prevent deletion of a PCRReplicateBatch with any results data entered
    def destroy(self, request, *args, **kwargs):
        nonnull_pcrreplicates = PCRReplicate.objects.filter(
            pcrreplicate_batch=self.get_object().id).exclude(cq_value__isnull=True)
        if any(nonnull_pcrreplicates):
            message = "A PCR Replicate Batch may not be deleted"
            message += " if any related PCR Replicates have results data entered."
            raise APIException(message)
        return super(PCRReplicateBatchViewSet, self).destroy(request, *args, **kwargs)


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

    # override the default DELETE method to prevent deletion of an Inhibition with any results data entered
    def destroy(self, request, *args, **kwargs):
        nonnull_pcrreplicates_dna = PCRReplicate.objects.filter(
            sample_extraction__inhibition_dna=self.get_object().id).exclude(cq_value__isnull=True)
        nonnull_pcrreplicates_rna = PCRReplicate.objects.filter(
            sample_extraction__inhibition_rna=self.get_object().id).exclude(cq_value__isnull=True)
        nonnull_pcrreplicates = nonnull_pcrreplicates_dna.union(nonnull_pcrreplicates_rna).distinct()
        if any(nonnull_pcrreplicates):
            message = "An Inhibition may not be deleted if any related PCR Replicates have results data entered."
            raise APIException(message)
        return super(InhibitionViewSet, self).destroy(request, *args, **kwargs)

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
                        if not cq:
                            suggested_dilution_factor = 10
                        elif 0.0 <= diff < 2.0:
                            suggested_dilution_factor = 1
                        elif diff >= 2.0 and cq < 36.0:
                            suggested_dilution_factor = 5
                        elif diff > 2.0 and cq > 36.0:
                            suggested_dilution_factor = 10
                        new_data = {"id": inhib.id, "sample": sample, "cq_value": cq,
                                    "suggested_dilution_factor": suggested_dilution_factor,
                                    "extraction_batch": eb.id}
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


######
#
#  Reports
#
######


class QualityControlReportView(views.APIView):
    permission_classes = (permissions.IsAuthenticated,)

    def post(self, request):
        queryset = Sample.objects.all()
        request_data = JSONParser().parse(request)
        resp = {}

        samples = request_data.get('samples', None)
        if samples is not None:
            queryset = queryset.filter(id__in=samples)

        # recalc reps validity
        for sample in queryset:
            recalc_reps('Sample', sample.id, recalc_rep_conc=False)

        matrix_counts = queryset.values('matrix__name').order_by().annotate(count=Count('matrix'))
        sample_type_counts = queryset.values('sample_type__name').order_by().annotate(count=Count('sample_type'))
        total_volume_sampled_unit_initial_counts = queryset.values(
            'total_volume_sampled_unit_initial__name').order_by().annotate(
            count=Count('total_volume_sampled_unit_initial'))
        post_dilution_volume_min = queryset.aggregate(min=Min('post_dilution_volume'))
        post_dilution_volume_max = queryset.aggregate(max=Max('post_dilution_volume'))
        total_volume_or_mass_sampled_min = queryset.aggregate(min=Min('total_volume_or_mass_sampled'))
        total_volume_or_mass_sampled_max = queryset.aggregate(max=Max('total_volume_or_mass_sampled'))
        final_concentrated_sample_volume_min = queryset.aggregate(
            min=Min('finalconcentratedsamplevolume__final_concentrated_sample_volume'))
        final_concentrated_sample_volume_max = queryset.aggregate(
            max=Max('finalconcentratedsamplevolume__final_concentrated_sample_volume'))

        # Sample-level QC summary stats
        sample_stats = []
        for matrix in matrix_counts:
            sample_stats.append({
                "metric": "Sample Matrix",
                "value": matrix['matrix__name'],
                "count": matrix['count'],
                "min": None,
                "max": None
            })
        for sample_type in sample_type_counts:
            sample_stats.append({
                "metric": "Sample Type",
                "value": sample_type['sample_type__name'],
                "count": sample_type['count'],
                "min": None,
                "max": None
            })
        for unit in total_volume_sampled_unit_initial_counts:
            sample_stats.append({
                "metric": "Total Volume Sampled Unit Initial",
                "value": unit['total_volume_sampled_unit_initial__name'],
                "count": unit['count'],
                "min": None,
                "max": None
            })
        sample_stats.append({
            "metric": "Post Dilution Volume",
            "value": None,
            "count": None,
            "min": post_dilution_volume_min['min'],
            "max": post_dilution_volume_max['max']
        })
        sample_stats.append({
            "metric": "Total Volume or Mass Sampled",
            "value": None,
            "count": None,
            "min": total_volume_or_mass_sampled_min['min'],
            "max": total_volume_or_mass_sampled_max['max']
        })
        sample_stats.append({
            "metric": "Final Concentrated Sample Volume",
            "value": None,
            "count": None,
            "min": final_concentrated_sample_volume_min['min'],
            "max": final_concentrated_sample_volume_max['max']
        })
        resp['sample_quality_control'] = sample_stats

        # ExtractionBatch-level raw values
        if samples is not None:
            eb_raw_data = ExtractionBatch.objects.filter(analysis_batch__samples__in=samples)
        else:
            eb_raw_data = ExtractionBatch.objects.all()

        # recalc reps validity
        for eb in eb_raw_data:
            recalc_reps('ExtractionBatch', eb.id, recalc_rep_conc=False)

        eb_raw_data = eb_raw_data.filter(reversetranscriptions__re_rt__isnull=True).annotate(
            rt_template_volume=F('reversetranscriptions__template_volume'))
        eb_raw_data = eb_raw_data.filter(reversetranscriptions__re_rt__isnull=True).annotate(
            rt_reaction_volume=F('reversetranscriptions__reaction_volume'))

        eb_raw_data = eb_raw_data.values('analysis_batch', 'extraction_number', 'extraction_volume', 'elution_volume',
                                         'rt_template_volume', 'rt_reaction_volume', 'qpcr_template_volume',
                                         'qpcr_reaction_volume'
                                         ).order_by('analysis_batch', 'extraction_number').distinct()
        resp['extraction_raw_data'] = list(eb_raw_data)

        # ExtractionBatch-level QC summary stats
        extraction_volumes = Counter(list(eb_raw_data.values_list('extraction_volume', flat=True)))
        elution_volumes = Counter(list(eb_raw_data.values_list('elution_volume', flat=True)))
        rt_template_volumes = Counter(list(eb_raw_data.values_list('rt_template_volume', flat=True)))
        rt_reaction_volumes = Counter(list(eb_raw_data.values_list('rt_reaction_volume', flat=True)))
        qpcr_template_volumes = Counter(list(eb_raw_data.values_list('qpcr_template_volume', flat=True)))
        qpcr_reaction_volumes = Counter(list(eb_raw_data.values_list('qpcr_reaction_volume', flat=True)))

        extraction_stats = []
        for key, value in extraction_volumes.items():
            extraction_stats.append({
                "metric": "Extraction Volume",
                "value": key,
                "count": value
            })
        for key, value in elution_volumes.items():
            extraction_stats.append({
                "metric": "Elution Volume",
                "value": key,
                "count": value
            })
        for key, value in rt_template_volumes.items():
            extraction_stats.append({
                "metric": "RT Template Volume",
                "value": key,
                "count": value
            })
        for key, value in rt_reaction_volumes.items():
            extraction_stats.append({
                "metric": "RT Reaction Volume",
                "value": key,
                "count": value
            })
        for key, value in qpcr_template_volumes.items():
            extraction_stats.append({
                "metric": "qPCR Template Volume",
                "value": key,
                "count": value
            })
        for key, value in qpcr_reaction_volumes.items():
            extraction_stats.append({
                "metric": "qPCR Reaction Volume",
                "value": key,
                "count": value
            })
        resp['extraction_quality_control'] = extraction_stats

        return Response(resp)


class ControlsResultsReportView(views.APIView):
    permission_classes = (permissions.IsAuthenticated,)

    def post(self, request):
        # samples = Sample.objects.all()
        targets = Target.objects.all().values('id', 'name').order_by('name')
        request_data = JSONParser().parse(request)
        sample_ids = request_data.get('samples', None)
        # if sample_ids:
        #     samples = Sample.objects.filter(id__in=sample_ids)
        target_ids = request_data.get('targets', None)
        if target_ids:
            targets = Target.objects.filter(id__in=target_ids).values('id', 'name').order_by('name')
        target_names = [target['name'] for target in targets]

        # recalc reps validity once for use by all the control queries below
        queryset = PCRReplicateBatch.objects.all()
        if sample_ids:
            queryset = queryset.filter(pcrreplicates__sample_extraction__sample__in=sample_ids)
        if target_ids:
            queryset = queryset.filter(target__in=target_ids)
        for pcrrep_batch in queryset:
            recalc_reps('PCRReplicateBatch', pcrrep_batch.id, recalc_rep_conc=False)

        pos = "Positive"
        neg = "Negative"
        nr = "No Result"
        na = "Not Analyzed"

        # PCRReplicateBatch-level controls
        # Ext Neg
        ext_negs = PCRReplicateBatch.objects.all().annotate(
            result=Case(
                When(rt_neg_cq_value__gt=0, then=Value(pos)),
                When(ext_neg_cq_value__gt=0, then=Value(pos)),
                When(ext_neg_cq_value__exact=0, then=Value(neg)),
                default=Value(nr), output_field=CharField()
            )).annotate(pcrreplicate_batch=F('id')).values(
            'extraction_batch__id', 'extraction_batch__analysis_batch', 'extraction_batch__analysis_batch__name',
            'extraction_batch__extraction_number', 'replicate_number', 'target__name', 'pcrreplicate_batch', 'result'
        ).order_by('extraction_batch__analysis_batch', 'extraction_batch__id')
        if sample_ids:
            ext_negs = ext_negs.filter(pcrreplicates__sample_extraction__sample__in=sample_ids)
        if target_ids:
            ext_negs = ext_negs.filter(target__in=target_ids)
        ext_neg_results = {}
        for ext_neg in ext_negs:
            # if the EB is already included in our local dict, just append the current target to it
            if ext_neg_results.get(ext_neg['extraction_batch__id'], None) is not None:
                data = ext_neg_results[ext_neg['extraction_batch__id']]
                data[ext_neg['target__name']] = ext_neg['result']
            # otherwise, add the EB to our local dict and append the current target to it
            else:
                data = {
                    "analysis_batch_string": ext_neg['extraction_batch__analysis_batch__name'],
                    "analysis_batch": ext_neg['extraction_batch__analysis_batch'],
                    "extraction_number": ext_neg['extraction_batch__extraction_number'],
                    # "replicate_number": ext_neg['replicate_number'],
                    "pcrreplicate_batch": ext_neg['pcrreplicate_batch'],
                    ext_neg['target__name']: ext_neg['result']
                }
            ext_neg_results[ext_neg['extraction_batch__id']] = data
        # convert the dict of dicts into a list of dicts
        ext_neg_results_list = list(ext_neg_results.values())
        ext_neg_results_list_ordered = []
        # include targets not analyzed
        for ext_neg_result in ext_neg_results_list:
            for target in targets:
                if target['name'] not in ext_neg_result:
                    ext_neg_result[target['name']] = na
            ext_neg_result_ids = OrderedDict({
                "analysis_batch": ext_neg_result.pop('analysis_batch'),
                "analysis_batch_string": ext_neg_result.pop('analysis_batch_string'),
                "extraction_number": ext_neg_result.pop('extraction_number'),
                "pcrreplicate_batch": ext_neg_result.pop('pcrreplicate_batch')
            })
            ext_neg_result_targets = OrderedDict(sorted(ext_neg_result.items()))
            ext_neg_results_list_ordered.append(OrderedDict(**ext_neg_result_ids, **ext_neg_result_targets))

        # PCR Neg
        pcr_negs = PCRReplicateBatch.objects.all().annotate(
            result=Case(
                When(pcr_neg_cq_value__gt=0, then=Value(pos)),
                When(pcr_neg_cq_value__exact=0, then=Value(neg)),
                default=Value(nr), output_field=CharField()
            )).annotate(pcrreplicate_batch=F('id')).values(
            'extraction_batch__id', 'extraction_batch__analysis_batch', 'extraction_batch__analysis_batch__name',
            'extraction_batch__extraction_number', 'replicate_number', 'target__name', 'pcrreplicate_batch', 'result'
        ).order_by('extraction_batch__analysis_batch', 'extraction_batch__id')
        if sample_ids:
            pcr_negs = pcr_negs.filter(pcrreplicates__sample_extraction__sample__in=sample_ids)
        if target_ids:
            pcr_negs = pcr_negs.filter(target__in=target_ids)
        pcr_neg_results = {}
        for pcr_neg in pcr_negs:
            # if the EB is already included in our local dict, just append the current target to it
            if pcr_neg_results.get(pcr_neg['extraction_batch__id'], None) is not None:
                data = pcr_neg_results[pcr_neg['extraction_batch__id']]
                data[pcr_neg['target__name']] = pcr_neg['result']
            # otherwise, add the EB to our local dict and append the current target to it
            else:
                data = {
                    "analysis_batch_string": pcr_neg['extraction_batch__analysis_batch__name'],
                    "analysis_batch": pcr_neg['extraction_batch__analysis_batch'],
                    "extraction_number": pcr_neg['extraction_batch__extraction_number'],
                    # "replicate_number": pcr_neg['replicate_number'],
                    "pcrreplicate_batch": pcr_neg['pcrreplicate_batch'],
                    pcr_neg['target__name']: pcr_neg['result']
                }
            pcr_neg_results[pcr_neg['extraction_batch__id']] = data
        # convert the dict of dicts into a list of dicts
        pcr_neg_results_list = list(pcr_neg_results.values())
        pcr_neg_results_list_ordered = []
        # include targets not analyzed
        for pcr_neg_result in pcr_neg_results_list:
            for target in targets:
                if target['name'] not in pcr_neg_result:
                    pcr_neg_result[target['name']] = na
            pcr_neg_result_ids = OrderedDict({
                "analysis_batch": pcr_neg_result.pop('analysis_batch'),
                "analysis_batch_string": pcr_neg_result.pop('analysis_batch_string'),
                "extraction_number": pcr_neg_result.pop('extraction_number'),
                "pcrreplicate_batch": pcr_neg_result.pop('pcrreplicate_batch')
            })
            pcr_neg_result_targets = OrderedDict(sorted(pcr_neg_result.items()))
            pcr_neg_results_list_ordered.append(OrderedDict(**pcr_neg_result_ids, **pcr_neg_result_targets))

        # PCR Pos
        pcr_poss = PCRReplicateBatch.objects.all().annotate(
            result=Case(
                When(pcr_pos_cq_value__gt=0, then=Value('pcr_pos_cq_value')),
                When(pcr_pos_cq_value__exact=0, then=Value(neg)),
                default=Value(nr), output_field=CharField()
            )).annotate(pcrreplicate_batch=F('id')).values(
            'extraction_batch__id', 'extraction_batch__analysis_batch', 'extraction_batch__analysis_batch__name',
            'extraction_batch__extraction_number', 'replicate_number', 'target__name', 'pcrreplicate_batch', 'result',
            'pcr_pos_cq_value').order_by('extraction_batch__analysis_batch', 'extraction_batch__id')
        if sample_ids:
            pcr_poss = pcr_poss.filter(pcrreplicates__sample_extraction__sample__in=sample_ids)
        if target_ids:
            pcr_poss = pcr_poss.filter(target__in=target_ids)
        pcr_pos_results = {}
        for pcr_pos in pcr_poss:
            # if the EB is already included in our local dict, just append the current target to it
            if pcr_pos_results.get(pcr_pos['extraction_batch__id'], None) is not None:
                data = pcr_pos_results[pcr_pos['extraction_batch__id']]
                if pcr_pos['result'] == 'pcr_pos_cq_value':
                    pcr_pos['result'] = pcr_pos['pcr_pos_cq_value']
                data[pcr_pos['target__name']] = pcr_pos['result']
            # otherwise, add the EB to our local dict and append the current target to it
            else:
                if pcr_pos['result'] == 'pcr_pos_cq_value':
                    pcr_pos['result'] = pcr_pos['pcr_pos_cq_value']
                data = {
                    "analysis_batch_string": pcr_pos['extraction_batch__analysis_batch__name'],
                    "analysis_batch": pcr_pos['extraction_batch__analysis_batch'],
                    "extraction_number": pcr_pos['extraction_batch__extraction_number'],
                    # "replicate_number": pcr_pos['replicate_number'],
                    "pcrreplicate_batch": pcr_pos['pcrreplicate_batch'],
                    pcr_pos['target__name']: pcr_pos['result']
                }
            pcr_pos_results[pcr_pos['extraction_batch__id']] = data
        # convert the dict of dicts into a list of dicts
        pcr_pos_results_list = list(pcr_pos_results.values())
        pcr_pos_results_list_ordered = []
        # include targets not analyzed
        for pcr_pos_result in pcr_pos_results_list:
            for target in targets:
                if target['name'] not in pcr_pos_result:
                    pcr_pos_result[target['name']] = na
            pcr_pos_result_ids = OrderedDict({
                "analysis_batch": pcr_pos_result.pop('analysis_batch'),
                "analysis_batch_string": pcr_pos_result.pop('analysis_batch_string'),
                "extraction_number": pcr_pos_result.pop('extraction_number'),
                "pcrreplicate_batch": pcr_pos_result.pop('pcrreplicate_batch')
            })
            pcr_pos_result_targets = OrderedDict(sorted(pcr_pos_result.items()))
            pcr_pos_results_list_ordered.append(OrderedDict(**pcr_pos_result_ids, **pcr_pos_result_targets))

        # ExtractionBatch-level controls
        # Ext Pos
        ext_poss = PCRReplicateBatch.objects.filter(
            extraction_batch__reversetranscriptions__re_rt__isnull=True
        ).annotate(
            ext_pos_rna_rt_cq_value=F('extraction_batch__reversetranscriptions__ext_pos_rna_rt_cq_value')
        ).annotate(
            result=Case(
                When(Q(ext_pos_rna_rt_cq_value__gt=0) & Q(target__nucleic_acid_type__name__exact='RNA'),
                     then=Value('ext_pos_rna_rt_cq_value')),
                When(Q(extraction_batch__ext_pos_dna_cq_value__gt=0) & Q(target__nucleic_acid_type__name__exact='DNA'),
                     then=Value('ext_pos_dna_cq_value')),
                When(extraction_batch__ext_pos_dna_cq_value__exact=0, then=Value(neg)),
                default=Value(nr), output_field=CharField()
            )).annotate(pcrreplicate_batch=F('id')).values(
            'extraction_batch__id', 'extraction_batch__analysis_batch', 'extraction_batch__analysis_batch__name',
            'extraction_batch__extraction_number', 'replicate_number', 'target__name', 'pcrreplicate_batch', 'result',
            'ext_pos_rna_rt_cq_value', 'extraction_batch__ext_pos_dna_cq_value'
        ).order_by('extraction_batch__analysis_batch', 'extraction_batch__id')
        if sample_ids:
            ext_poss = ext_poss.filter(pcrreplicates__sample_extraction__sample__in=sample_ids)
        if target_ids:
            ext_poss = ext_poss.filter(target__in=target_ids)
        ext_pos_results = {}
        for ext_pos in ext_poss:
            # if the EB is already included in our local dict, just append the current target to it
            if ext_pos_results.get(ext_pos['extraction_batch__id'], None) is not None:
                data = ext_pos_results[ext_pos['extraction_batch__id']]
                if ext_pos['result'] == 'ext_pos_rna_rt_cq_value':
                    ext_pos['result'] = ext_pos['ext_pos_rna_rt_cq_value']
                elif ext_pos['result'] == 'ext_pos_dna_cq_value':
                    ext_pos['result'] = ext_pos['extraction_batch__ext_pos_dna_cq_value']
                data[ext_pos['target__name']] = ext_pos['result']
            # otherwise, add the EB to our local dict and append the current target to it
            else:
                if ext_pos['result'] == 'ext_pos_rna_rt_cq_value':
                    ext_pos['result'] = ext_pos['ext_pos_rna_rt_cq_value']
                elif ext_pos['result'] == 'ext_pos_dna_cq_value':
                    ext_pos['result'] = ext_pos['extraction_batch__ext_pos_dna_cq_value']
                data = {
                    "analysis_batch_string": ext_pos['extraction_batch__analysis_batch__name'],
                    "analysis_batch": ext_pos['extraction_batch__analysis_batch'],
                    "extraction_number": ext_pos['extraction_batch__extraction_number'],
                    "pcrreplicate_batch": ext_pos['pcrreplicate_batch'],
                    # "replicate_number": ext_pos['replicate_number'],
                    ext_pos['target__name']: ext_pos['result']
                }
            ext_pos_results[ext_pos['extraction_batch__id']] = data
        # convert the dict of dicts into a list of dicts
        ext_pos_results_list = list(ext_pos_results.values())
        ext_pos_results_list_ordered = []
        # include targets not analyzed
        for ext_pos_result in ext_pos_results_list:
            for target in targets:
                if target['name'] not in ext_pos_result:
                    ext_pos_result[target['name']] = na
            ext_pos_result_ids = OrderedDict({
                "analysis_batch": ext_pos_result.pop('analysis_batch'),
                "analysis_batch_string": ext_pos_result.pop('analysis_batch_string'),
                "extraction_number": ext_pos_result.pop('extraction_number'),
                "pcrreplicate_batch": ext_pos_result.pop('pcrreplicate_batch')
            })
            ext_pos_result_targets = OrderedDict(sorted(ext_pos_result.items()))
            ext_pos_results_list_ordered.append(OrderedDict(**ext_pos_result_ids, **ext_pos_result_targets))

        # Sample-level controls
        # PegNegs
        # peg_negs = Sample.objects.filter(record_type=2)
        peg_neg_ids = list(set(Sample.objects.filter(id__in=sample_ids).values_list('peg_neg', flat=True)))
        peg_negs = Sample.objects.filter(id__in=peg_neg_ids).order_by('id')
        peg_neg_results_list = []
        for peg_neg in peg_negs:
            peg_neg_resp = {"id": peg_neg.id, "collaborator_sample_id": peg_neg.collaborator_sample_id,
                            "collection_start_date": peg_neg.collection_start_date}
            for target in targets:
                # only check for valid reps with the same target
                reps = PCRReplicate.objects.filter(
                    sample_extraction__sample_id=peg_neg.id,
                    pcrreplicate_batch__target_id__exact=target['id'], invalid=False)
                # if there are no reps, then this target was not analyzed
                if len(reps) == 0:
                    result = na
                else:
                    # if even a single one of the peg_neg reps is greater than zero,
                    # the data rep result must be set to positive
                    pos_result = [r.cq_value for r in reps if r.cq_value is not None and r.cq_value > Decimal('0')]
                    if pos_result:
                        result = pos
                    else:
                        neg_result = [r.cq_value for r in reps if r.cq_value is not None and r.cq_value == Decimal('0')]
                        result = neg if neg_result else nr
                peg_neg_resp[target['name']] = result
            peg_neg_results_list.append(peg_neg_resp)

        resp = {
            "ext_neg": ext_neg_results_list_ordered,
            "pcr_neg": pcr_neg_results_list_ordered,
            "pcr_pos": pcr_pos_results_list_ordered,
            "ext_pos": ext_pos_results_list_ordered,
            "peg_neg": peg_neg_results_list,
            "targets": target_names
        }

        return Response(resp)
