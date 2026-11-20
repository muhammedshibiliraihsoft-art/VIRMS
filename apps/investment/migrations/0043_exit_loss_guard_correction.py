from importlib import import_module
from django.db import migrations


def replace_guards(apps, schema_editor):
    schema_editor.execute("DROP FUNCTION investor_exit_loss_application_complete() CASCADE; DROP FUNCTION investor_exit_loss_immutable() CASCADE; DROP FUNCTION investor_exit_loss_allocation_guard() CASCADE; DROP FUNCTION investor_exit_loss_application_guard() CASCADE;", params=None)
    import_module("apps.investment.migrations.0041_investorexitlossapplication_and_more").install_guards(apps, schema_editor)


def restore_guards(apps, schema_editor):
    import_module("apps.investment.migrations.0041_investorexitlossapplication_and_more").remove_guards(apps, schema_editor)


class Migration(migrations.Migration):
    dependencies = [
        ("investment", "0042_exit_loss_application_guards"),
        ("accounting", "0030_remove_accountingevent_acct_event_category_ck_and_more"),
    ]

    operations = [migrations.RunPython(replace_guards, restore_guards)]
