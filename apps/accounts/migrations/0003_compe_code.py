from django.core.validators import RegexValidator
from django.db import migrations, models


def fill_seed_codes(apps, schema_editor):
    accounts = apps.get_model("accounts", "Account")
    for cnpj, code in {"60701190000104": "341", "60746948000112": "237", "00000000000191": "001",
                       "18236120000158": "260", "00360305000104": "104"}.items():
        accounts.objects.filter(company_cnpj=cnpj).update(compe_code=code)


class Migration(migrations.Migration):
    dependencies = [("accounts", "0002_alter_account_company_cnpj_and_more")]
    operations = [
        migrations.AddField("account", "compe_code", models.CharField(default="000", max_length=3, validators=[RegexValidator(r"^[0-9]{3}$")])),
        migrations.RunPython(fill_seed_codes, migrations.RunPython.noop),
    ]
