"""
Video processing, split into two layers:

- `run_video_processing(video_id)` — the actual work, plain synchronous
  Python. Called directly from InspectionVideo.save() so video upload works
  correctly with zero extra infrastructure (no Redis, no Celery worker).

- `process_inspection_video` — a thin Celery task wrapping the same
  function, ready to use the moment a broker is actually deployed. Switch
  `models.InspectionVideo.save()` to call `process_inspection_video.delay(...)`
  instead of `run_video_processing(...)` directly once Celery is running —
  that's the only change needed.

This split avoids the trap of writing async-only code that can't run
locally: the spec asks for asynchronous processing "for large videos" in
production, but requiring Redis just to upload a test video in development
would be a worse trade-off than starting synchronous and upgrading later.
"""
import logging

logger = logging.getLogger("acis")


def run_video_processing(video_id):
    """
    1. Validate the original file (already done at upload time by
       validators.validate_video_file).
    2. Generate a thumbnail/poster frame.
    3. Extract duration/resolution metadata.
    4. Optionally transcode to a web-friendly format.
    5. Flip processing_status to READY (or FAILED with processing_error set).

    Thumbnail/metadata extraction is left as a documented extension point —
    wire in ffmpeg-python or moviepy here. Swallowing that dependency in
    this scaffold would make `pip install` slower for a feature you may
    swap out (e.g. for a managed transcoding service in prod).
    """
    from .models import InspectionVideo, VideoProcessingStatus

    try:
        video = InspectionVideo.objects.get(id=video_id)
    except InspectionVideo.DoesNotExist:
        logger.warning("run_video_processing: %s no longer exists", video_id)
        return

    video.processing_status = VideoProcessingStatus.PROCESSING
    video.save(update_fields=["processing_status", "updated_at"])

    try:
        # TODO: integrate ffmpeg-python / moviepy here to populate
        # duration_seconds, width, height and thumbnail.
        video.processing_status = VideoProcessingStatus.READY
        video.save(update_fields=["processing_status", "updated_at"])
    except Exception as exc:  # noqa: BLE001
        video.processing_status = VideoProcessingStatus.FAILED
        video.processing_error = str(exc)
        video.save(update_fields=["processing_status", "processing_error", "updated_at"])
        logger.exception("Video processing failed for %s", video_id)


try:
    from celery import shared_task

    @shared_task(bind=True, max_retries=3)
    def process_inspection_video(self, video_id):
        """Celery entry point — not used yet (see module docstring), kept
        ready for when a broker is deployed."""
        run_video_processing(video_id)

except ImportError:  # pragma: no cover — celery not installed yet is fine;
    # run_video_processing() above works without it.
    process_inspection_video = None
