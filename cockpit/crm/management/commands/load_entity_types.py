import json
from pathlib import Path
from django.core.management.base import BaseCommand, CommandError
from crm.models import EntityType


class Command(BaseCommand):
    help = "Load EntityType records from a JSON file."

    def add_arguments(self, parser):
        parser.add_argument(
            "file_path",
            type=str,
            help="Path to JSON file containing entity types [{\"code\":..., \"title\":...}, ...]"
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Show what would be loaded without making changes."
        )

    def handle(self, *args, **options):
        file_path = Path(options["file_path"])
        dry_run = options["dry_run"]

        if not file_path.exists():
            raise CommandError(f"File not found: {file_path}")

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception as e:
            raise CommandError(f"Failed to read JSON: {e}")

        if not isinstance(data, list):
            raise CommandError("JSON must be an array of objects with 'code' and 'title'.")

        for entry in data:
            if not isinstance(entry, dict) or "code" not in entry or "title" not in entry:
                raise CommandError(f"Invalid entry: {entry}")

        self.stdout.write(f"Found {len(data)} entity types to load.")
        for entry in data:
            self.stdout.write(f"  {entry['code']}: {entry['title']}")

        if dry_run:
            self.stdout.write(self.style.WARNING("DRY RUN - No changes will be made."))
            return

        created, updated = 0, 0
        for entry in data:
            obj, is_created = EntityType.objects.update_or_create(
                code=entry["code"], defaults={"title": entry["title"]}
            )
            if is_created:
                created += 1
            else:
                updated += 1
        self.stdout.write(self.style.SUCCESS(f"Created: {created}, Updated: {updated}"))
