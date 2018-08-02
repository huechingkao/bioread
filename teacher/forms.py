# -*- coding: utf-8 -*-
from django import forms
from teacher.models import *

#上傳檔案
class UploadFileForm(forms.Form):
    file = forms.FileField()

# 新增一個分組表單
class GroupForm(forms.ModelForm):
        class Meta:
           model = ClassroomGroup
           fields = ['title','numbers', 'assign']
        
        def __init__(self, *args, **kwargs):
            super(GroupForm, self).__init__(*args, **kwargs)
            self.fields['title'].label = "分組名稱"							
            self.fields['numbers'].label = "分組數目"	
						
# 新增一個分組表單
class GroupForm2(forms.ModelForm):
        class Meta:
           model = ClassroomGroup
           fields = ['title','numbers']
        
        def __init__(self, *args, **kwargs):
            super(GroupForm2, self).__init__(*args, **kwargs)
            self.fields['title'].label = "分組名稱"							
            self.fields['numbers'].label = "分組數目"	
