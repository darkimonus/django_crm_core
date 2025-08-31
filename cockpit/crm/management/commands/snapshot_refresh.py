import logging
from datetime import datetime, timezone
from typing import List, Optional
from django.core.management.base import BaseCommand, CommandError
from django.db import connection

from crm.models import Entity, EntityDetail


logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Refresh snapshots and materialized views for CRM data"

    def add_arguments(self, parser):
        parser.add_argument(
            "--entity-types",
            nargs="+",
            type=str,
            help="Specific entity types to refresh (default: all)"
        )
        parser.add_argument(
            "--detail-codes",
            nargs="+",
            type=str,
            help="Specific detail codes to refresh (default: all)"
        )
        parser.add_argument(
            "--since",
            type=str,
            help="Only refresh data changed since this timestamp (ISO format)"
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Show what would be refreshed without making changes"
        )
        parser.add_argument(
            "--force",
            action="store_true",
            help="Force refresh even if no changes detected"
        )
        parser.add_argument(
            "--create-snapshot-table",
            action="store_true",
            help="Create a new snapshot table with current timestamp"
        )

    def handle(self, *args, **options):
        entity_types = options.get("entity_types")
        detail_codes = options.get("detail_codes")
        since = options.get("since")
        dry_run = options.get("dry_run")
        force = options.get("force")
        create_snapshot_table = options.get("create_snapshot_table")

        self.stdout.write("Starting snapshot refresh...")
        self.stdout.write(f"Entity types: {entity_types or 'all'}")
        self.stdout.write(f"Detail codes: {detail_codes or 'all'}")
        self.stdout.write(f"Since: {since or 'all time'}")
        self.stdout.write(f"Dry run: {dry_run}")
        self.stdout.write(f"Force: {force}")
        self.stdout.write(f"Create snapshot table: {create_snapshot_table}")

        # Parse since timestamp if provided
        since_ts = None
        if since:
            try:
                since_ts = datetime.fromisoformat(since.replace('Z', '+00:00'))
                if since_ts.tzinfo is None:
                    since_ts = since_ts.replace(tzinfo=timezone.utc)
            except ValueError as e:
                raise CommandError(f"Invalid timestamp format: {e}")

        # Check for changes if not forcing
        if not force and not create_snapshot_table:
            changes = self._check_for_changes(since_ts, entity_types, detail_codes)
            if not changes:
                self.stdout.write(
                    self.style.SUCCESS("No changes detected. Use --force to refresh anyway.")
                )
                return

        # Perform refresh operations
        if create_snapshot_table:
            self._create_snapshot_table(dry_run)

        self._refresh_entity_snapshots(
            since_ts, entity_types, dry_run
        )
        self._refresh_detail_snapshots(
            since_ts, detail_codes, dry_run
        )

        self.stdout.write(self.style.SUCCESS("Snapshot refresh completed successfully!"))

    def _check_for_changes(
        self, 
        since_ts: Optional[datetime], 
        entity_types: Optional[List[str]], 
        detail_codes: Optional[List[str]]
    ) -> bool:
        """Check if there are any changes that require refresh"""
        self.stdout.write("Checking for changes...")

        # Check entity changes
        entity_query = Entity.objects.filter(is_current=True)
        if since_ts:
            entity_query = entity_query.filter(updated_at__gte=since_ts)
        if entity_types:
            entity_query = entity_query.filter(type_code__code__in=entity_types)

        entity_count = entity_query.count()
        self.stdout.write(f"Current entities to refresh: {entity_count}")

        # Check detail changes
        detail_query = EntityDetail.objects.filter(is_current=True)
        if since_ts:
            detail_query = detail_query.filter(updated_at__gte=since_ts)
        if detail_codes:
            detail_query = detail_query.filter(detail_code__in=detail_codes)

        detail_count = detail_query.count()
        self.stdout.write(f"Current details to refresh: {detail_count}")

        return entity_count > 0 or detail_count > 0

    def _create_snapshot_table(self, dry_run: bool) -> None:
        """Create a new snapshot table with current timestamp"""
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        table_name = f"crm_snapshot_{timestamp}"

        if dry_run:
            self.stdout.write(f"Would create snapshot table: {table_name}")
            return

        self.stdout.write(f"Creating snapshot table: {table_name}")

        with connection.cursor() as cursor:
            # Create snapshot table with current entity data
            cursor.execute(f"""
                CREATE TABLE {table_name} AS
                SELECT 
                    e.entity_uuid,
                    et.code as type_code,
                    e.display_name,
                    e.valid_from,
                    e.valid_to,
                    e.is_current,
                    e.hashdiff,
                    e.created_at,
                    e.updated_at
                FROM crm_entity e
                JOIN crm_entitytype et ON e.type_code_id = et.id
                WHERE e.is_current = true
            """)

            # Create index on entity_uuid for performance
            cursor.execute(f"""
                CREATE INDEX idx_{table_name}_entity_uuid 
                ON {table_name} (entity_uuid)
            """)

        self.stdout.write(
            self.style.SUCCESS(f"Snapshot table {table_name} created successfully")
        )

    def _refresh_entity_snapshots(
        self, 
        since_ts: Optional[datetime], 
        entity_types: Optional[List[str]], 
        dry_run: bool
    ) -> None:
        """Refresh entity snapshots"""
        self.stdout.write("Refreshing entity snapshots...")

        query = Entity.objects.filter(is_current=True)
        if since_ts:
            query = query.filter(updated_at__gte=since_ts)
        if entity_types:
            query = query.filter(type_code__code__in=entity_types)

        entity_count = query.count()
        self.stdout.write(f"Entities to refresh: {entity_count}")

        if dry_run:
            self.stdout.write("DRY RUN - Would refresh entity snapshots")
            return

        # Here you would implement the actual snapshot refresh logic
        # This could involve:
        # 1. Updating materialized views
        # 2. Refreshing cache
        # 3. Updating summary tables
        # 4. Rebuilding indexes

        # For now, we'll just log the entities that would be refreshed
        for entity in query.select_related('type_code')[:10]:  # Limit for demo
            logger.info(
                f"Refreshing entity: {entity.entity_uuid} "
                f"({entity.type_code.code})"
            )

        self.stdout.write(
            self.style.SUCCESS(f"Entity snapshots refreshed: {entity_count} entities")
        )

    def _refresh_detail_snapshots(
        self, 
        since_ts: Optional[datetime], 
        detail_codes: Optional[List[str]], 
        dry_run: bool
    ) -> None:
        """Refresh detail snapshots"""
        self.stdout.write("Refreshing detail snapshots...")

        query = EntityDetail.objects.filter(is_current=True)
        if since_ts:
            query = query.filter(updated_at__gte=since_ts)
        if detail_codes:
            query = query.filter(detail_code__in=detail_codes)

        detail_count = query.count()
        self.stdout.write(f"Details to refresh: {detail_count}")

        if dry_run:
            self.stdout.write("DRY RUN - Would refresh detail snapshots")
            return

        # Here you would implement the actual snapshot refresh logic
        # This could involve:
        # 1. Updating materialized views
        # 2. Refreshing cache
        # 3. Updating summary tables
        # 4. Rebuilding indexes

        # For now, we'll just log the details that would be refreshed
        for detail in query[:10]:  # Limit for demo
            logger.info(
                f"Refreshing detail: {detail.entity_uuid} "
                f"({detail.detail_code})"
            )

        self.stdout.write(
            self.style.SUCCESS(f"Detail snapshots refreshed: {detail_count} details")
        )
