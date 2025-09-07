from django import forms
from .models import Post, Advertisement

class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ['area', 'image']  
        widgets = {
            'area': forms.TextInput(attrs={'required': 'required'}),
        }

class AdvertisementForm(forms.ModelForm):
    class Meta:
        model = Advertisement
        fields = ['area', 'content', 'advertiser_name', 'image']
        widgets = {
            'area': forms.TextInput(attrs={'required': 'required'}),
            'content': forms.Textarea(attrs={'required': 'required'}),
            'advertiser_name': forms.TextInput(),
        }