from django import forms
from .models import Project, BuildUpdate

class CreateProjectForm(forms.ModelForm):
    class Meta:
        model = Project
        fields = ['title', 'description', 'image', 'default_image', 'status', 'repo_url', 'website_url']
        labels = {
            'title': 'title',
            'description': 'description',
            'image': 'image',
            'default_image': 'default image',
            'status': 'status',
            'repo_url': 'repository',
            'website_url': 'website',
        }
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'input',
                'placeholder': 'short project name',
            }),
            'description': forms.Textarea(attrs={
                'class': 'input',
                'rows': 5,
                'placeholder': 'What are you building and why?',
            }),
            'image': forms.ClearableFileInput(attrs={
                'class': 'input input--file',
                'accept': 'image/jpeg,image/png',
            }),
            'default_image': forms.Select(attrs={'class': 'input'}),
            'status': forms.Select(attrs={'class': 'input'}),
            'repo_url': forms.URLInput(attrs={
                'class': 'input',
                'placeholder': 'https://github.com/you/your-repo',
            }),
            'website_url': forms.URLInput(attrs={
                'class': 'input',
                'placeholder': 'https://your-project.dev',
            }),
        }

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
        labels = {
            'title': 'title',
            'type': 'type',
            'body': 'body',
        }
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'input',
                'placeholder': 'short summary, like a commit message',
            }),
            'type': forms.Select(attrs={'class': 'input'}),
            'body': forms.Textarea(attrs={
                'class': 'input',
                'rows': 7,
                'placeholder': 'What did you ship, learn, or change?',
            }),
        }