from django import forms
from .models import Project, BuildUpdate

class CreateProjectForm(forms.ModelForm):
    class Meta:
        model = Project
        fields = ['title', 'description', 'image', 'default_image', 'status', 'repo_url', 'website_url']

    def clean_image(self):
        image = self.cleaned_data.get('image')

        if not image:
            return image

        allowed_extensions = ['jpg', 'jpeg', 'png']
        allowed_types = ['image/jpeg', 'image/png']

        extension = image.name.split('.')[-1].lower()

        if extension not in allowed_extensions:
            raise forms.ValidationError(
                'Format is invalid.'
            )

        if image.content_type not in allowed_types:
            raise forms.ValidationError(
                'Image type not valid.'
            )

        return image

class CreateBuildUpdateForm(forms.ModelForm):
    class Meta:
        model = BuildUpdate
        fields = ['title', 'type', 'body']