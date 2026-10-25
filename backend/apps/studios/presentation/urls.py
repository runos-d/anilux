from django.urls import path, re_path
from config import feature_flags
from config.disabled_features import disabled_feature
from apps.studios.presentation.views.studios_views import (
    StudioListView, StudioPopularView, StudioDetailView, StudioDetailByIdView,
    StudioWorksView, StudioStaffView, StudioNewsView, StudioAwardsView,
    StudioDiscussionsView, StudioDiscussionCreateView,
    StudioDiscussionRepliesView, StudioDiscussionLikeView, StudioDiscussionDislikeView,
    StudioReviewsView, StudioReviewCreateView,
    StudioSubscribeView, StudioSimilarView, StudioSyncFromAnimeView,
)

urlpatterns = [
    path('', StudioListView.as_view(), name='studio-list'),
    path('popular/', StudioPopularView.as_view(), name='studio-popular'),

    path('<slug:slug>/', StudioDetailView.as_view(), name='studio-detail'),
    path('id/<uuid:pk>/', StudioDetailByIdView.as_view(), name='studio-detail-by-id'),

    path('<slug:slug>/works/', StudioWorksView.as_view(), name='studio-works'),
    path('<slug:slug>/staff/', StudioStaffView.as_view(), name='studio-staff'),
    path('<slug:slug>/news/', StudioNewsView.as_view(), name='studio-news'),
    path('<slug:slug>/awards/', StudioAwardsView.as_view(), name='studio-awards'),
    path('<slug:slug>/discussions/', StudioDiscussionsView.as_view(), name='studio-discussions'),
    path('<slug:slug>/discussions/create/', StudioDiscussionCreateView.as_view(), name='studio-discussion-create'),
    path('<slug:slug>/discussions/<uuid:discussion_id>/replies/', StudioDiscussionRepliesView.as_view(), name='studio-discussion-replies'),
    path('<slug:slug>/reviews/', StudioReviewsView.as_view(), name='studio-reviews'),
    path('<slug:slug>/reviews/create/', StudioReviewCreateView.as_view(), name='studio-review-create'),
    path('<slug:slug>/subscribe/', StudioSubscribeView.as_view(), name='studio-subscribe'),
    path('<slug:slug>/similar/', StudioSimilarView.as_view(), name='studio-similar'),
]

if feature_flags.FEATURE_STUDIO_SYNC_ENABLED:
    urlpatterns.insert(2, path('sync/', StudioSyncFromAnimeView.as_view(), name='studio-sync'))
else:
    urlpatterns.insert(2, path('sync/', disabled_feature, name='studio-sync-disabled'))
if feature_flags.FEATURE_STUDIO_REACTIONS_ENABLED:
    urlpatterns.extend([
        path('<slug:slug>/discussions/<uuid:discussion_id>/like/', StudioDiscussionLikeView.as_view(), name='studio-discussion-like'),
        path('<slug:slug>/discussions/<uuid:discussion_id>/dislike/', StudioDiscussionDislikeView.as_view(), name='studio-discussion-dislike'),
    ])
else:
    urlpatterns.extend([
        re_path(r'^[^/]+/discussions/[^/]+/(?:like|dislike)/$', disabled_feature),
    ])
