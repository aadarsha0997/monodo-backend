from datetime import timedelta

from django import template
from django.utils import timezone

from referral_system.models import CustomUser, LoginActivity, Record, ReferralTracking, Level

register = template.Library()


@register.simple_tag
def recent_logins(limit=8):
    return (
        LoginActivity.objects.select_related("user")
        .order_by("-login_time")[:limit]
    )


@register.simple_tag
def recent_records(limit=8):
    return (
        Record.objects.select_related("level")
        .order_by("-updated_at")[:limit]
    )


@register.simple_tag
def dashboard_metrics():
    now = timezone.now()
    last_24 = now - timedelta(hours=24)

    return [
        {
            "label": "Total Users",
            "value": CustomUser.objects.count(),
        },
        {
            "label": "Active Agents",
            "value": CustomUser.objects.filter(user_type="AGENT", is_active=True).count(),
        },
        {
            "label": "Referrals (24h)",
            "value": ReferralTracking.objects.filter(created_at__gte=last_24).count(),
        },
        {
            "label": "Pending Records",
            "value": Record.objects.filter(status="PENDING").count(),
        },
        {
            "label": "Published Levels",
            "value": Level.objects.filter(is_active=True).count(),
        },
    ]

