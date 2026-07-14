from django.conf import settings
from django.core.exceptions import ValidationError
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from apps.payments.services.gateway import PaymentGatewayService


def _webhook_signature(request: HttpRequest) -> str | None:
    header = settings.PAYMENT_GATEWAY_WEBHOOK_SIGNATURE_HEADER
    return request.headers.get(header) or request.META.get(
        f"HTTP_{header.upper().replace('-', '_')}"
    )


@csrf_exempt
@require_POST
def payment_webhook(request: HttpRequest) -> HttpResponse:
    try:
        result = PaymentGatewayService.handle_webhook(
            payload=request.body,
            signature=_webhook_signature(request),
        )
    except ValidationError as exc:
        message = exc.messages[0] if exc.messages else str(exc)
        return JsonResponse({"error": message}, status=400)

    return JsonResponse(
        {
            "status": "duplicate" if result.duplicate else "ok",
            "intent_id": result.intent.pk if result.intent else None,
        },
    )
