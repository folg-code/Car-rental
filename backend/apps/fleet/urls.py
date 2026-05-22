from django.urls import path

from apps.fleet import views

app_name = "fleet"

urlpatterns = [
    path("", views.car_list, name="car_list"),
    path("nowe/", views.car_create, name="car_create"),
    path("kategorie/", views.category_list, name="category_list"),
    path("kategorie/<int:pk>/edycja/", views.category_edit, name="category_edit"),
    path("<int:pk>/", views.car_detail, name="car_detail"),
    path("<int:pk>/edycja/", views.car_edit, name="car_edit"),
    path("<int:car_pk>/blokada/", views.block_create, name="block_create"),
    path(
        "<int:car_pk>/blokada/<int:block_pk>/usun/",
        views.block_delete,
        name="block_delete",
    ),
    path("<int:car_pk>/uszkodzenie/", views.damage_create, name="damage_create"),
]
