from django.contrib import messages
from django.core.exceptions import ValidationError
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render

from apps.accounts.permissions import owner_or_manager_required
from apps.pricing.forms import (
    DailyRateForm,
    ExtraServiceForm,
    PriceListForm,
    PricingRuleForm,
)
from apps.pricing.models import DailyRate, ExtraService, PriceList, PricingRule
from apps.pricing.selectors.price_list import get_price_list_by_id, list_price_lists
from apps.pricing.services.price_list import PriceListService


@owner_or_manager_required
def price_list_list(request: HttpRequest) -> HttpResponse:
    return render(
        request,
        "pricing/price_list_list.html",
        {"price_lists": list_price_lists()},
    )


@owner_or_manager_required
def price_list_create(request: HttpRequest) -> HttpResponse:
    form = PriceListForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        price_list = form.save(commit=False)
        PriceListService.save_price_list(price_list)
        messages.success(request, f"Utworzono cennik {price_list.name}.")
        return redirect("pricing:price_list_detail", pk=price_list.pk)
    return render(
        request,
        "pricing/price_list_form.html",
        {"form": form, "title": "Nowy cennik"},
    )


@owner_or_manager_required
def price_list_edit(request: HttpRequest, pk: int) -> HttpResponse:
    price_list = get_object_or_404(PriceList, pk=pk)
    form = PriceListForm(request.POST or None, instance=price_list)
    if request.method == "POST" and form.is_valid():
        updated = form.save(commit=False)
        PriceListService.save_price_list(updated)
        messages.success(request, "Zapisano cennik.")
        return redirect("pricing:price_list_detail", pk=price_list.pk)
    return render(
        request,
        "pricing/price_list_form.html",
        {
            "form": form,
            "title": f"Edycja — {price_list.name}",
            "price_list": price_list,
        },
    )


@owner_or_manager_required
def price_list_detail(request: HttpRequest, pk: int) -> HttpResponse:
    price_list = get_price_list_by_id(pk)
    if price_list is None:
        messages.error(request, "Nie znaleziono cennika.")
        return redirect("pricing:price_list_list")

    daily_rate_form = DailyRateForm(request.POST or None, prefix="rate")
    rule_form = PricingRuleForm(request.POST or None, prefix="rule")
    extra_form = ExtraServiceForm(request.POST or None, prefix="extra")

    if request.method == "POST":
        action = request.POST.get("action", "")
        if action == "add_rate" and daily_rate_form.is_valid():
            try:
                PriceListService.add_daily_rate(
                    price_list=price_list,
                    category_id=daily_rate_form.cleaned_data["category"].pk,
                    amount=daily_rate_form.cleaned_data["amount"],
                )
                messages.success(request, "Dodano stawke dzienna.")
            except ValidationError as exc:
                messages.error(request, exc.messages[0] if exc.messages else str(exc))
            return redirect("pricing:price_list_detail", pk=pk)

        if action == "add_rule" and rule_form.is_valid():
            rule = rule_form.save(commit=False)
            rule.price_list = price_list
            try:
                rule.save()
                messages.success(request, "Dodano regule cenowa.")
            except ValidationError as exc:
                messages.error(request, exc.messages[0] if exc.messages else str(exc))
            return redirect("pricing:price_list_detail", pk=pk)

        if action == "add_extra" and extra_form.is_valid():
            extra = extra_form.save(commit=False)
            extra.price_list = price_list
            try:
                extra.save()
                messages.success(request, "Dodano usluge dodatkowa.")
            except ValidationError as exc:
                messages.error(request, exc.messages[0] if exc.messages else str(exc))
            return redirect("pricing:price_list_detail", pk=pk)

        if action == "delete_rate":
            rate = get_object_or_404(
                DailyRate, pk=request.POST.get("item_id"), price_list=price_list
            )
            rate.delete()
            messages.success(request, "Usunieto stawke.")
            return redirect("pricing:price_list_detail", pk=pk)

        if action == "delete_rule":
            rule = get_object_or_404(
                PricingRule, pk=request.POST.get("item_id"), price_list=price_list
            )
            rule.delete()
            messages.success(request, "Usunieto regule.")
            return redirect("pricing:price_list_detail", pk=pk)

        if action == "delete_extra":
            extra = get_object_or_404(
                ExtraService, pk=request.POST.get("item_id"), price_list=price_list
            )
            extra.delete()
            messages.success(request, "Usunieto usluge.")
            return redirect("pricing:price_list_detail", pk=pk)

    return render(
        request,
        "pricing/price_list_detail.html",
        {
            "price_list": price_list,
            "daily_rate_form": daily_rate_form,
            "rule_form": rule_form,
            "extra_form": extra_form,
        },
    )
