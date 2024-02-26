# Generated by Django 5.0.1 on 2024-02-22 06:29

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("account", "0007_rename_twofactor_user_is_2fa"),
    ]

    operations = [
        migrations.CreateModel(
            name="EmailVerification",
            fields=[
                (
                    "user",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE,
                        primary_key=True,
                        serialize=False,
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                ("code", models.CharField(max_length=6)),
                (
                    "type",
                    models.CharField(
                        choices=[("PASS", "pass"), ("LOGIN", "login")],
                        default="LOGIN",
                        max_length=5,
                    ),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True)),
            ],
        ),
    ]