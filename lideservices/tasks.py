import json
from collections import Counter, OrderedDict
from django.db.models import Q, Case, When, Value, Count, Sum, Min, Max, Avg, FloatField, CharField
from django.db.models.functions import Cast
from django.core.files.base import ContentFile
from lideservices.aggregates import Median
from lideservices.serializers import *
from lideservices.models import *
from celery import shared_task


LIST_DELIMETER = settings.LIST_DELIMETER


class DecimalEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Decimal):
            return float(obj)
        return json.JSONEncoder.default(self, obj)


@shared_task(name="generate_inhibition_report_task")
def generate_inhibition_report(sample, report_file_id, username):
    report_file = ReportFile.objects.filter(id=report_file_id).first()

    try:
        queryset = SampleExtraction.objects.all()
        if sample is not None:
            if LIST_DELIMETER in sample:
                sample_list = sample.split(',')
                queryset = queryset.filter(sample__in=sample_list)
            else:
                queryset = queryset.filter(sample__exact=sample)

        data = SampleExtractionReportSerializer(queryset, many=True).data
        datetimenow = datetime.today().strftime('%Y-%m-%d_%H:%M:%S')
        new_file_name = "InhibitionReport_" + username + "_" + datetimenow + ".json"
        new_file_content = ContentFile(json.dumps(data, cls=DecimalEncoder))

        report_file.file.save(new_file_name, new_file_content)
        report_file.status = Status.objects.filter(id=2).first()
        report_file.save()
        return "generate_inhibition_report completed and created file {0}".format(new_file_name)

    except Exception as exc:
        message = "generate_inhibition_report failed and no file was created, error message: {0}".format(exc)
        report_file.status = Status.objects.filter(id=3).first()
        report_file.fail_reason = message
        report_file.save()
        return message


@shared_task(name="results_summary_report_task")
def generate_results_summary_report(sample, target, statistic, report_file_id, username):
    report_file = ReportFile.objects.filter(id=report_file_id).first()

    try:
        STATISTICS = ['sample_count', 'positive_count', 'percent_positive', 'max_concentration', 'min_concentration',
                      'median_concentration', 'average_concentration', 'min_concentration_positive',
                      'median_concentration_positive', 'average_concentration_positive']

        queryset = FinalSampleMeanConcentration.objects.all()
        # filter by sample IDs, exact list
        if sample is not None:
            if LIST_DELIMETER in sample:
                sample_list = sample.split(LIST_DELIMETER)
                queryset = queryset.filter(sample__in=sample_list)
            else:
                queryset = queryset.filter(sample__exact=sample)
        # filter by target IDs, exact list
        if target is not None:
            if LIST_DELIMETER in target:
                target_list = target.split(LIST_DELIMETER)
                queryset = queryset.filter(target__in=target_list)
            else:
                queryset = queryset.filter(target__exact=target)
        # get the requested statistics, exact list
        statistic_list = statistic.split(LIST_DELIMETER) if statistic is not None else STATISTICS

        # set aside a parallel query for totals
        totals_queryset = queryset
        total_sample_count = totals_queryset.aggregate(Count('sample_id', distinct=True))['sample_id__count']

        # recalc reps validity
        for fsmc in queryset:
            recalc_reps('FinalSampleMeanConcentration', fsmc.sample.id, target=fsmc.target.id, recalc_rep_conc=False)

        # get binary count of all positive samples if necessary
        total_pos_count = None
        if ('positive_count' in statistic_list
                or ('percent_positive' in statistic_list and 'positive_count' not in statistic_list)):
            total_pos_count = queryset.values(
                'sample').annotate(conc=Sum('final_sample_mean_concentration')).filter(conc__gt=0).count()

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
            totals['sample_count'] = total_sample_count
        if ('positive_count' in statistic_list
                or ('percent_positive' in statistic_list and 'positive_count' not in statistic_list)):
            # include the positive_count by target
            queryset = queryset.annotate(positive_count=Count('id', filter=Q(final_sample_mean_concentration__gt=0)))
            # include the positive_count for all targets
            totals['positive_count'] = total_pos_count
        if 'percent_positive' in statistic_list:
            # include the percent_positive by target
            queryset = queryset.annotate(
                percent_positive=(Cast('positive_count', FloatField()) / Cast('sample_count', FloatField()) * 100))
            # include the percent_positive for all targets
            totals['percent_positive'] = (total_pos_count / total_sample_count) * 100 if total_pos_count else 0
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

        data = list(queryset)
        data.append(totals)

        datetimenow = datetime.today().strftime('%Y-%m-%d_%H:%M:%S')
        new_file_name = "ResultsSummaryReport_" + username + "_" + datetimenow + ".json"
        new_file_content = ContentFile(json.dumps(data, cls=DecimalEncoder))

        report_file.file.save(new_file_name, new_file_content)
        report_file.status = Status.objects.filter(id=2).first()
        report_file.save()
        return "results_summary_report completed and created file {0}".format(new_file_name)

    except Exception as exc:
        message = "results_summary_report failed and no file was created, error message: {0}".format(exc)
        report_file.status = Status.objects.filter(id=3).first()
        report_file.fail_reason = message
        report_file.save()
        return message


@shared_task(name="individual_sample_report_task")
def generate_individual_sample_report(sample, target, report_file_id, username):
    report_file = ReportFile.objects.filter(id=report_file_id).first()

    try:
        queryset = FinalSampleMeanConcentration.objects.all()
        # filter by sample IDs, exact list
        if sample is not None:
            sample_list = sample.split(',')
            queryset = queryset.filter(sample__in=sample_list)
        # filter by target IDs, exact list
        if target is not None:
            target_list = target.split(',')
            queryset = queryset.filter(target__in=target_list)
        # recalc reps validity
        for fsmc in queryset:
            recalc_reps('FinalSampleMeanConcentration', fsmc.sample.id, target=fsmc.target.id,
                        recalc_rep_conc=False)

        data = FinalSampleMeanConcentrationResultsSerializer(queryset, many=True).data
        datetimenow = datetime.today().strftime('%Y-%m-%d_%H:%M:%S')
        new_file_name = "IndividualSampleReport_" + username + "_" + datetimenow + ".json"
        new_file_content = ContentFile(json.dumps(data, cls=DecimalEncoder))

        report_file.file.save(new_file_name, new_file_content)
        report_file.status = Status.objects.filter(id=2).first()
        report_file.save()
        return "individual_sample_report_task completed and created file {0}".format(new_file_name)

    except Exception as exc:
        message = "individual_sample_report_task failed and no file was created, error message: {0}".format(exc)
        report_file.status = Status.objects.filter(id=3).first()
        report_file.fail_reason = message
        report_file.save()
        return message


@shared_task(name="quality_control_report_task")
def generate_quality_control_report(samples, report_file_id, username):
    report_file = ReportFile.objects.filter(id=report_file_id).first()

    try:
        data = {}

        queryset = Sample.objects.all()
        if samples is not None:
            queryset = queryset.filter(id__in=samples)

        # recalc reps validity
        for sample in queryset:
            recalc_reps('Sample', sample.id, recalc_rep_conc=False)

        matrix_counts = queryset.values('matrix__name').order_by().annotate(count=Count('matrix'))
        sample_type_counts = queryset.values('sample_type__name').order_by().annotate(count=Count('sample_type'))
        meter_reading_unit_counts = queryset.values(
            'meter_reading_unit__name').order_by().annotate(
            count=Count('meter_reading_unit'))
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
        for unit in meter_reading_unit_counts:
            sample_stats.append({
                "metric": "Meter Reading Unit",
                "value": unit['meter_reading_unit__name'],
                "count": unit['count'],
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
        data['sample_quality_control'] = sample_stats

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
        data['extraction_raw_data'] = list(eb_raw_data)

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
        data['extraction_quality_control'] = extraction_stats

        datetimenow = datetime.today().strftime('%Y-%m-%d_%H:%M:%S')
        new_file_name = "QualityControlReport_" + username + "_" + datetimenow + ".json"
        new_file_content = ContentFile(json.dumps(data, cls=DecimalEncoder))

        report_file.file.save(new_file_name, new_file_content)
        report_file.status = Status.objects.filter(id=2).first()
        report_file.save()
        return "quality_control_report_task completed and created file {0}".format(new_file_name)

    except Exception as exc:
        message = "quality_control_report_task failed and no file was created, error message: {0}".format(exc)
        report_file.status = Status.objects.filter(id=3).first()
        report_file.fail_reason = message
        report_file.save()
        return message


@shared_task(name="control_results_report_task")
def generate_control_results_report(sample_ids, target_ids, report_file_id, username):
    report_file = ReportFile.objects.filter(id=report_file_id).first()

    try:
        targets = Target.objects.all().values('id', 'name').order_by('name')
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

        data = {
            "ext_neg": ext_neg_results_list_ordered,
            "pcr_neg": pcr_neg_results_list_ordered,
            "pcr_pos": pcr_pos_results_list_ordered,
            "ext_pos": ext_pos_results_list_ordered,
            "peg_neg": peg_neg_results_list,
            "targets": target_names
        }

        datetimenow = datetime.today().strftime('%Y-%m-%d_%H:%M:%S')
        new_file_name = "ControlResultsReport_" + username + "_" + datetimenow + ".json"
        new_file_content = ContentFile(json.dumps(data, cls=DecimalEncoder, default=str))

        report_file.file.save(new_file_name, new_file_content)
        report_file.status = Status.objects.filter(id=2).first()
        report_file.save()
        return "control_results_report_task completed and created file {0}".format(new_file_name)

    except Exception as exc:
        message = "control_results_report_task failed and no file was created, error message: {0}".format(exc)
        report_file.status = Status.objects.filter(id=3).first()
        report_file.fail_reason = message
        report_file.save()
        return message
