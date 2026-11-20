from importlib import import_module
from django.db import migrations


def install(apps, schema_editor):
    import_module("apps.investment.migrations.0041_investorexitlossapplication_and_more").install_guards(apps, schema_editor)


def remove(apps, schema_editor):
    import_module("apps.investment.migrations.0041_investorexitlossapplication_and_more").remove_guards(apps, schema_editor)


class Migration(migrations.Migration):
    dependencies = [
        ("investment", "0041_investorexitlossapplication_and_more"),
        ("accounting", "0028_accountingsourcelink_investor_exit_loss_application_and_more"),
    ]

    operations = [migrations.RunPython(install, remove)]
