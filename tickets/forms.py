from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import Ticket, Comment, Profile


class RegistrationForm(UserCreationForm):
    email = forms.EmailField(required=True)
    role = forms.ChoiceField(choices=Profile.ROLE_CHOICES, initial='user')

    class Meta:
        model = User
        fields = ('username', 'email', 'password1', 'password2', 'role')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name in self.fields:
            self.fields[field_name].widget.attrs.update({'class': 'form-control'})

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        if commit:
            user.save()
            user.profile.role = self.cleaned_data['role']
            user.profile.save()
        return user


class TicketCreateForm(forms.ModelForm):
    class Meta:
        model = Ticket
        fields = ('title', 'description', 'priority')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name in self.fields:
            self.fields[field_name].widget.attrs.update({'class': 'form-control'})
        self.fields['description'].widget.attrs.update({'rows': 5})


class TicketUpdateForm(forms.ModelForm):
    class Meta:
        model = Ticket
        fields = ('status', 'priority', 'assigned_to')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name in self.fields:
            self.fields[field_name].widget.attrs.update({'class': 'form-select'})
        # Only show employees in assigned_to dropdown
        self.fields['assigned_to'].queryset = User.objects.filter(profile__role='employee')
        self.fields['assigned_to'].required = False


class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ('body',)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['body'].widget.attrs.update({
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Add a comment...'
        })
        self.fields['body'].label = ''
