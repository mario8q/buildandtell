from django import forms

from .models import VoiceProfile


class VoiceSettingsForm(forms.ModelForm):
    class Meta:
        model = VoiceProfile
        fields = ['enabled', 'default_language']
        labels = {
            'enabled': 'Allow AI calls',
            'default_language': 'Default language',
        }
        help_texts = {
            'enabled': (
                'Let other logged-in builders call an AI that answers '
                'questions about your public projects.'
            ),
            'default_language': (
                'Callers can switch between English and Spanish before '
                'starting a call.'
            ),
        }
        widgets = {
            'enabled': forms.CheckboxInput(attrs={'class': 'checkbox'}),
            'default_language': forms.Select(attrs={'class': 'input'}),
        }
