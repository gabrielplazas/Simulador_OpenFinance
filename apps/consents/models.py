import uuid
from datetime import timedelta
from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


class ConsentStatus(models.TextChoices):
    AWAITING_AUTHORISATION = 'AWAITING_AUTHORISATION', 'Aguardando Autorização'
    AUTHORISED = 'AUTHORISED', 'Autorizado'
    REJECTED = 'REJECTED', 'Rejeitado/Expirado'
    REVOKED = 'REVOKED', 'Revogado'


class Consent(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='consents',
        verbose_name='Usuário'
    )
    accounts = models.ManyToManyField('accounts.Account', blank=True, related_name='consents')
    rejection_reason = models.CharField(max_length=40, blank=True)
    logged_user = models.JSONField(default=dict, blank=True)
    consent_id = models.UUIDField(
        default=uuid.uuid4,
        unique=True,
        editable=False,
        verbose_name='ID do Consentimento (Open Finance)'
    )
    status = models.CharField(
        max_length=30,
        choices=ConsentStatus.choices,
        default=ConsentStatus.AWAITING_AUTHORISATION,
        verbose_name='Status do Consentimento'
    )
    # Lista de escopos de permissão solicitados, ex: ["ACCOUNTS_READ", "ACCOUNTS_BALANCES_READ"]
    permissions = models.JSONField(verbose_name='Permissões de Acesso')
    
    creation_date_time = models.DateTimeField(auto_now_add=True, verbose_name='Data/Hora de Criação')
    expiration_date_time = models.DateTimeField(null=True, blank=True, verbose_name='Data/Hora de Expiração')
    status_update_date_time = models.DateTimeField(auto_now=True, verbose_name='Última Atualização de Status')

    class Meta:
        verbose_name = 'Consentimento'
        verbose_name_plural = 'Consentimentos'
        ordering = ['-creation_date_time']

    def __str__(self):
        return f"Consentimento {self.consent_id} ({self.status}) - {self.user.username}"

    def reject(self, reason):
        self.status = ConsentStatus.REJECTED
        self.rejection_reason = reason
        self.save(update_fields=["status", "rejection_reason", "status_update_date_time"])

    def refresh_expiry(self):
        # Called while the consent row is locked for the v3 lifecycle.
        now = timezone.now()
        if self.status == ConsentStatus.AWAITING_AUTHORISATION and self.creation_date_time + timedelta(hours=1) <= now:
            self.reject("CONSENT_EXPIRED")
        elif self.status in (ConsentStatus.AWAITING_AUTHORISATION, ConsentStatus.AUTHORISED) and self.expiration_date_time and self.expiration_date_time <= now:
            self.reject("CONSENT_MAX_DATE_REACHED")

    @property
    def is_valid(self):
        """
        Retorna True se o consentimento está autorizado e ainda não expirou.
        """
        return self.status == ConsentStatus.AUTHORISED and (self.expiration_date_time is None or self.expiration_date_time > timezone.now())

class ConsentExtension(models.Model):
    consent = models.ForeignKey(Consent, on_delete=models.CASCADE, related_name="extensions")
    created_at = models.DateTimeField(auto_now_add=True)
    expiration_date_time = models.DateTimeField(null=True, blank=True)
