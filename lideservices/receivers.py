from django.dispatch import receiver
from django.db.models.signals import post_save
from lideservices.models import *

# listen for updated pcrreplicate instances
@receiver(post_save, sender=PCRReplicate)
def pcrreplicate_post_save(sender, **kwargs):
    instance = kwargs['instance']

    # if there is a gc_reaction value, calculate the replicate_concentration and set the concentration_unit
    if instance.gc_reaction is not None:
        # calculate their replicate_concentration
        instance.calc_rep_conc()
        instance.save()

    # assess the invalid flags
    # invalid flags default to True (i.e., the rep is invalid) and can only be set to False if:
    #     1. all parent controls exist
    #     2. all parent control flags are False (i.e., the controls are valid)
    #     3. the cq_value and gc_reaction of this rep are greater than or equal to zero
    if instance.invalid_override is None:
        if (
                not instance.pcrreplicate_batch.ext_neg_invalid and
                not instance.pcrreplicate_batch.rt_neg_invalid and
                not instance.pcr_neg_invalid.pcr_neg_flag and
                instance.cq_value >= 0 and
                instance.gc_reaction >= 0
        ):
            instance.invalid = False
        else:
            instance.invalid = True

    # determine if all replicates for a given sample-target combo are now in the database or not
    # and calculate sample mean concentration if yes or set to null if no
    pcrrepbatch = PCRReplicateBatch.objects.get(id=instance.pcrreplicate_batch.id)
    fsmc = FinalSampleMeanConcentration.objects.filter(
        sample=instance.extraction.sample, target=pcrrepbatch.target).first()
    # if the sample-target combo (fsmc) does not exist, create it
    if not fsmc:
        fsmc = FinalSampleMeanConcentration.objects.create(
            sample=instance.extraction.sample, target=pcrrepbatch.target)
    # if all the valid related reps have gc_reaction values, calculate sample mean concentration
    if fsmc.all_sample_target_reps_uploaded():
        fsmc.calc_sample_mean_conc()
    # otherwise not all valid related reps have gc_reacion values, so set sample mean concentration to null
    else:
        fsmc.update(sample_mean_concentration=None)


# listen for updated extraction batch instances
@receiver(post_save, sender=ExtractionBatch)
def extractionbatch_post_save(sender, **kwargs):
    instance = kwargs['instance']

    # if the invalid is true, invalidate all child replicates
    if instance.ext_pos_invalid:
        for extraction in instance.extractions:
            for pcrreplicate in extraction.pcrreplicates:
                pcrreplicate.update(invalid=True)

                # determine if all replicates for a given sample-target combo are now in the database or not
                # and calculate sample mean concentration if yes or set to null if no
                pcrrepbatch = PCRReplicateBatch.objects.get(id=pcrreplicate.pcrreplicate_batch)
                fsmc = FinalSampleMeanConcentration.objects.filter(
                    sample=extraction.sample, target=pcrrepbatch.target).first()
                # if the sample-target combo (fsmc) does not exist, create it
                if not fsmc:
                    fsmc = FinalSampleMeanConcentration.objects.create(
                        sample=extraction.sample, target=pcrrepbatch.target)
                # if all the valid related reps have gc_reaction values, calculate sample mean concentration
                if fsmc.all_sample_target_reps_uploaded():
                    fsmc.calc_sample_mean_conc()
                # otherwise not all valid related reps have gc_reacion values, so set sample mean concentration to null
                else:
                    fsmc.update(sample_mean_concentration=None)


# listen for updated reverse transcription instances
@receiver(post_save, sender=ReverseTranscription)
def reversetranscription_post_save(sender, **kwargs):
    instance = kwargs['instance']

    # if the invalid is true, invalidate all child replicates
    if instance.rt_pos_invalid:
        extraction_batch = ExtractionBatch.objects.get(id=instance.extraction_batch)
        for extraction in extraction_batch.extractions:
            for pcrreplicate in extraction.pcrreplicates:
                pcrreplicate.update(invalid=True)

                # determine if all replicates for a given sample-target combo are now in the database or not
                # and calculate sample mean concentration if yes or set to null if no
                pcrrepbatch = PCRReplicateBatch.objects.get(id=pcrreplicate.pcrreplicate_batch)
                fsmc = FinalSampleMeanConcentration.objects.filter(
                    sample=extraction.sample, target=pcrrepbatch.target).first()
                # if the sample-target combo (fsmc) does not exist, create it
                if not fsmc:
                    fsmc = FinalSampleMeanConcentration.objects.create(
                        sample=extraction.sample, target=pcrrepbatch.target)
                # if all the valid related reps have gc_reaction values, calculate sample mean concentration
                if fsmc.all_sample_target_reps_uploaded():
                    fsmc.calc_sample_mean_conc()
                # otherwise not all valid related reps have gc_reacion values, so set sample mean concentration to null
                else:
                    fsmc.update(sample_mean_concentration=None)
