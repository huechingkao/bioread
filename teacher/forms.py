# -*- coding: utf-8 -*-
from django import forms
from teacher.models import *
from account.models import *

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

# 新增一個課程表單
class ForumCategroyForm(forms.ModelForm):
        class Meta:
           model = FWork
           fields = ['domains', 'levels']
        
        def __init__(self, *args, **kwargs):
            super(ForumCategroyForm, self).__init__(*args, **kwargs)			
						
# 新增一個繳交期長表單
class ForumDeadlineForm(forms.ModelForm):
        class Meta:
           model = FClass
           fields = ['deadline', 'deadline_date']
        
        def __init__(self, *args, **kwargs):
            super(ForumDeadlineForm, self).__init__(*args, **kwargs)			

						
# 新增一個作業
class ForumForm(forms.ModelForm):
        class Meta:
           model = FWork
           fields = ['title']
        
        def __init__(self, *args, **kwargs):
            super(ForumForm, self).__init__(*args, **kwargs)
            self.fields['title'].label = "討論主題"
            self.fields['title'].widget.attrs.update({'class' : 'form-control list-group-item-text'})									
						
# 新增一個作業
class ForumContentForm(forms.ModelForm):
        class Meta:
           model = FContent
           fields = ['forum_id', 'types', 'title', 'link', 'youtube', 'file', 'memo']
        
        def __init__(self, *args, **kwargs):
            super(ForumContentForm, self).__init__(*args, **kwargs)
            self.fields['forum_id'].required = False		
            self.fields['title'].required = False						
            self.fields['link'].required = False
            self.fields['youtube'].required = False
            self.fields['file'].required = False
            self.fields['memo'].required = False						
						
# 新增一個課程表單
class AnnounceForm(forms.ModelForm):
        class Meta:
           model = Message
           fields = ['title', 'content']
        
        def __init__(self, *args, **kwargs):
            super(AnnounceForm, self).__init__(*args, **kwargs)
            self.fields['title'].label = "公告主旨"
            self.fields['title'].widget.attrs['size'] = 50	
            self.fields['content'].required = False							
            self.fields['content'].label = "公告內容"
            self.fields['content'].widget.attrs['cols'] = 50
            self.fields['content'].widget.attrs['rows'] = 20        
            self.fields['title'].widget.attrs.update({'class' : 'form-control list-group-item-text'})      						
						
