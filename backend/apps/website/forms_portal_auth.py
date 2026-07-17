from django import forms


class PortalLoginRequestForm(forms.Form):
    identifier = forms.CharField(
        label="Email lub numer rezerwacji",
        max_length=255,
        widget=forms.TextInput(
            attrs={
                "class": "w-full border border-gray-300 rounded px-3 py-2",
                "placeholder": "np. anna@example.com lub 12",
                "autocomplete": "username",
            }
        ),
    )


class PortalLoginVerifyForm(forms.Form):
    code = forms.CharField(
        label="Kod z emaila",
        max_length=6,
        min_length=6,
        widget=forms.TextInput(
            attrs={
                "class": (
                    "w-full border border-gray-300 rounded px-3 py-2 tracking-widest"
                ),
                "placeholder": "000000",
                "inputmode": "numeric",
                "autocomplete": "one-time-code",
            }
        ),
    )
