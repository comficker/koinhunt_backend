from django.db import models
from utils.slug import unique_slugify
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _


class BaseModel(models.Model):
    STATUS_CHOICE = (
        (-1, _("Deleted")),
        (0, _("Pending")),
        (1, _("Active")),
    )

    updated = models.DateTimeField(default=timezone.now)
    created = models.DateTimeField(default=timezone.now)
    db_status = models.IntegerField(choices=STATUS_CHOICE, default=1)

    class Meta:
        abstract = True

    def save(self, **kwargs):
        # generate unique slug
        self.created = timezone.now()
        self.updated = timezone.now()
        super(BaseModel, self).save(**kwargs)


class HasIDSting(models.Model):
    name = models.CharField(max_length=200)
    id_string = models.CharField(max_length=200)

    def save(self, **kwargs):
        # generate unique slug
        if hasattr(self, 'slug') and self.id is None and self.id_string is None or self.id_string == "":
            unique_slugify(self, self.name, "id_string")
        elif self.id is not None and self.id_string:
            unique_slugify(self, self.id_string, "id_string")
        super(HasIDSting, self).save(**kwargs)

    class Meta:
        abstract = True


class Validation(models.Model):
    verified = models.BooleanField(default=False)
    validation_score = models.FloatField(default=0)

    class Meta:
        abstract = True
