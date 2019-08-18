from django import forms

class ImportLadderGamesForm(forms.Form):
    email = forms.CharField(max_length=255)
    password = forms.CharField(max_length=255, widget=forms.PasswordInput)
    ladder_id = forms.IntegerField(label='Ladder ID', initial=0, min_value=0, max_value=10000)
    max_results = forms.IntegerField(label='Max Results', initial=50, min_value=1)
    offset = forms.IntegerField(min_value=0, initial=0)
    halt_if_exists = forms.BooleanField(initial=True)
