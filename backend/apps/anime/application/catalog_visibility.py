from functools import reduce
from operator import or_
from django.db.models import Q
from django.utils import timezone
from apps.anime.models import Anime
from apps.anime.infrastructure.models.anime import CatalogHideRule, CatalogVisibility


def rule_query(rule):
    field = {'genre': 'genres__contains', 'studio': 'studios__contains',
             'title': 'title_ru__icontains', 'franchise': 'franchise__name__icontains',
             'kind': 'kind__iexact'}[rule.rule_type]
    value = [rule.value] if rule.rule_type in ('genre', 'studio') else rule.value
    query = Q(**{field: value})
    if rule.rule_type == 'title':
        query |= Q(title_en__icontains=rule.value) | Q(title_jp__icontains=rule.value)
    return query


def hidden_anime():
    rules = reduce(or_, (rule_query(rule) for rule in CatalogHideRule.objects.all()), Q(pk__in=[]))
    return Anime.objects.filter(rules | Q(catalog_visibility__manual_hidden=True)).exclude(
        catalog_visibility__restored=True)


def hidden_values(rule_type):
    return {
        value.strip().casefold()
        for value in CatalogHideRule.objects.filter(rule_type=rule_type).values_list('value', flat=True)
        if value and value.strip()
    }


def is_hidden_value(rule_type, value):
    return isinstance(value, str) and value.strip().casefold() in hidden_values(rule_type)


def visible_anime():
    return Anime.objects.filter(
        is_available=True,
        has_cyrillic=True,
    ).exclude(year__gt=timezone.now().year).exclude(title_ru__isnull=True).exclude(title_ru='').exclude(
        pk__in=hidden_anime().values('pk')
    )


def invalidate():
    from apps.anime.application.recommendations import invalidate_catalog
    invalidate_catalog()
