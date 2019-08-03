from django import forms

class ImportLadderGamesForm(forms.Form):
    email = forms.CharField(help_text='Your Email', max_length=255)
    password = forms.CharField(help_text='Your Password', max_length=255)
    ladder_id = forms.IntegerField(label='Ladder ID', initial=0, min_value=0, max_value=10000)
    max_results = forms.IntegerField(label='Max Results', initial=50, min_value=1)
    offset = forms.IntegerField(min_value=0, initial=0)
