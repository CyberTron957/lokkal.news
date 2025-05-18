from django import forms
from .models import Post

class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ['area', 'image']  
        widgets = {
            'area': forms.TextInput(attrs={'required': 'required'}),
        }