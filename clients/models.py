from datetime import date

from django.db import models


class Client(models.Model):
    class Status(models.TextChoices):
        ACTIVE = "active", "Ativo"
        DELINQUENT = "delinquent", "Inadimplente"
        SETTLED = "settled", "Quitado"
    
    class VehicleType(models.TextChoices):
        MOTO = "moto", "Moto"
        CARRO = "carro", "Carro"

    name = models.CharField("Nome", max_length=100)
    phone = models.CharField("Telefone", max_length=20)
    email = models.EmailField("E-mail", blank=True)
    vehicle_type = models.CharField(
        "Tipo de Veículo",
        max_length=10,
        choices=VehicleType.choices,
        default=VehicleType.MOTO,
        help_text="Tipo de veículo do cliente (Moto = R$ 49,99, Carro = R$ 59,99)",
    )
    monthly_fee = models.DecimalField("Mensalidade", max_digits=10, decimal_places=2)
    due_date = models.DateField(
        "Data de vencimento",
        default=date.today,
        help_text="Próxima data de cobrança.",
    )
    due_day = models.PositiveSmallIntegerField("Dia de vencimento", default=5, editable=False)
    payment_link = models.URLField("Link de pagamento", blank=True)
    status = models.CharField(
        "Status",
        max_length=20,
        choices=Status.choices,
        default=Status.ACTIVE,
    )
    auto_messaging_enabled = models.BooleanField(
        "Envio automático habilitado",
        default=True,
        help_text="Quando ativo, o sistema enviará mensagens automáticas nas datas configuradas.",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("name",)
        verbose_name = "Cliente"
        verbose_name_plural = "Clientes"

    def __str__(self) -> str:
        return self.name

    @property
    def formatted_phone(self) -> str:
        return "".join(filter(str.isdigit, self.phone or ""))

    def save(self, *args, **kwargs):
        if self.due_date:
            self.due_day = self.due_date.day
        
        # Definir valor automaticamente baseado no tipo de veículo
        # Se for novo cliente ou se o tipo de veículo mudou
        if not self.pk:
            # Novo cliente - definir valor automaticamente
            if self.vehicle_type == self.VehicleType.MOTO:
                self.monthly_fee = 49.99
            elif self.vehicle_type == self.VehicleType.CARRO:
                self.monthly_fee = 59.99
        else:
            # Cliente existente - verificar se o tipo de veículo mudou
            old_instance = Client.objects.get(pk=self.pk)
            if old_instance.vehicle_type != self.vehicle_type:
                # Tipo mudou - atualizar valor automaticamente
                if self.vehicle_type == self.VehicleType.MOTO:
                    self.monthly_fee = 49.99
                elif self.vehicle_type == self.VehicleType.CARRO:
                    self.monthly_fee = 59.99
        
        super().save(*args, **kwargs)
