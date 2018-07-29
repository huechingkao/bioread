# -*- coding: UTF-8 -*-
from django import forms
from django.contrib.auth.models import User, Group
from nocaptcha_recaptcha.fields import NoReCaptchaField
from account.models import *

# 使用者登入表單
class LoginForm(forms.Form):
    username = forms.CharField(label='帳號')
    password = forms.CharField(label='密碼', widget=forms.PasswordInput)

class UserRegistrationForm(forms.ModelForm):
    error_messages = {
        'duplicate_username': ("此帳號已被使用")
    }

    username = forms.RegexField(
        label="帳號", max_length=30, regex=r"^[\w.@+-]+$",
        error_messages={
            'invalid': ("帳號名稱無效")
        }
    )
    password = forms.CharField(label='密碼', widget=forms.PasswordInput)
    password2 = forms.CharField(label='確認密碼', widget=forms.PasswordInput)

    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email']
        labels = {
            'first_name': '真實姓名',
            'last_name': '學校名稱',
            'email': '電子郵件',
        }

    def clean_password2(self):
        cd = self.cleaned_data
        if cd['password'] != cd['password2']:
            raise forms.ValidationError('Passwords don\'t match.')
        return cd['password2']

    def clean_username(self):
        username = self.cleaned_data["username"]
        if self.instance.username == username:
            return username
        try:
            User._default_manager.get(username=username)
        except User.DoesNotExist:
            return username
        raise forms.ValidationError(
            self.error_messages['duplicate_username'],
            code='duplicate_username',
        )

class UserUpdateForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ('username', 'first_name', 'last_name', 'email')
        labels = {
            'username': '帳號',
            'first_name': '真實姓名',
            'last_name': '學校名稱',
            'email': '電子郵件',
        }

class UserPasswordForm(forms.ModelForm):
    password = forms.CharField(label='密碼', widget=forms.PasswordInput)

    class Meta:
        model = User
        fields = ('password',)

class UserTeacherForm(forms.Form):
    teacher = forms.BooleanField(label='教師', required=False)

    def __init__(self, *args, **kwargs):
        user_id = kwargs.pop('pk', None)
        super(UserTeacherForm, self).__init__(*args, **kwargs)
        self.fields['teacher'].initial = User.objects.get(id=user_id).groups.filter(name='teacher').exists()

# 學校表單
class RegistrationSchoolForm(forms.ModelForm):
    captcha = NoReCaptchaField(label='')

    class Meta:
        model = School
        fields = ('county', 'zone', 'system', 'name')
        labels = {
            'county': '縣市',
            'zone': '區域',
            'system': '學制',
            'name': '學校名稱',
        }
        
# 新增一個私訊表單
class LineForm(forms.ModelForm):
    class Meta:
       model = Message
       fields = ['title','content',]
       
    def __init__(self, *args, **kwargs):
        super(LineForm, self).__init__(*args, **kwargs)
        self.fields['title'].label = "主旨"
        self.fields['title'].widget.attrs['size'] = 50
        self.fields['content'].label = "內容"
        self.fields['content'].required = False            
        self.fields['content'].widget.attrs['cols'] = 50
        self.fields['content'].widget.attrs['rows'] = 20          
