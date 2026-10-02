from django import forms
from taggit.forms import TagWidget
from .models import Project, BuildUpdate

class CreateProjectForm(forms.ModelForm):
    class Meta:
        model = Project
        fields = ['title', 'description', 'tags', 'image', 'default_image', 'status', 'repo_url', 'website_url']
        labels = {
            'title': 'title',
            'description': 'description',
            'tags': 'tags',
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
            'description': forms.TextInput(attrs={
                'class': 'input',
                'rows': 5,
                'placeholder': 'What are you building and why?',
            }),
            'tags': TagWidget(attrs={
                'class': 'input',
                'placeholder': 'python, django, api',
            }),
            'image': forms.ClearableFileInput(attrs={
                'class': 'input input--file',
                'accept': 'image/jpeg,image/png,image/jpg',
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

class SearchProjectForm(forms.Form):
    query = forms.CharField(max_length=255)