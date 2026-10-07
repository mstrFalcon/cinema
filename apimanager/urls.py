from django.urls import path
from . import views

urlpatterns = [
    path('', views.get_films, name="get_films"),
    path('films/<int:id>/', views.film_detail, name="film_detail"),
    path('persons', views.get_persons, name="get_persons"),
    path('persons/<int:id>/', views.person_detail, name="person_detail"),
    path('api/seasons/<int:season_id>/episodes/', views.get_episodes, name='get_episodes'),
]