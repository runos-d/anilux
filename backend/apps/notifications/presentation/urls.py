from django.urls import path, include
from .views.push_views import PushConfig, DeviceSubscription
from rest_framework.routers import DefaultRouter
from apps.notifications.presentation.views.notifications_views import ComplaintViewSet, NotificationViewSet, ReminderViewSet, NotificationSettingViewSet, EpisodeSubscriptionViewSet

router = DefaultRouter()
router.register(r'complaints', ComplaintViewSet)
router.register(r'notifications', NotificationViewSet)
router.register(r'reminders', ReminderViewSet)
router.register(r'episode-subs', EpisodeSubscriptionViewSet, basename='episodesubs')

urlpatterns = router.urls + [
    path('push/config/', PushConfig.as_view()),
    path('push/subscription/', DeviceSubscription.as_view()),
    path('settings/', NotificationSettingViewSet.as_view({'get': 'retrieve', 'put': 'update', 'patch': 'update'})),
]
