from __future__ import annotations

import csv
import io
from datetime import datetime
from decimal import Decimal, InvalidOperation
from typing import Iterable, Tuple

from django import forms

from clients.models import Client


TAILWIND_INPUT_CLASSES = (
    "block w-full rounded-xl border border-slate-200 bg-white px-4 py-3 text-sm font-medium text-slate-700 "
    "shadow-sm transition focus:border-brand-500 focus:outline-none focus:ring-2 focus:ring-brand-200"
)

TAILWIND_SELECT_CLASSES = (
    "block w-full rounded-xl border border-slate-200 bg-white px-4 py-3 text-sm font-medium text-slate-700 "
    "shadow-sm transition focus:border-brand-500 focus:outline-none focus:ring-2 focus:ring-brand-200"
)

TAILWIND_FILE_CLASSES = (
    "block w-full text-sm font-medium text-slate-700 file:mr-4 file:rounded-xl file:border-0 "
    "file:bg-brand-50 file:px-5 file:py-3 file:text-sm file:font-semibold file:text-brand-700 hover:file:bg-brand-100"
)


class ClientForm(forms.ModelForm):
    due_date = forms.DateField(
        label="Data de vencimento",
        widget=forms.DateInput(attrs={"type": "date"}),
        required=True,
    )

    class Meta:
        model = Client
        fields = [
            "name",
            "phone",
            "email",
            "vehicle_type",
            "monthly_fee",
            "due_date",
            "payment_link",
            "status",
            "auto_messaging_enabled",
        ]
        widgets = {
            "monthly_fee": forms.NumberInput(attrs={"step": "0.01", "min": "0", "readonly": True}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Adicionar JavaScript para atualizar valor automaticamente quando veículo mudar
        if 'vehicle_type' in self.fields:
            self.fields['vehicle_type'].widget.attrs['onchange'] = 'updateMonthlyFee()'
            self.fields['monthly_fee'].help_text = "Valor definido automaticamente baseado no tipo de veículo"
        
        for field in self.fields.values():
            attrs = field.widget.attrs
            if isinstance(field.widget, forms.CheckboxInput):
                attrs["class"] = f"{attrs.get('class', '')} h-5 w-5 rounded border-slate-300 text-brand-500 focus:ring-brand-400".strip()
                continue
            if isinstance(field.widget, forms.Select):
                attrs["class"] = f"{attrs.get('class', '')} {TAILWIND_SELECT_CLASSES}".strip()
            else:
                attrs["class"] = f"{attrs.get('class', '')} {TAILWIND_INPUT_CLASSES}".strip()
            if "placeholder" not in attrs:
                attrs.setdefault("placeholder", field.label)


class ContactImportForm(forms.Form):
    file = forms.FileField(label="Arquivo CSV")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        attrs = self.fields["file"].widget.attrs
        attrs["class"] = f"{attrs.get('class', '')} {TAILWIND_FILE_CLASSES}".strip()

    def clean_file(self):
        uploaded = self.cleaned_data["file"]
        try:
            decoded = uploaded.read().decode("utf-8-sig")
        except UnicodeDecodeError as exc:  # pragma: no cover - validação simples
            raise forms.ValidationError("Não foi possível ler o arquivo. Utilize codificação UTF-8.") from exc

        reader = csv.DictReader(io.StringIO(decoded))
        headers = {header.strip().lower() for header in reader.fieldnames or []}
        required_headers = {"name", "phone", "monthly_fee", "due_date"}
        missing = required_headers - headers
        if missing:
            raise forms.ValidationError(
                f"Cabeçalhos obrigatórios ausentes: {', '.join(sorted(missing))}. "
                "Use colunas: name, phone, monthly_fee, due_date, email, payment_link, status."
            )

        rows: list[dict] = []
        errors: list[str] = []
        for idx, row in enumerate(reader, start=2):
            name = (row.get("name") or "").strip()
            phone = (row.get("phone") or "").strip()
            monthly_fee = (row.get("monthly_fee") or "").replace(",", ".").strip()
            due_date_raw = (row.get("due_date") or "").strip()

            if not name or not phone or not monthly_fee or not due_date_raw:
                errors.append(f"Linha {idx}: name, phone, monthly_fee e due_date são obrigatórios.")
                continue

            try:
                fee_value = Decimal(monthly_fee)
                if fee_value < 0:
                    raise InvalidOperation("Valor negativo")
            except (InvalidOperation, ValueError):
                errors.append(f"Linha {idx}: monthly_fee inválido ({monthly_fee}).")
                continue

            due_date = _parse_date(due_date_raw)
            if not due_date:
                errors.append(f"Linha {idx}: due_date inválido ({due_date_raw}). Use formato DD/MM/AAAA ou AAAA-MM-DD.")
                continue

            rows.append(
                {
                    "name": name,
                    "phone": phone,
                    "email": (row.get("email") or "").strip(),
                    "monthly_fee": fee_value,
                    "due_date": due_date.date(),
                    "payment_link": (row.get("payment_link") or "").strip(),
                    "status": (row.get("status") or "").strip() or Client.Status.ACTIVE,
                }
            )

        if errors:
            raise forms.ValidationError(errors)

        uploaded.seek(0)
        uploaded.parsed_rows = rows  # type: ignore[attr-defined]
        return uploaded


def _parse_date(value: str) -> datetime | None:
    value = value.strip()
    patterns: Iterable[Tuple[str, bool]] = [
        ("%d/%m/%Y", True),
        ("%Y-%m-%d", True),
        ("%d-%m-%Y", True),
    ]
    for pattern, _ in patterns:
        try:
            return datetime.strptime(value, pattern)
        except ValueError:
            continue
    return None


