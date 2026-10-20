from django import template
from django.conf import settings

register = template.Library()


@register.simple_tag
def image_thumb(image, width, height, quality=90):
    if not image:
        return ''

    if settings.DEBUG:
        return image.url

    from cloudinary import CloudinaryResource

    return CloudinaryResource(image.name).build_url(
        width=width,
        height=height,
        crop='fill',
        gravity='auto',
        quality=quality,
        secure=True,
    )
