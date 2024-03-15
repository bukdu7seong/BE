from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("account", "0004_user_is_verified"),
    ]

    operations = [
        migrations.AlterField(
            model_name="emailverification",
            name="type",
            field=models.CharField(
                choices=[("PASS", "pass"), ("LOGIN", "login")],
                default="LOGIN",
                max_length=5,
            ),
        ),
    ]
