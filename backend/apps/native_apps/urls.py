from django.urls import path
from .views import ReleasesView, DownloadView
urlpatterns = [path('releases/', ReleasesView.as_view()),
               path('releases/<str:key>/<str:name>', DownloadView.as_view())]
