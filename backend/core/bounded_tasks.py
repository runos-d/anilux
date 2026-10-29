from celery import Task


class BoundedPublishTask(Task):
    abstract = True

    def apply_async(self, *args, **options):
        if self.app.conf.get('site_bounded_publish', False):
            for name in ('timeout', 'confirm_timeout'):
                value = options.get(name)
                options[name] = min(2., max(.1, float(value))) if value is not None else 2.
        return super().apply_async(*args, **options)
