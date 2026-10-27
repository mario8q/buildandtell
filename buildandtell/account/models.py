from django.db import models
from django.conf import settings
from django.urls import reverse
from projects.models import Project

class Profile(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        related_name='profile',
        on_delete=models.CASCADE
    )
    image = models.ImageField(
        upload_to='account/%Y/%m/%d',
        blank=True
    )
    bio = models.TextField(
        blank=True
    )

    projects_stars = models.ManyToManyField(
        Project,
        related_name='users_stars',
        blank=True
    )

    following = models.ManyToManyField(
        'self',
        symmetrical=False,
        blank=True
    )
    followers = models.PositiveIntegerField(default=0)

    website = models.URLField(blank=True)

    github = models.URLField(blank=True)

    def get_absolute_url(self):
        return reverse("account:user_detail", kwargs={'username': self.user.username})

    def __str__(self):
        return f'Profile of {self.user.username}'