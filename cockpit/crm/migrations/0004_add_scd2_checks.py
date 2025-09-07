from django.db import migrations, models
from django.db.models import Q, F


class Migration(migrations.Migration):
    dependencies = [
        ("crm", "0003_exclude_coalesce"),
    ]

    operations = [
        # Entity SCD2 checks
        migrations.AddConstraint(
            model_name="entity",
            constraint=models.CheckConstraint(
                name="scd2_valid_bounds_chk",
                condition=Q(valid_from__lt=F("valid_to")) | Q(valid_to__isnull=True),
            ),
        ),
        migrations.AddConstraint(
            model_name="entity",
            constraint=models.CheckConstraint(
                name="scd2_current_to_null_chk",
                condition=(
                    Q(is_current=True, valid_to__isnull=True)
                    | Q(is_current=False, valid_to__isnull=False)
                ),
            ),
        ),
        # EntityDetail SCD2 checks
        migrations.AddConstraint(
            model_name="entitydetail",
            constraint=models.CheckConstraint(
                name="scd2_valid_bounds_chk",
                condition=Q(valid_from__lt=F("valid_to")) | Q(valid_to__isnull=True),
            ),
        ),
        migrations.AddConstraint(
            model_name="entitydetail",
            constraint=models.CheckConstraint(
                name="scd2_current_to_null_chk",
                condition=(
                    Q(is_current=True, valid_to__isnull=True)
                    | Q(is_current=False, valid_to__isnull=False)
                ),
            ),
        ),
    ]

