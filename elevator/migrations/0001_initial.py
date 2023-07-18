# Generated by Django 4.2.3 on 2023-07-18 16:32

from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="Elevator",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4,
                        editable=False,
                        primary_key=True,
                        serialize=False,
                    ),
                ),
                ("current_floor", models.IntegerField()),
                ("is_operational", models.BooleanField(default=True)),
                (
                    "direction",
                    models.CharField(choices=[(1, "up"), (2, "down")], max_length=255),
                ),
            ],
        ),
        migrations.CreateModel(
            name="ElevatorSystem",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4,
                        editable=False,
                        primary_key=True,
                        serialize=False,
                    ),
                ),
                ("name", models.CharField(max_length=255)),
                ("no_of_floors", models.IntegerField()),
                (
                    "elevators",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="elevator_system",
                        to="elevator.elevator",
                    ),
                ),
            ],
        ),
    ]
