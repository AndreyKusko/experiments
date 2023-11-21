# Django Models

choice выбор, делачется через Charfield
```
class MyModel(...):
    class MySource:
        FIRST = "FIRST"
        SECOND = "SECOND"
        ...
    MY_SOURCES = (
        (MySource.FIRST, "Alpha"),
        (MySource.SECOND, "Beta"),
    )
    id = models.Integer...
    ...
    my_source = models.CharField(
        max_length=128, blank=True, null=True, verbose_name="Источник оформления",
        default=MySource.FIRST, или сразу Alpha
        choices=MY_SOURCES,
    )
```

