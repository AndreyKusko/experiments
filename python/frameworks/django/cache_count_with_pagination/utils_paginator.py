import hashlib

from django.core.cache import cache
from django.core.paginator import Paginator
from django.utils.functional import cached_property
from rest_framework.pagination import LimitOffsetPagination


class CachedPaginator(Paginator):
    @cached_property
    def count(self):
        return self.object_list.values("id").count()


class CachedPageNumberPagination(LimitOffsetPagination):
    # django_paginator_class = CachedPaginator

    # @cached_property
    def get_count(self, queryset):
        try:
            query = str(queryset.query).encode("utf8")
        except:
            query = None
        
        if not query:
            return queryset.values("id").count()

        cache_key = "query-count:" + hashlib.md5(query).hexdigest()
        # value = cache.get(cache_key)
        value = None

        if not value:
            value = queryset.values("id").count()
            cache.set(cache_key, value, 300)

        return value
