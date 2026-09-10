from django.db import models
from django.conf import settings
from django.urls import reverse
from django.utils.text import slugify

class Project(models.Model):
    class Status(models.TextChoices):
        PLANNING = 'PL', 'planning'
        IN_PROGRESS = 'IN', 'in_progress'
        COMPLETED = 'CO', 'completed'
        ARCHIVED = 'AR', 'archived'

    class DefaultImage(models.TextChoices):
        DEFAULT_1 = 'pro-default-1', 'Default 1'
        DEFAULT_2 = 'pro-default-2', 'Default 2'
        DEFAULT_3 = 'pro-default-3', 'Default 3'

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name='projects',
        on_delete=models.CASCADE
    )
    title = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255, unique=True, blank=True)
    description = models.TextField()
    status = models.CharField(
        choices=Status.choices, 
        max_length=2, 
        default=Status.PLANNING
    )
    image = models.ImageField(
        upload_to='projects/%Y/%m/%d',
        blank=True,
        null=True
    )
    default_image = models.CharField(
        max_length=20,
        choices=DefaultImage.choices,
        default=DefaultImage.DEFAULT_1
    )
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

    def save(self, *args, **kwargs):
            if not self.slug:
                base = slugify(self.title) or 'project'
                candidate, n = base, 1
                while Project.objects.filter(slug=candidate).exists():
                    candidate, n = f"{base}-{n}", n + 1
                self.slug = candidate
            super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse('projects:project_detail', kwargs={'slug': self.slug})
class BuildUpdate(models.Model):
    class UpdateType(models.TextChoices):
        FEATURE = 'FE', 'Feature'
        BUG = 'BU', 'Bug'
        FIX = 'FX', 'Fix'
        IMPROVEMENT = 'IM', 'Improvement'
        LEARNING = 'LE', 'Learning'
        ARCHITECTURE = 'AR', 'Architecture'
        EXPERIMENT = 'EX', 'Experiment'
        MILESTONE = 'MI', 'Milestone'
        NOTE = 'NO', 'Note'

    project = models.ForeignKey(
        Project,
        related_name="updates",
        on_delete=models.CASCADE
    )
    title = models.CharField(max_length=255)
    type = models.CharField(
        max_length=2,
        choices=UpdateType.choices,
        default=UpdateType.NOTE
    )
    body = models.TextField()
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=['-created'])
        ]
        ordering = ['-created']

    def __str__(self):
        return f'{self.title} build update'