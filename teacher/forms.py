# -*- coding: utf-8 -*-
from django import forms

#上傳檔案
class UploadFileForm(forms.Form):
    file = forms.FileField()
