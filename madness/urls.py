"""
Copyright 2016, Paul Powell, All rights reserved.
"""
from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.urls import path, re_path

from tournament.views import *

urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/login/', LoginView.as_view(), name='login'),
    path('accounts/logout/', auth_views.LogoutView.as_view(next_page='/'), name='logout'),
    path('accounts/register/', RegisterView.as_view(), name='register'),
    path('', home_page, name='home-page'),
    path('tournament/generate/', run_tournament, name='run-tournament'),
    re_path(r'^tournament/generate/(?P<option_id>[0-9]+)/$', run_tournament_options, name='run-tournament-options'),
    path('tournament/options/', create_with_options, name='create-with-options'),
    re_path(r'^tournament/options/(?P<year>[0-9]{4})/$', create_with_options_year, name='create-with-options-year'),
    re_path(r'^tournament/(?P<result_id>[0-9]+)/$', view_result, name='view-result'),
    re_path(r'^tournament/(?P<result_id>[0-9]+)/save$', save_result, name='save-result'),
    re_path(r'^tournament/(?P<result_id>[0-9]+)/remove$', remove_result, name='remove-result'),
    re_path(r'^tournament/(?P<result_id>[0-9]+)/full$', view_full_result, name='view-full-result'),
    re_path(r'^tournament/(?P<result_id>[0-9]+)/print$', print_bracket, name='print-bracket'),
    re_path(r'^tournament/brackets', my_brackets, name='my-brackets'),
    re_path(r'^tournament/help/introduction', help_introduction, name='help-introduction'),
    re_path(r'^tournament/help/create', help_create, name='help-create'),
    re_path(r'^tournament/help/save', help_save, name='help-save'),
    re_path(r'^tournament/help/show', help_show, name='help-show'),
    re_path(r'^tournament/help/year', help_year, name='help-year'),
]
