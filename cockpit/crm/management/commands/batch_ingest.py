import json
import logging
from pathlib import Path
from typing import Dict, Any, List
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from crm.services.ingest import ingest_entity, ingest_detail


logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Batch ingest entities and details from JSON/JSONL files"

    def add_arguments(self, parser):
        parser.add_argument(
            "file_path",
            type=str,
            help="Path to JSON or JSONL file containing ingest data"
        )
        parser.add_argument(
            "--actor",
            type=str,
            default="batch_ingest@management",
            help="Actor name for audit trail "
                 "(default: batch_ingest@management)"
        )
        parser.add_argument(
            "--correlation-id",
            type=str,
            help="Correlation ID for audit trail (defaults to filename)"
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Process data without committing to database"
        )
        parser.add_argument(
            "--batch-size",
            type=int,
            default=1000,
            help="Number of records to process in each batch (default: 1000)"
        )
        parser.add_argument(
            "--continue-on-error",
            action="store_true",
            help="Continue processing even if individual records fail"
        )

    def handle(self, *args, **options):
        file_path = Path(options["file_path"])
        actor = options["actor"]
        correlation_id = options["correlation_id"] or file_path.name
        dry_run = options["dry_run"]
        batch_size = options["batch_size"]
        continue_on_error = options["continue_on_error"]

        if not file_path.exists():
            raise CommandError(f"File not found: {file_path}")

        self.stdout.write(f"Processing file: {file_path}")
        self.stdout.write(f"Actor: {actor}")
        self.stdout.write(f"Correlation ID: {correlation_id}")
        self.stdout.write(f"Dry run: {dry_run}")
        self.stdout.write(f"Batch size: {batch_size}")
        self.stdout.write(f"Continue on error: {continue_on_error}")

        # Determine file format and process
        if file_path.suffix.lower() == ".jsonl":
            records = self._read_jsonl(file_path)
        else:
            records = self._read_json(file_path)

        if not records:
            self.stdout.write(self.style.WARNING("No records found in file"))
            return

        self.stdout.write(f"Found {len(records)} records to process")

        # Process records
        stats = {
            "total": len(records),
            "entities_created": 0,
            "entities_updated": 0,
            "entities_noop": 0,
            "details_created": 0,
            "details_updated": 0,
            "details_noop": 0,
            "errors": 0,
        }

        for i in range(0, len(records), batch_size):
            batch = records[i:i + batch_size]
            batch_stats = self._process_batch(
                batch, actor, correlation_id, dry_run, continue_on_error
            )
            
            # Update overall stats
            for key in stats:
                if key in batch_stats:
                    stats[key] += batch_stats[key]

            batch_num = i//batch_size + 1
            total_batches = (len(records) + batch_size - 1)//batch_size
            entity_count = (
                    batch_stats['entities_created'] +
                    batch_stats['entities_updated'] +
                    batch_stats['entities_noop']
            )
            detail_count = (
                    batch_stats['details_created'] +
                    batch_stats['details_updated'] +
                    batch_stats['details_noop']
            )
            
            self.stdout.write(
                f"Processed batch {batch_num}/{total_batches}: "
                f"{entity_count} entities, {detail_count} details, "
                f"{batch_stats['errors']} errors"
            )

        # Final summary
        self.stdout.write("\n" + "="*50)
        self.stdout.write("FINAL SUMMARY")
        self.stdout.write("="*50)
        self.stdout.write(f"Total records processed: {stats['total']}")
        self.stdout.write(f"Entities - Created: {stats['entities_created']},"
                          f" Updated: {stats['entities_updated']}, No-op: {stats['entities_noop']}")
        self.stdout.write(f"Details - Created: {stats['details_created']},"
                          f" Updated: {stats['details_updated']}, No-op: {stats['details_noop']}")
        self.stdout.write(f"Errors: {stats['errors']}")

        if dry_run:
            self.stdout.write(self.style.WARNING("\nDRY RUN - No changes were made to the database"))

    def _read_json(self, file_path: Path) -> List[Dict[str, Any]]:
        """
        Read JSON file containing array of records
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            if isinstance(data, list):
                return data
            elif isinstance(data, dict) and "records" in data:
                return data["records"]
            else:
                raise CommandError("JSON file must contain an array of records or a dict with 'records' key")
        except json.JSONDecodeError as e:
            raise CommandError(f"Invalid JSON in file: {e}")

    def _read_jsonl(self, file_path: Path) -> List[Dict[str, Any]]:
        """Read JSONL file (one JSON object per line)"""
        records = []
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                for line_num, line in enumerate(f, 1):
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        record = json.loads(line)
                        records.append(record)
                    except json.JSONDecodeError as e:
                        raise CommandError(f"Invalid JSON on line {line_num}: {e}")
        except Exception as e:
            raise CommandError(f"Error reading JSONL file: {e}")
        
        return records

    def _process_batch(
        self, 
        batch: List[Dict[str, Any]], 
        actor: str, 
        correlation_id: str, 
        dry_run: bool,
        continue_on_error: bool
    ) -> Dict[str, int]:
        """Process a batch of records"""
        stats = {
            "entities_created": 0,
            "entities_updated": 0,
            "entities_noop": 0,
            "details_created": 0,
            "details_updated": 0,
            "details_noop": 0,
            "errors": 0,
        }

        if dry_run:
            # In dry run mode, just validate the records
            for record in batch:
                try:
                    self._validate_record(record)
                    if record.get("type") == "entity":
                        stats["entities_noop"] += 1
                    elif record.get("type") == "detail":
                        stats["details_noop"] += 1
                except Exception as e:
                    stats["errors"] += 1
                    if not continue_on_error:
                        raise e
                    logger.error(f"Record validation error: {e}")
            return stats

        # Process records in transaction
        try:
            with transaction.atomic():
                for record in batch:
                    try:
                        result = self._process_record(record, actor, correlation_id)
                        if result["type"] == "entity":
                            if result["status"] == "created":
                                stats["entities_created"] += 1
                            elif result["status"] == "updated":
                                stats["entities_updated"] += 1
                            else:  # noop
                                stats["entities_noop"] += 1
                        elif result["type"] == "detail":
                            if result["status"] == "created":
                                stats["details_created"] += 1
                            elif result["status"] == "updated":
                                stats["details_updated"] += 1
                            else:  # noop
                                stats["details_noop"] += 1
                    except Exception as e:
                        stats["errors"] += 1
                        if not continue_on_error:
                            raise e
                        logger.error(f"Record processing error: {e}")
        except Exception as e:
            if not continue_on_error:
                raise CommandError(f"Batch processing failed: {e}")
            logger.error(f"Batch processing error: {e}")

        return stats

    def _validate_record(self, record: Dict[str, Any]) -> None:
        """Validate a record structure"""
        if not isinstance(record, dict):
            raise ValueError("Record must be a dictionary")

        record_type = record.get("type")
        if record_type not in ["entity", "detail"]:
            raise ValueError("Record must have 'type' field with value 'entity' or 'detail'")

        if record_type == "entity":
            required_fields = ["entity_uuid", "type_code", "display_name", "change_ts"]
        else:  # detail
            required_fields = ["entity_uuid", "detail_code", "value_kind", "change_ts"]

        missing_fields = [field for field in required_fields if field not in record]
        if missing_fields:
            raise ValueError(f"Missing required fields: {missing_fields}")

    def _process_record(
        self, 
        record: Dict[str, Any], 
        actor: str, 
        correlation_id: str
    ) -> Dict[str, Any]:
        """Process a single record"""
        self._validate_record(record)
        
        record_type = record["type"]
        
        # Add actor and correlation_id to payload
        payload = record.copy()
        payload["actor"] = actor
        payload["correlation_id"] = correlation_id
        
        if record_type == "entity":
            result = ingest_entity(payload)
            return {
                "type": "entity",
                "status": result.status,
                "entity_uuid": str(result.instance.entity_uuid)
            }
        else:  # detail
            result = ingest_detail(payload)
            return {
                "type": "detail", 
                "status": result.status,
                "entity_uuid": str(result.instance.entity_uuid),
                "detail_code": result.instance.detail_code
            }
