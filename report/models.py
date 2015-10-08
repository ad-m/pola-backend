from os.path import basename
from django.conf import settings
from django.core.urlresolvers import reverse
from django.db import models
from django.utils.translation import ugettext_lazy as _
from product.models import Product
from datetime import datetime


class ReportQuerySet(models.QuerySet):
    def only_open(self):
        return (self.filter(resolved_at__isnull=True)
                    .filter(resolved_by__isnull=True))

    def only_resolved(self):
        return (self.filter(resolved_at__isnull=False)
                    .filter(resolved_by__isnull=False))


class Report(models.Model):
    product = models.ForeignKey(Product)
    client = models.CharField(max_length=40,
                              blank=True, null=True, default=None)
    created_at = models.DateTimeField(auto_now_add=True)
    resolved_at = models.DateTimeField(null=True, blank=True)
    resolved_by = models.ForeignKey(settings.AUTH_USER_MODEL,
                                    null=True, blank=True)
    desciption = models.TextField()
    objects = ReportQuerySet.as_manager()

    def status(self):
        if self.resolved_at is not None:
            return self.RESOLVED

        if self.resolved_by is not None:
            return self.RESOLVED

        return self.OPEN

    def resolve(self, user, commit=True):
        self.resolved_at = datetime.now()
        self.resolved_by = user
        if commit:
            self.save()

    def get_absolute_url(self):
        return reverse('report:detail', args=[self.pk])

    def __unicode__(self):
        return self.desciption[:20] or "None"

    OPEN = 1
    RESOLVED = 2

    class Meta:
        verbose_name = _("Report")
        verbose_name_plural = _("Reports")


class Attachment(models.Model):
    report = models.ForeignKey(Report)
    attachment = models.FileField(
        upload_to="reports/%Y/%m/%d", verbose_name=_("File"))

    @property
    def filename(self):
        return basename(self.attachment.name)

    def __unicode__(self):
        return "%s" % (self.filename)

    def get_absolute_url(self):
        return self.attachment.url

    class Meta:
        verbose_name = _("Report's attachment")
        verbose_name_plural = _("Report's attachments")
