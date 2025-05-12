from django import forms
from .models import Post, Comment

class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ['title', 'content']

class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ['content', 'post', 'parent_comment', 'content', 'image']
        widgets = {
            'image': forms.ClearableFileInput(attrs={'accept': 'image/*,.gif'})
        }
    def clean_content(self):
        content = self.cleaned_data.get('content')
        if not content:
            raise forms.ValidationError("Content cannot be empty")
        return content