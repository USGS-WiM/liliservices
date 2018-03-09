from django.dispatch import receiver
from django.db.models.signals import post_save
from lideservices.models import *

# listen for updated pcrreplicate instances
@receiver(post_save, sender=PCRReplicate)
def pcrreplicate_post_save(sender, **kwargs):
    instance = kwargs['instance']

    # if there is a gc_reaction value and set the concentration_unit
    if instance.gc_reaction is not None:
        # calculate their replicate_concentration
        instance.calc_rep_conc()

        # set the concentration_unit
        instance.concentration_unit = instance.get_conc_unit(instance.extraction.sample.id)

        instance.save()

    # determine if all replicates for a given sample-target combo are now in the database or not
    # and calculate sample mean concentration if yes or set to null if no
    pcrrepbatch = PCRReplicateBatch.objects.get(id=instance.pcrreplicate_batch.id)
    result = Result.objects.filter(sample=instance.extraction.sample, target=pcrrepbatch.target).first()
    # if the sample-target combo (result) does not exist, create it
    if not result:
        result = Result.objects.create(sample=instance.extraction.sample, target=pcrrepbatch.target)
    # if all the valid related reps have gc_reaction values, calculate sample mean concentration
    if result.all_sample_target_reps_uploaded():
        result.calc_sample_mean_conc()
    # otherwise not all valid related reps have gc_reacion values, so set sample mean concentration to null
    else:
        result.update(sample_mean_concentration=None)


# listen for updated extraction batch instances
@receiver(post_save, sender=ExtractionBatch)
def extractionbatch_post_save(sender, **kwargs):
    instance = kwargs['instance']

    # if the bad_result_flag is true, invalidate all child replicates
    if instance.ext_pos_bad_result_flag:
        for extraction in instance.extractions:
            for pcrreplicate in extraction.pcrreplicates:
                pcrreplicate.update(bad_result_flag=True)

                # determine if all replicates for a given sample-target combo are now in the database or not
                # and calculate sample mean concentration if yes or set to null if no
                pcrrepbatch = PCRReplicateBatch.objects.get(id=pcrreplicate.pcrreplicate_batch)
                result = Result.objects.filter(sample=extraction.sample, target=pcrrepbatch.target).first()
                # if the sample-target combo (result) does not exist, create it
                if not result:
                    result = Result.objects.create(sample=extraction.sample, target=pcrrepbatch.target)
                # if all the valid related reps have gc_reaction values, calculate sample mean concentration
                if result.all_sample_target_reps_uploaded():
                    result.calc_sample_mean_conc()
                # otherwise not all valid related reps have gc_reacion values, so set sample mean concentration to null
                else:
                    result.update(sample_mean_concentration=None)


# listen for updated reverse transcription instances
@receiver(post_save, sender=ReverseTranscription)
def reversetranscription_post_save(sender, **kwargs):
    instance = kwargs['instance']

    # if the bad_result_flag is true, invalidate all child replicates
    if instance.rt_pos_bad_result_flag:
        extraction_batch = ExtractionBatch.objects.get(id=instance.extraction_batch)
        for extraction in extraction_batch.extractions:
            for pcrreplicate in extraction.pcrreplicates:
                pcrreplicate.update(bad_result_flag=True)

                # determine if all replicates for a given sample-target combo are now in the database or not
                # and calculate sample mean concentration if yes or set to null if no
                pcrrepbatch = PCRReplicateBatch.objects.get(id=pcrreplicate.pcrreplicate_batch)
                result = Result.objects.filter(sample=extraction.sample, target=pcrrepbatch.target).first()
                # if the sample-target combo (result) does not exist, create it
                if not result:
                    result = Result.objects.create(sample=extraction.sample, target=pcrrepbatch.target)
                # if all the valid related reps have gc_reaction values, calculate sample mean concentration
                if result.all_sample_target_reps_uploaded():
                    result.calc_sample_mean_conc()
                # otherwise not all valid related reps have gc_reacion values, so set sample mean concentration to null
                else:
                    result.update(sample_mean_concentration=None)