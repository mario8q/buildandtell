from django.db import models
from django.conf import settings


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

    website = models.URLField(blank=True)

    github = models.URLField(blank=True)

    def __str__(self):
        return f'Profile of {self.user.username}'