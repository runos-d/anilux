from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.response import Response

from apps.social.infrastructure.models.social import Report, Post, PostComment




@api_view(["GET"])
@permission_classes([IsAuthenticated, IsAdminUser])
def get_reports(request):
    import logging

    logger = logging.getLogger(__name__)

    try:
        page = int(request.query_params.get("page", 1))
        per_page = int(request.query_params.get("per_page", 20))
        offset = (page - 1) * per_page

        status_filter = request.query_params.get("status")
        content_type_filter = request.query_params.get("content_type")
        reason_filter = request.query_params.get("reason")

        queryset = Report.objects.all().select_related("reporter")

        if status_filter:
            queryset = queryset.filter(status=status_filter)
        if content_type_filter:
            queryset = queryset.filter(content_type=content_type_filter)
        if reason_filter:
            queryset = queryset.filter(reason=reason_filter)

        queryset = queryset.order_by("-created_at")

        total = queryset.count()
        reports_page = list(queryset[offset : offset + per_page])

        from apps.social.presentation.serializers.social_serializers import ReportSerializer
        from apps.notifications.infrastructure.models.notifications import Complaint
        from apps.social.infrastructure.post_media_urls import media_url
        from django.contrib.auth import get_user_model

        reports_data = ReportSerializer(reports_page, many=True, context={"request": request}).data
        snapshots = {
            str(row["source_report_id"]): row["target_snapshot"] or {}
            for row in Complaint.objects.filter(
                source_report_id__in=[report.pk for report in reports_page]
            ).values("source_report_id", "target_snapshot")
        }
        User = get_user_model()

        for report, report_data in zip(reports_page, reports_data):
            snapshot = snapshots.get(str(report.pk), {})
            content = {}
            report_data["reporter"] = {
                "id": report.reporter_id,
                "username": report.reporter.username,
                "nickname": report.reporter.nickname,
                "url": f"/profile/@{report.reporter.nickname}" if report.reporter.nickname else f"/profile/{report.reporter.username}",
            }
            report_data["description"] = report.comment
            if report_data["content_type"] == "post":
                post = Post.objects.select_related("author").prefetch_related("media_files").filter(
                    id=report_data["content_id"]
                ).first()
                if post:
                    available = not post.is_deleted
                    content = {
                        "title": post.title or snapshot.get("title") or "",
                        "text": post.text or snapshot.get("text") or "",
                        "author": {
                            "id": post.author_id,
                            "username": post.author.username,
                            "nickname": post.author.nickname,
                        },
                        "url": f"/post/{post.public_id}" if available else None,
                        "available": available,
                        "media": [
                            {
                                "id": item.pk,
                                "type": item.media_type,
                                "caption": item.caption,
                                "url": media_url(item.file.name, request) if item.file else None,
                            }
                            for item in post.media_files.filter(is_active=True)
                        ],
                    }
            elif report_data["content_type"] == "comment":
                comment = PostComment.objects.select_related("author", "post").filter(
                    id=report_data["content_id"]
                ).first()
                if comment:
                    available = not comment.is_deleted and not comment.post.is_deleted
                    content = {
                        "text": comment.content or snapshot.get("text") or "",
                        "author": {
                            "id": comment.author_id,
                            "username": comment.author.username,
                            "nickname": comment.author.nickname,
                        },
                        "url": f"/post/{comment.post.public_id}" if available else None,
                        "available": available,
                        "media": [],
                    }
            elif report_data["content_type"] == "user":
                target_user = User.objects.filter(id=report_data["content_id"]).first()
                if target_user:
                    content = {
                        "title": target_user.display_name or target_user.username,
                        "text": "",
                        "author": {
                            "id": target_user.pk,
                            "username": target_user.username,
                            "nickname": target_user.nickname,
                        },
                        "url": f"/profile/@{target_user.nickname}" if target_user.nickname else f"/profile/{target_user.username}",
                        "available": target_user.is_active,
                        "media": [],
                    }

            if not content and snapshot:
                content = {
                    "title": snapshot.get("title") or "",
                    "text": snapshot.get("text") or "",
                    "author": {
                        "id": snapshot.get("author_id"),
                        "username": snapshot.get("author_username") or "",
                        "nickname": None,
                    },
                    "url": None,
                    "available": False,
                    "media": [
                        {
                            **item,
                            "url": media_url(item.get("path"), request) if item.get("path") else None,
                        }
                        for item in snapshot.get("media", [])
                    ],
                }

            report_data["content_preview"] = content or None

        return Response(
            {
                "results": reports_data,
                "count": total,
                "page": page,
                "per_page": per_page,
                "total_pages": (total + per_page - 1) // per_page,
            }
        )
    except Exception as e:
        logger.error(f"Error in get_reports: {e}", exc_info=True)
        return Response({"error": "Ошибка при загрузке жалоб", "detail": str(e)}, status=500)


@api_view(["POST"])
@permission_classes([IsAuthenticated, IsAdminUser])
def resolve_report(request, report_id):
    import logging

    logger = logging.getLogger(__name__)

    try:
        report = get_object_or_404(Report, id=report_id)

        if report.status != "pending":
            return Response(
                {"error": "Жалоба уже рассмотрена"}, status=400
            )

        status = request.data.get("status")
        if status not in ["resolved", "rejected"]:
            return Response(
                {"error": "Недопустимый статус. Используйте 'resolved' или 'rejected'"},
                status=400,
            )

        report.status = status
        report.resolved_by = request.user
        report.resolved_at = timezone.now()

        comment = str(request.data.get("moderator_comment", "")).strip()
        action_taken = request.data.get("action", "none")

        from apps.notifications.infrastructure.models.notifications import Complaint
        complaint = Complaint.objects.filter(source_report_id=report.pk).first()
        if complaint:
            from types import SimpleNamespace
            from apps.users.presentation.views.users_views import AdminComplaintsView
            proxy = SimpleNamespace(
                user=request.user,
                data={
                    "status": "resolved" if status == "resolved" else "dismissed",
                    "action": action_taken if status == "resolved" else "none",
                    "resolution": comment or (
                        "Нарушение подтверждено." if status == "resolved"
                        else "Нарушение не подтверждено."
                    ),
                },
            )
            result = AdminComplaintsView().patch(proxy, complaint.pk)
            if result.status_code >= 400:
                return result
            report.refresh_from_db()
        else:
            report.status = status
            report.resolved_by = request.user
            report.resolved_at = timezone.now()
            report.moderation_comment = comment
            report.action_taken = action_taken
            report.save()

        logger.info(
            f"Report {report_id} resolved by {request.user.username} as {status}"
        )

        return Response(
            {
                "success": True,
                "message": f"Жалоба {status}",
                "report": {
                    "id": report.id,
                    "status": report.status,
                    "resolved_by": request.user.username,
                    "resolved_at": report.resolved_at.isoformat(),
                },
            }
        )
    except Exception as e:
        logger.error(f"Error in resolve_report {report_id}: {e}", exc_info=True)
        return Response(
            {"error": "Ошибка при решении жалобы", "detail": str(e)}, status=500
        )
