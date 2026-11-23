from django.db import migrations, models


def bind_existing_accounts(apps, schema_editor):
    Consent = apps.get_model("consents", "Consent")
    Account = apps.get_model("accounts", "Account")
    for consent in Consent.objects.filter(status="AUTHORISED").iterator():
        consent.accounts.set(Account.objects.filter(user_id=consent.user_id))


class Migration(migrations.Migration):
    dependencies = [("accounts", "0002_alter_account_company_cnpj_and_more"), ("consents", "0001_initial")]
    operations = [
        migrations.AddField("consent", "accounts", models.ManyToManyField(blank=True, related_name="consents", to="accounts.account")),
        migrations.AddField("consent", "logged_user", models.JSONField(blank=True, default=dict)),
        migrations.AddField("consent", "rejection_reason", models.CharField(blank=True, max_length=40)),
        migrations.AlterField("consent", "expiration_date_time", models.DateTimeField(blank=True, null=True, verbose_name="Data/Hora de Expiração")),
        migrations.CreateModel(name="ConsentExtension", fields=[
            ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
            ("created_at", models.DateTimeField(auto_now_add=True)),
            ("expiration_date_time", models.DateTimeField(blank=True, null=True)),
            ("consent", models.ForeignKey(on_delete=models.CASCADE, related_name="extensions", to="consents.consent")),
        ]),
        migrations.RunPython(bind_existing_accounts, migrations.RunPython.noop),
    ]
