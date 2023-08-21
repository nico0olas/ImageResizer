from django import forms


class MultipleFileInput(forms.ClearableFileInput):
    allow_multiple_selected = True


class MultipleFileField(forms.FileField):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault("widget", MultipleFileInput())
        super().__init__(*args, **kwargs)

    def clean(self, data, initial=None):
        single_file_clean = super().clean
        if isinstance(data, (list, tuple)):
            result = [single_file_clean(d, initial) for d in data]
        else:
            result = single_file_clean(data, initial)
        return result


class FileFieldForm(forms.Form):
    file_field = MultipleFileField(label="Selectionner les images")
    #compression = forms.IntegerField(label='Niveau de compression', min_value=1, max_value=10, initial=5)
    CHOICES = [("1", "un peu"), ("3", "beaucoup"), ("5", "à la folie"), ("7", "passionnément"), ("100", "Minecraft")]
    compression = forms.ChoiceField(label='Niveau de compression',widget=forms.RadioSelect, choices=CHOICES)
