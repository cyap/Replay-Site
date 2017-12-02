from django import forms

class ThreadForm(forms.Form):
    thread_url = forms.URLField(label="Thread URL", required=False)
    thread_start = forms.IntegerField(
    	label="Starting post (Default: First)",
    	required=False)
    thread_end = forms.IntegerField(label="Ending post (Default: Last)", required=False)
    thread_tiers = forms.CharField(label="Tiers (Default: gen7pokebankou)", required=False)
    thread_title = forms.CharField(label="Title", required=False)
    
class RangeForm(forms.Form):
	range_start = forms.IntegerField(label="Start", required=False)
	range_end = forms.IntegerField(label="End", required=False)
	range_tiers = forms.CharField(label="Tier", initial="gen7pokebankou", required=False)
	server = forms.CharField(label="Server (Leave blank for Main)", initial="smogtours", required=False)
	
class OptionsPane(forms.Form):
	moves_check = forms.BooleanField(label="Moves and Teammates", initial=True, required=False)
	leads_check = forms.BooleanField(label="Leads", initial=True, required=False)
	combos_check = forms.BooleanField(label="Combos", initial=True, required=False)
	cutoff = forms.FloatField(label="Cutoff (%)", required=False)
	numeric_cutoff = forms.IntegerField(label="Cutoff (numeric)", required=False)
 
# TODO
# Num validation
# % appended to textbox for cutoff
# individual ids for fields
	