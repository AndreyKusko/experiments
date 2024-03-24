import hashlib

from rest_framework import pagination
from django.core.cache import caches
from rest_framework.response import Response


def CachedCountQueryset(queryset, timeout=60 * 15, cache_name="default"):
    cache = caches[cache_name]
    queryset = queryset._chain()
    real_count = queryset.count

    def count(queryset):
        cache_key = "query-count:" + hashlib.md5(str(queryset.query).encode("utf8")).hexdigest()
        value = cache.get(cache_key)

        value = real_count()
        cache.set(cache_key, value, timeout)
        return value

    queryset.count = count.__get__(queryset, type(queryset))
    return queryset


class CustomPagination(pagination.PageNumberPagination):
    page_size_query_param = "per_page"
    page_size = 20

    def paginate_queryset(self, queryset, request, view=None):
        if hasattr(queryset, "count"):
            queryset = CachedCountQueryset(queryset)

        return super().paginate_queryset(queryset, request, view=view)

    def get_paginated_response(self, data):
        return Response(
            {"page": self.page.number, "total_count": self.page.paginator.count, "results": data},
            content_type="application/json; charset=utf-8",
        )
