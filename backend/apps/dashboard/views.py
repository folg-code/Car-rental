from django.shortcuts import render

from apps.accounts.permissions import staff_required


@staff_required
def panel_home(request):
    return render(
        request,
        "dashboard/panel.html",
        {"user": request.user},
    )
