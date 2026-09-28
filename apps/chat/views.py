import mimetypes
import re

from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.db import transaction
from django.http import Http404, HttpResponse, JsonResponse, StreamingHttpResponse
from django.shortcuts import get_object_or_404, render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_POST

from .models import Conversation, ConversationKind, Membership, Message
from .services import classify_upload, ensure_everyone, person_name, unread_total


def _member_or_404(user, pk):
    m = Membership.objects.select_related("conversation").filter(conversation_id=pk, user=user).first()
    if m is None:
        raise Http404
    return m


def _iso(dt):
    return timezone.localtime(dt).isoformat()


def _title(conv, user):
    if conv.kind == ConversationKind.DIRECT:
        other = conv.memberships.exclude(user=user).select_related("user").first()
        return person_name(other.user) if other else "Chat"
    return conv.name or "Group"


def _subtitle(conv, user):
    if conv.kind == ConversationKind.DIRECT:
        other = conv.memberships.exclude(user=user).select_related("user").first()
        return other.user.role_label if other else ""
    if conv.kind == ConversationKind.EVERYONE:
        return "All employees"
    return f"{conv.memberships.count()} members"


def _message_json(m, user):
    return {
        "id": m.id, "mine": m.sender_id == user.pk, "sender": person_name(m.sender),
        "text": m.text, "kind": m.attachment_kind,
        "url": reverse("chat:media", args=[m.id]) if m.attachment_kind else "",
        "file_name": m.attachment_name, "created_at": _iso(m.created_at),
    }


def _preview(m, user):
    if m is None:
        return ""
    who = "You" if m.sender_id == user.pk else person_name(m.sender)
    body = m.text or {"image": "Photo", "video": "Video"}.get(m.attachment_kind, "")
    return f"{who}: {body}"[:70]


@login_required
def chat_home(request):
    ensure_everyone(request.user)
    User = get_user_model()
    people = [
        {"id": u.pk, "name": person_name(u), "role": u.role_label}
        for u in User.objects.filter(is_active=True).exclude(pk=request.user.pk).order_by("first_name", "username")
    ]
    return render(request, "chat/chat.html", {"people": people})


@login_required
def conversations(request):
    ensure_everyone(request.user)
    rows = []
    for m in Membership.objects.filter(user=request.user).select_related("conversation"):
        c = m.conversation
        last = c.messages.select_related("sender").order_by("-id").first()
        if c.kind == ConversationKind.DIRECT and last is None:
            continue
        unread = c.messages.filter(id__gt=m.last_read_id).exclude(sender=request.user).count()
        when = last.created_at if last else c.created_at
        rows.append((when, {
            "id": str(c.id), "kind": c.kind, "title": _title(c, request.user),
            "preview": _preview(last, request.user), "time": _iso(when), "unread": unread,
        }))
    rows.sort(key=lambda r: r[0], reverse=True)
    return JsonResponse({"conversations": [r[1] for r in rows]})


@login_required
def messages(request, pk):
    m = _member_or_404(request.user, pk)
    conv = m.conversation
    try:
        after = int(request.GET.get("after") or 0)
    except ValueError:
        after = 0
    qs = conv.messages.select_related("sender")
    if after:
        items = list(qs.filter(id__gt=after).order_by("id")[:200])
    else:
        items = list(reversed(list(qs.order_by("-id")[:50])))
    if items:
        latest = items[-1].id
        Membership.objects.filter(pk=m.pk, last_read_id__lt=latest).update(last_read_id=latest)
    return JsonResponse({
        "conversation": {"id": str(conv.id), "kind": conv.kind, "title": _title(conv, request.user), "subtitle": _subtitle(conv, request.user)},
        "messages": [_message_json(x, request.user) for x in items],
    })


@login_required
@require_POST
def send(request, pk):
    mem = _member_or_404(request.user, pk)
    text = request.POST.get("text", "").strip()[:4000]
    upload = request.FILES.get("file")
    if not text and not upload:
        return JsonResponse({"error": "Nothing to send."}, status=400)
    msg = Message(conversation=mem.conversation, sender=request.user, text=text)
    if upload:
        try:
            kind, mime = classify_upload(upload)
        except ValidationError as e:
            return JsonResponse({"error": e.messages[0]}, status=400)
        msg.attachment = upload
        msg.attachment_kind = kind
        msg.attachment_mime = mime
        msg.attachment_name = upload.name[:255]
    msg.save()
    Membership.objects.filter(pk=mem.pk).update(last_read_id=msg.id)
    return JsonResponse({"message": _message_json(msg, request.user)})


@login_required
@require_POST
def start_direct(request, user_id):
    other = get_object_or_404(get_user_model().objects.filter(is_active=True), pk=user_id)
    if other.pk == request.user.pk:
        return JsonResponse({"error": "You cannot chat with yourself."}, status=400)
    key = "-".join(sorted([str(request.user.pk), str(other.pk)], key=int))
    with transaction.atomic():
        conv, created = Conversation.objects.get_or_create(direct_key=key, defaults={"kind": ConversationKind.DIRECT})
        for u in (request.user, other):
            Membership.objects.get_or_create(conversation=conv, user=u)
    return JsonResponse({"id": str(conv.id)})


@login_required
@require_POST
def create_group(request):
    name = request.POST.get("name", "").strip()[:100]
    ids = [i for i in request.POST.getlist("members") if i.isdigit()]
    users = list(get_user_model().objects.filter(is_active=True, pk__in=ids).exclude(pk=request.user.pk))
    if not name:
        return JsonResponse({"error": "Please enter a group name."}, status=400)
    if not users:
        return JsonResponse({"error": "Pick at least one member."}, status=400)
    with transaction.atomic():
        conv = Conversation.objects.create(kind=ConversationKind.GROUP, name=name, created_by=request.user)
        Membership.objects.bulk_create([Membership(conversation=conv, user=u) for u in users + [request.user]])
    return JsonResponse({"id": str(conv.id)})


@login_required
def unread(request):
    return JsonResponse({"count": unread_total(request.user)})


def _iter_file(fh, start, length, chunk=64 * 1024):
    try:
        fh.seek(start)
        remaining = length
        while remaining > 0:
            data = fh.read(min(chunk, remaining))
            if not data:
                break
            remaining -= len(data)
            yield data
    finally:
        fh.close()


@login_required
def media(request, pk):
    msg = get_object_or_404(Message, pk=pk)
    _member_or_404(request.user, msg.conversation_id)
    if not msg.attachment:
        raise Http404
    size = msg.attachment.size
    ctype = msg.attachment_mime or mimetypes.guess_type(msg.attachment_name)[0] or "application/octet-stream"
    start, end, status = 0, size - 1, 200
    rng = request.headers.get("Range", "")
    m = re.match(r"bytes=(\d*)-(\d*)$", rng)
    if m and (m.group(1) or m.group(2)):
        if m.group(1):
            start = int(m.group(1))
            end = int(m.group(2)) if m.group(2) else size - 1
        else:
            start = max(size - int(m.group(2)), 0)
        end = min(end, size - 1)
        if start > end or start >= size:
            resp = HttpResponse(status=416)
            resp["Content-Range"] = f"bytes */{size}"
            return resp
        status = 206
    length = end - start + 1
    resp = StreamingHttpResponse(_iter_file(msg.attachment.open("rb"), start, length), status=status, content_type=ctype)
    resp["Content-Length"] = str(length)
    resp["Accept-Ranges"] = "bytes"
    resp["Cache-Control"] = "private, max-age=3600"
    resp["X-Content-Type-Options"] = "nosniff"
    if status == 206:
        resp["Content-Range"] = f"bytes {start}-{end}/{size}"
    return resp
