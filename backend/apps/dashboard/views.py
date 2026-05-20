from django.shortcuts import render

from apps.accounts.permissions import staff_required


@staff_required
def panel_home(request):
    return render(request, "dashboard/panel.html")


@staff_required
def module_placeholder(request, module_name: str):
    return render(
        request,
        "dashboard/module_placeholder.html",
        {"module_name": module_name},
    )
