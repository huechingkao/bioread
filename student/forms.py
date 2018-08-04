# -*- coding: UTF-8 -*-
from django import forms
from student.models import *

class EnrollForm(forms.ModelForm): 
    password = forms.CharField()

    class Meta:
        model = Enroll
        fields = ('seat',)
        
    def __init__(self, *args, **kwargs):
        super(EnrollForm, self).__init__(*args, **kwargs)  
        self.fields['password'].label = "選課密碼"
        self.fields['seat'].label = "座號"
        
class ForumSubmitForm(forms.ModelForm):
    class Meta:
        model = SFWork
        fields = ['memo','memo_e', 'memo_c']  
      
    def __init__(self, *args, **kwargs):
        super(ForumSubmitForm, self).__init__(*args, **kwargs)
        self.fields['memo'].label = "心得感想"
        self.fields['memo_e'].label = "英文"
        self.fields['memo_c'].label = "中文"            
        #self.fields['file'].label = "檔案"
