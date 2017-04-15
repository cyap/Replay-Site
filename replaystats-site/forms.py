from django import forms

class ThreadForm(forms.Form):
    thread_url = forms.URLField(label="Thread URL", required=False)
    thread_start = forms.CharField(label="Starting post (Default: First)", required=False)
    thread_end = forms.CharField(label="Ending post (Default: Last)", required=False)
    thread_tiers = forms.CharField(label="Tiers (Default: gen7pokebankou)", required=False)
    thread_title = forms.CharField(label="Title", required=False)
    
class RangeForm(forms.Form):
	range_start = forms.CharField(label="Start", required=False)
	range_end = forms.CharField(label="End", required=False)
	range_tier = forms.CharField(label="Tier (Default: gen7pokebankou)", required=False)
	
class OptionsPane(forms.Form):
	moves_check = forms.BooleanField(label="Moves and Teammates", initial=True)
	leads_check = forms.BooleanField(label="Leads", initial=True)
	combos_check = forms.BooleanField(label="Combos", initial=True)
	cutoff = forms.CharField(label="Cutoff (%)", required=False)
	numeric_cutoff = forms.CharField(label="Cutoff (numeric)", required=False)
 
# TODO
# Num validation
# % appended to textbox for cutoff
# individual ids for fields
	