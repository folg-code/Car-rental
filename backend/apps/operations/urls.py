from django.urls import path

from apps.operations import views

app_name = "operations"

urlpatterns = [
    path("", views.operations_home, name="home"),
    path("wydania/", views.handover_queue, name="handover_queue"),
    path("zwroty/", views.return_queue, name="return_queue"),
    path("wydanie/<int:rental_id>/", views.handover_create, name="handover_create"),
    path(
        "wydanie/<int:rental_id>/podglad/",
        views.handover_detail,
        name="handover_detail",
    ),
    path("zwrot/<int:rental_id>/", views.return_create, name="return_create"),
    path(
        "zwrot/<int:rental_id>/podglad-doplat/",
        views.return_surcharge_preview,
        name="return_surcharge_preview",
    ),
    path(
        "zwrot/<int:rental_id>/podglad/",
        views.return_detail,
        name="return_detail",
    ),
]
