from django.contrib import admin

from .models import Idea, IdeaVote


@admin.register(Idea)
class IdeaAdmin(admin.ModelAdmin):
    list_display = ("title", "kind", "status", "priority", "author", "votes_count", "created_at")
    list_filter = ("kind", "status", "priority")
    search_fields = ("title", "description", "author__username")
    readonly_fields = ("votes_count", "created_at", "updated_at")


@admin.register(IdeaVote)
class IdeaVoteAdmin(admin.ModelAdmin):
    list_display = ("idea", "user", "created_at")
    search_fields = ("idea__title", "user__username")
