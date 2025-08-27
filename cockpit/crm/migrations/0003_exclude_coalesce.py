from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("crm", "0002_entities_and_audit")
    ]
    operations = [
        migrations.RunSQL(
            sql=r"""
            ALTER TABLE entity
              DROP CONSTRAINT IF EXISTS entity_no_overlap;
            ALTER TABLE entity
              ADD CONSTRAINT entity_no_overlap
              EXCLUDE USING gist (
                entity_uuid WITH =,
                tstzrange(valid_from, COALESCE(valid_to, 'infinity'::timestamptz)) WITH &&
              );

            ALTER TABLE entity_detail
              DROP CONSTRAINT IF EXISTS edetail_no_overlap;
            ALTER TABLE entity_detail
              ADD CONSTRAINT edetail_no_overlap
              EXCLUDE USING gist (
                entity_uuid  WITH =,
                detail_code WITH =,
                tstzrange(valid_from, COALESCE(valid_to, 'infinity'::timestamptz)) WITH &&
              );
            """,
            reverse_sql=r"""
            ALTER TABLE entity DROP CONSTRAINT IF EXISTS entity_no_overlap;
            ALTER TABLE entity_detail DROP CONSTRAINT IF EXISTS edetail_no_overlap;
            """,
        ),
    ]