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
        fields = ['area']
        widgets = {
            'area': forms.TextInput(attrs={'required': 'required'}),
        }