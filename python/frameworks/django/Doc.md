# Django admin 


Inlines
https://habr.com/ru/articles/651179/
https://github.com/theatlantic/django-nested-admin



# Django
django signals (pre_save, post_save ...)
https://simpleisbetterthancomplex.com/tutorial/2016/07/28/how-to-create-django-signals.html <- мега полезная статья
https://docs.djangoproject.com/en/2.2/ref/signals/#django.db.models.signals.pre_save

```
def my_model_post_save_receiver(instance, created, *_args, **_kwargs):
    if created:
        from api.serializers import AuthUserSerializer

        serializer = AuthUserSerializer(instance)
        data = serializer.data
        data["qwe"] = 'qwe'

        response = request_authentication_server(method="POST", data=data)
        status_code = response.status_code
        # status_code = 400
        if status_code not in (200, 201):
            message = f'id={instance.id} 'action' failed'
            send_log(
                place=inspect.currentframe().f_code.co_name,
                message=message,
                status=status_code,
                user=instance.id,
            )

def my_model_pre_save_receiver(instance, *_args, **_kwargs):
    if instance.id:
        from myapp.serializers import MySerializer
        from myapp.models import MyModel

        my_model = MyModel.objects.only("id", "name").get(id=instance.id)
        old_field = my_model.phone
        if old_field != instance.my_field or my_model.status != instance.status:

            serializer = MySerializer(instance)
            data = serializer.data
            data["my_add_key"] = 'qwe'

            link = "".join([old_field, "/"])
            response = request_authentication_server(method="PATCH", link=link, data=data)
            status_code = response.status_code
            if not status_code == 200:
                message = f'id={instance.id} update failed'
                send_log(
                    place=inspect.currentframe().f_code.co_name,
                    message=message,
                    status=status_code,
                    user=instance.id,
                )
                raise Exception(message)
```

# Либа django-model-utils 
Помогает отслеживать изменения в сигналах моделей причем из любого сигнала.
- https://stackoverflow.com/questions/5582410/django-how-to-access-original-unmodified-instance-in-post-save-signal
- https://stackoverflow.com/questions/51775506/django-how-to-get-old-value-and-new-value-in-pre-save-fucntion/51779505
```
сlass MyModel(…):
    …
    tracker = ( FieldTracker())  # req


def my_model_pre_save_receiver(sender, instance, *args, **kwargs):
    print('instance.id', instance.id)
    if (
        instance.tracker.has_changed("phone") or instance.tracker.has_changed("status")
    ) and instance.tracker.previous("phone"):
        from my_app.serializers import MyModelSerializer

        serializer = MyModelSerializer(instance)
        data = serializer.data
        data["my_add_key"] = 'qwe'

        link = "".join([instance.tracker.previous("phone"), "/"])
        response = request_authentication_server(method="PATCH", link=link, data=data)
        status_code = response.status_code
        if not status_code == 200:
            error = (
                f"Error in {inspect.currentframe().f_code.co_name} "
                f'| id={instance.id} update fail in, '
                f"code={status_code}, reason={response.reason}"
            )
            logger.error(error)
            raise Exception(error)

```


