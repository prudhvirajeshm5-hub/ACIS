from django.db import transaction

from apps.audit.utils import log_action
from apps.mis.models import MISQCStage

from .models import QCDecision, QCReview

DECISION_TO_MIS_QC_STAGE = {
    QCDecision.RECOMMENDED: MISQCStage.APPROVED,
    QCDecision.NOT_RECOMMENDED: MISQCStage.REJECTED,
    QCDecision.NEED_CORRECTION: MISQCStage.CORRECTION,
    QCDecision.REINSPECTION_REQUIRED: MISQCStage.CORRECTION,
}


@transaction.atomic
def record_qc_decision(*, inspection, qc_executive, decision, remarks):
    previous = inspection.qc_reviews.first()  # ordering = -reviewed_at
    review = QCReview.objects.create(
        inspection=inspection, qc_executive=qc_executive, decision=decision,
        remarks=remarks, supersedes=previous,
    )

    mis = inspection.mis
    mis.qc_stage = DECISION_TO_MIS_QC_STAGE[decision]
    mis.save(update_fields=["qc_stage", "updated_at"])

    if decision in (QCDecision.NEED_CORRECTION, QCDecision.REINSPECTION_REQUIRED):
        inspection.is_submitted = False
        inspection.save(update_fields=["is_submitted", "updated_at"])

    log_action(action="approve" if decision == QCDecision.RECOMMENDED else "reject", module="qc", obj=review)
    return review
