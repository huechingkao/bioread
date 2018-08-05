from django.urls import path
from django.contrib.auth.decorators import login_required
from . import views

urlpatterns = [
    path('', login_required(views.root)),
    path('annotations', login_required(views.annotations)),
    path('annotations/<int:annotation_id>', login_required(views.single_annotation)),
    path('search', login_required(views.search)),
]