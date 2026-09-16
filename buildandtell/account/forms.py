from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.models import User
from .models import Profile

class UserRegistrationForm(forms.ModelForm):
    password = forms.CharField(label="password", widget=forms.PasswordInput(attrs={'class': 'input', 'placeholder': '••••••••'}))
    password2 = forms.CharField(label="repeat password", widget=forms.PasswordInput(attrs={'class': 'input', 'placeholder': '••••••••'}))
    class Meta:
        model = get_user_model()
        fields = ["first_name", "username", "email"]
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'input', 'placeholder': 'Mario'}),
            'username': forms.TextInput(attrs={'class': 'input', 'placeholder': 'mario8q'}),
            'email': forms.EmailInput(attrs={'class': 'input', 'placeholder': 'you@buildandtell.app'}),
        }

    def clean_password2(self):
        cd = self.cleaned_data
        if cd["password"] != cd["password2"]:
            raise forms.ValidationError("Passwords does not match")
        return cd["password2"]

    def clean_email(self):
        data = self.cleaned_data["email"]
        if User.objects.filter(email=data).exists():
            raise forms.ValidationError("Email already in use")
        return data
class UserEditForm(forms.ModelForm):
    class Meta:
        model = get_user_model()
        fields = ['first_name', 'username', 'email']
        labels = {
            'first_name': 'first name',
            'username': 'username',
            'email': 'email',
        }
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'input', 'placeholder': 'Mario'}),
            'username': forms.TextInput(attrs={'class': 'input', 'placeholder': 'mario8q'}),
            'email': forms.EmailInput(attrs={'class': 'input', 'placeholder': 'you@buildandtell.app'}),
        }

    def clean_email(self):
        email = self.cleaned_data['email']
        qs = User.objects.exclude(id=self.instance.id).filter(email=email)
        if qs.exists():
            raise forms.ValidationError('Email already in use')
        return email

class ProfileEditForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ['image', 'bio', 'website', 'github']
        labels = {
            'image': 'avatar',
            'bio': 'bio',
            'website': 'website',
            'github': 'github',
        }
        widgets = {
            'image': forms.ClearableFileInput(attrs={
                'class': 'input input--file',
                'accept': 'image/jpeg,image/png',
            }),
            'bio': forms.Textarea(attrs={
                'class': 'input',
                'rows': 5,
                'placeholder': 'What kind of things do you build?',
            }),
            'website': forms.URLInput(attrs={
                'class': 'input',
                'placeholder': 'https://your-site.dev',
            }),
            'github': forms.URLInput(attrs={
                'class': 'input',
                'placeholder': 'https://github.com/you',
            }),
        }