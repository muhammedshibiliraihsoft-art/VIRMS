from django.contrib.postgres.operations import AddIndexConcurrently
from django.db import migrations, models


class Migration(migrations.Migration):
    atomic = False

    dependencies = [
        ("accounts", "0010_platform_identity_preflight"),
    ]

    operations = [
        AddIndexConcurrently(
            model_name="loginattempt",
            index=models.Index(
                fields=["updated_at", "id"], name="login_state_expiry_idx"
            ),
        ),
    ]
