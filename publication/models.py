from django.db import models
from django.utils import timezone
from django.contrib.flatpages.models import FlatPage as OldFlatPage
from django.contrib.auth.models import User
from page.models import Menu


class Entry(models.Model):
    title = models.CharField(max_length=100)
    slug = models.SlugField(unique=True)
    content = models.TextField()
    created = models.DateTimeField(editable=False, default=None)
    updated = models.DateTimeField()
    menu = models.ForeignKey(Menu, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)

    class Meta:
        verbose_name_plural = 'entries'
        ordering = ('-created', '-updated')

    def __str__(self):
        return self.title

    def is_created(self):
        return self.created <= timezone.now()

    is_created.boolean = True

    def is_updated(self):
        return self.created < self.updated

    is_updated.boolean = True

    def save(self, *args, **kwargs):
        date = timezone.now()
        if self.id is None:
            self.created = date
        self.updated = date
        return super(Entry, self).save(*args, **kwargs)


class FlatPage(OldFlatPage):
    created = models.DateTimeField(editable=False, default=None)
    updated = models.DateTimeField()
    menu = models.OneToOneField(Menu, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)

    def save(self, *args, **kwargs):
        date = timezone.now()
        if self.id is None:
            self.created = date
        self.updated = date
        return super(FlatPage, self).save(*args, **kwargs)

    class Meta:
        ordering = ('-created', '-updated')
