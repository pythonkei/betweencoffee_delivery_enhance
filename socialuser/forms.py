# socialuser/forms.py
from django.forms import ModelForm
from django import forms
from django.contrib.auth.models import User
from .models import Profile


class ProfileForm(ModelForm):
    class Meta:
        model = Profile
        fields = ['image', 'displayname', 'info']  # Removed phone from fields
        widgets = {
            'image': forms.FileInput(),
            'displayname': forms.TextInput(attrs={'placeholder': 'Add display name'}),
            'info': forms.Textarea(attrs={'rows':3, 'placeholder': 'Add information'})
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['phone'] = forms.CharField(
            required=True,
            widget=forms.TextInput(attrs={
                'placeholder': '91234567',
                'pattern': '[0-9]{8}',
                'title': '請輸入8位數字電話號碼'
            }),
            initial=self.instance.hk_phone() if self.instance.phone else ""
        )

    def clean_phone(self):
        phone = self.data.get('phone', '')
        if phone:
            if not phone.startswith('+852'):
                phone = f"+852{phone}"
            if len(phone) != 12 or not phone[1:].isdigit():
                raise forms.ValidationError("請輸入有效的8位數字香港電話號碼")
            return phone
        raise forms.ValidationError("電話號碼為必填欄位")


class PhoneForm(ModelForm):
    class Meta:
        model = Profile
        fields = ['phone']
        widgets = {
            'phone': forms.TextInput(attrs={
                'placeholder': '91234567',
                'pattern': '[0-9]{8}',
                'title': '請輸入8位數字電話號碼'
            })
        }

    def clean_phone(self):
        phone = str(self.cleaned_data.get('phone'))  # Convert to string first
        if phone:
            # Remove any existing country code
            if phone.startswith('+852'):
                phone = phone[4:]
            # Ensure it's 8 digits
            if len(phone) != 8 or not phone.isdigit():
                raise forms.ValidationError("請輸入有效的8位數字香港電話號碼")
            return f"+852{phone}"  # Return in E.164 format
        return phone


class EmailForm(ModelForm):
    email = forms.EmailField(required=True)
    class Meta:
        model = User
        fields = ['email']


class UsernameForm(ModelForm):
    class Meta:
        model = User
        fields = ['username']