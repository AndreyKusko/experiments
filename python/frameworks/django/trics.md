# Django focus  //  Django tips  //  django trics

- [Фичи Django ORM, о которых вы не знали](https://tproger.ru/translations/django-orm-tips/)

### Select for update
У Django при редактировании модели в корневых файлах есть select_for_update методы.

### Dajgno admin can_delete / has_delete_permission
- https://stackoverflow.com/questions/38127581/django-admin-has-delete-permission-ignored-for-delete-action

### Creating a profile model with both an InlineAdmin and a post_save signal in Django
- https://stackoverflow.com/questions/14345303/creating-a-profile-model-with-both-an-inlineadmin-and-a-post-save-signal-in-djan
```
    class UserProfileInline(admin.StackedInline):
        model = UserProfile

        def has_delete_permission(self, request, obj=None):
            return False

    class UserWithProfileAdmin(UserAdmin):
        inlines = [UserProfileInline]

        def add_view(self, request, form_url="", extra_context=None):
            self.inlines = []
            return super().add_view(request, form_url="", extra_context=None)

        def change_view(self, *args, **kwargs):
            self.inlines = [UserProfileInline]
            return super().change_view(*args, **kwargs)


    admin.site.unregister(User)
    admin.site.register(User, UserWithProfileAdmin)
```
## Admin
### sortable string
```
list_display = ("id", "sortable_name")
list_display_links = ("id", "sortable_str")
ordering = ("number", "name")

def sortable_name(self, obj):
    """Make possible dynamic ordering from model's method __str__."""
    return obj.__str__()

sortable_name.short_description = "Секция"
sortable_name.admin_order_field = "oidp__living_complex__name"
```

## Aggregate
```
from django.contrib.auth.models import User
from django.db.models import Count, Sum, Case, When, Value, IntegerField
User.objects.aggregate(
    total_users=Count('id'),
    total_active_users=Sum(Case( When(is_active=True, then=Value(1)), default=Value(0), output_field=IntegerField(),),),
)
```
`SELECT COUNT(id) AS total_users, SUM(CASE WHEN is_active THEN 1 ELSE 0 END) AS total_active_users FROM auth_users;`
В Django 2.0 был добавлен аргумент filter для агрегатных функций.
```
from django.contrib.auth.models import User
from django.db.models import Count, F
User.objects.aggregate(
    total_users=Count('id'),
    total_active_users=Count('id', filter=F('is_active')),
)
```
`SELECT COUNT(id) AS total_users, COUNT(id) FILTER (WHERE is_active) AS total_active_users FROM auth_users;`
