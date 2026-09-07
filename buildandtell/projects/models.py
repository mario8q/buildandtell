from django.db import models
from django.conf import settings

class Project(models.Model):
    class Status(models.TextChoices):
        PLANNING = 'P', 'planning'
        IN_PROGRESS = 'IN', 'in_progress'
        COMPLETED = 'C', 'completed'
        ARCHIVED = 'A', 'archived'

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name='projects',
        on_delete=models.CASCADE
    )
    title = models.CharField(max_length=255)
    description = models.TextField()
    status = models.CharField(choices=Status, max_length=2, default=Status.PLANNING)
    repo_url = models.URLField(blank=True, null=True)
    website_url = models.URLField(blank=True, null=True)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=['-created'])
        ]
        ordering = ['-created']

    def __str__(self):
        return f"{self.title} project"

class Documentation(models.Model):
    project = models.ForeignKey(
        Project,
        related_name="documents",
        on_delete=models.CASCADE
    )
    title = models.CharField(max_length=255)
    body = models.TextField()
    order = models.PositiveBigIntegerField(default=0)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=['-created'])
        ]
        ordering = ['order', 'created']