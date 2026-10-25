from django.urls import path, include
from rest_framework.routers import DefaultRouter
from apps.reactor.presentation.views.reactor_views import ReactorPostViewSet

router = DefaultRouter()
router.register(r'posts', ReactorPostViewSet)

urlpatterns = router.urls