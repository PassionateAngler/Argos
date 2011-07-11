from django import forms
from moviemaker.models import MovieCacheFile

class CameraSearch(forms.Form):
    from datetime import timedelta
    INPUT_FORMAT = "%Y-%m-%d %H:%M"
    #ALLOWED_LENGHT = timedelta(seconds=MovieCacheFile.MAX_SLICE_DIST)
    start = forms.DateTimeField(required=True)
    #end = forms.DateTimeField(required=True)

    #def clean(self):
    #    from datetime import datetime as dt
    #    cleaned_data = self.cleaned_data
    #    start = cleaned_data.get('start')
    #    end = cleaned_data.get('end')
    #    if start and end :
    #        if start + self.ALLOWED_LENGHT <= end:
    #            del cleaned_data['start']
    #            del cleaned_data['end']
    #            raise forms.ValidationError("Maximum movie lenght is one hour")
    #        if start > end:
    #            del cleaned_data['start']
    #            del cleaned_data['end']
    #            raise forms.ValidationError("End-time before start-time")

    #    return cleaned_data
