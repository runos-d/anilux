from django.contrib import admin
from .models import SiteSeoSettings, SeoCollection, SeoOverride, SeoAlias


@admin.register(SiteSeoSettings)
class SiteSettingsAdmin(admin.ModelAdmin):
    def has_add_permission(self, request):
        return not SiteSeoSettings.objects.exists()


@admin.register(SeoCollection)
class CollectionAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'enabled', 'updated_at')
    list_filter = ('enabled',)
    prepopulated_fields = {'slug': ('name',)}


@admin.register(SeoOverride)
class OverrideAdmin(admin.ModelAdmin):
    list_display = ('path', 'title', 'noindex')
    search_fields = ('path', 'title')


@admin.register(SeoAlias)
class AliasAdmin(admin.ModelAdmin):
    list_display = ('path', 'kind', 'object_id')
    readonly_fields = ('path', 'kind', 'object_id')

    def has_add_permission(self, request):
        return False
