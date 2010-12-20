from django import forms
from django.contrib.auth.models import User

class ContactForm(forms.Form):
    name = forms.CharField(max_length=100,
           help_text="Full Name", widget=forms.TextInput(attrs={'size':'40'}),required=False)
    subject = forms.CharField(max_length=100,
              help_text="Subject of your message", widget=forms.TextInput(attrs={'size':'40'}))
    sender = forms.EmailField(
              help_text="Your email address", widget=forms.TextInput(attrs={'size':'40'}),required=True)
    message = forms.CharField(
              help_text="Please enter as much text as you would like",
              widget=forms.Textarea(attrs={'rows':'12','cols':'60'}))
    cc_myself = forms.BooleanField(required=False,
                help_text="Send yourself a copy of this message")
