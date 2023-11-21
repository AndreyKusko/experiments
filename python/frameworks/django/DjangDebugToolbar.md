Django Debug toolbar
- settings.py
    DEBUG_TOOLBAR = True
    if DEBUG and DEBUG_TOOLBAR:
        DEBUG_TOOLBAR_PATCH_SETTINGS = False
        MIDDLEWARE += ("debug_toolbar.middleware.DebugToolbarMiddleware",)
        INSTALLED_APPS += ("debug_toolbar",)
        INTERNAL_IPS = ("127.0.0.1",)

        def show_on_api(request):
            return True

        DEBUG_TOOLBAR_CONFIG = {"SHOW_TOOLBAR_CALLBACK": show_on_api}

- urls.py
    import debug_toolbar
    from django.conf.urls import url
    from django.contrib import admin
    ...
    include("hrm.urls")),
        path("management/", include("management.urls")),
        url(r"^__debug__/", include(debug_toolbar.urls)),
    ]
- 