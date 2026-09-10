from .models import Notification, NotificationChannel


def notify(*, recipient, title, body="", link="", channel=NotificationChannel.IN_APP):
    """
    Single entry point for every notification-worthy event in the spec
    (new assignment, inspection overdue, QC pending, etc). Callers never
    need to know which channels are actually wired up yet.
    """
    return Notification.objects.create(recipient=recipient, channel=channel, title=title, body=body, link=link)
