
from django.db import models

class AcademicYear(models.Model):
    name = models.CharField("السنة الدراسية", max_length=20, unique=True)
    start_date = models.DateField("تاريخ البدء", blank=True, null=True)
    end_date = models.DateField("تاريخ الانتهاء", blank=True, null=True)
    is_active = models.BooleanField("السنة النشطة", default=False)
    code = models.CharField("كود السنة", max_length=10, unique=True, editable=False)
    def __str__(self): return self.name
    class Meta:
        verbose_name = "سنة دراسية"
        verbose_name_plural = "السنوات الدراسية"
        ordering = ['-name']