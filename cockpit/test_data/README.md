# Test Data for Management Commands

This directory contains various test data files for testing the `batch_ingest` and `snapshot_refresh` management commands.

## File Overview

### 📁 **Basic Test Files**

#### `sample_entities.json`
- **Purpose**: Basic entity testing
- **Content**: 5 entities (3 PERSON, 2 COMPANY)
- **Records**: 5
- **Use Case**: Testing basic entity ingestion

#### `sample_details.json`
- **Purpose**: Basic detail testing with all value types
- **Content**: 15 details covering all value kinds (TEXT, NUM, TS, BOOL, JSON)
- **Records**: 15
- **Use Case**: Testing detail ingestion with various data types

### 📁 **Advanced Test Files**

#### `combined_data.json`
- **Purpose**: Mixed entity and detail data
- **Content**: 2 entities + 5 details in single file
- **Records**: 7
- **Use Case**: Testing mixed data ingestion in one file

#### `large_dataset.jsonl`
- **Purpose**: Performance and batch processing testing
- **Content**: 10 entities + 20 details in JSONL format
- **Records**: 30
- **Use Case**: Testing batch processing, performance, and JSONL format

### 📁 **Error Testing Files**

#### `invalid_data.json`
- **Purpose**: Error handling testing
- **Content**: Various invalid records
- **Records**: 5 (all invalid)
- **Use Case**: Testing error handling and validation

#### `update_scenarios.json`
- **Purpose**: SCD2 update behavior testing
- **Content**: Same entity with updates over time
- **Records**: 8
- **Use Case**: Testing SCD2 versioning and updates

## Usage Examples

### Basic Testing

```bash
# Test basic entity ingestion
python manage.py batch_ingest test_data/sample_entities.json --dry-run

# Test basic detail ingestion
python manage.py batch_ingest test_data/sample_details.json --dry-run

# Test combined data
python manage.py batch_ingest test_data/combined_data.json --dry-run
```

### Performance Testing

```bash
# Test large dataset with custom batch size
python manage.py batch_ingest test_data/large_dataset.jsonl --batch-size 5 --dry-run

# Test performance with different batch sizes
python manage.py batch_ingest test_data/large_dataset.jsonl --batch-size 10
python manage.py batch_ingest test_data/large_dataset.jsonl --batch-size 20
```

### Error Handling Testing

```bash
# Test error handling (should fail)
python manage.py batch_ingest test_data/invalid_data.json

# Test error handling with continue on error
python manage.py batch_ingest test_data/invalid_data.json --continue-on-error
```

### SCD2 Update Testing

```bash
# Test SCD2 updates
python manage.py batch_ingest test_data/update_scenarios.json --dry-run

# Test actual updates
python manage.py batch_ingest test_data/update_scenarios.json
```

### Snapshot Refresh Testing

```bash
# Test snapshot refresh after data ingestion
python manage.py snapshot_refresh --dry-run

# Test selective refresh
python manage.py snapshot_refresh --entity-types PERSON --dry-run

# Test time-based refresh
python manage.py snapshot_refresh --since "2025-01-19T00:00:00Z" --dry-run
```

## Data Types Covered

### Entity Types
- `PERSON`: Individual people
- `COMPANY`: Business entities

### Detail Value Kinds
- `TEXT`: String values (emails, names, etc.)
- `NUM`: Numeric values (ages, salaries, counts)
- `TS`: Timestamp values (dates, times)
- `BOOL`: Boolean values (true/false flags)
- `JSON`: Complex structured data

### Detail Codes
- `EMAIL`: Contact email addresses
- `PHONE`: Phone numbers
- `WEBSITE`: Company websites
- `AGE`: Person ages
- `SALARY`: Employee salaries
- `EMPLOYEE_COUNT`: Company employee counts
- `BIRTH_DATE`: Person birth dates
- `FOUNDED_DATE`: Company founding dates
- `IS_ACTIVE`: Active status flags
- `IS_PUBLIC`: Public company flags
- `DEPARTMENT`: Employee departments
- `ROLE`: Job roles
- `INDUSTRY`: Company industries
- `SECTOR`: Business sectors
- `MARKET_CAP`: Company market capitalization
- `SCORE`: Performance scores
- `REVENUE`: Company revenue
- `PREFERENCES`: User preferences (JSON)
- `FUNDING_ROUNDS`: Company funding data (JSON)
- `METRICS`: Business metrics (JSON)

## Test Scenarios

### 1. **Basic Functionality**
- ✅ Entity creation
- ✅ Detail creation
- ✅ All value types
- ✅ Mixed data in single file

### 2. **Performance Testing**
- ✅ Large dataset processing
- ✅ JSONL format
- ✅ Different batch sizes
- ✅ Memory efficiency

### 3. **Error Handling**
- ✅ Invalid entity types
- ✅ Invalid value kinds
- ✅ Missing required fields
- ✅ Invalid timestamps
- ✅ Unknown record types

### 4. **SCD2 Behavior**
- ✅ Initial entity creation
- ✅ Entity updates
- ✅ Detail updates
- ✅ Idempotent operations
- ✅ Version history

### 5. **Audit Trail**
- ✅ Actor tracking
- ✅ Correlation ID tracking
- ✅ Timestamp handling
- ✅ Change history

## File Formats

### JSON Format
- Standard JSON array of objects
- Good for smaller datasets
- Easy to read and edit

### JSONL Format
- One JSON object per line
- Better for large datasets
- Memory efficient
- Streaming friendly

## Correlation IDs

Each test file uses specific correlation IDs for tracking:
- `test_batch_001`: Basic sample data
- `test_combined_001`: Combined data
- `large_batch_001`: Large dataset
- `invalid_test_001`: Invalid data
- `update_test_001/002/003`: Update scenarios

## Expected Results

### Successful Ingestion
- Entities created/updated
- Details created/updated
- Audit trail recorded
- Statistics reported

### Error Scenarios
- Invalid data rejected
- Error messages logged
- Processing continues (with `--continue-on-error`)
- Statistics include error counts

### SCD2 Updates
- New versions created
- Old versions closed
- Hashdiff changes tracked
- Audit trail maintained

## Tips for Testing

1. **Always use `--dry-run` first** to validate data
2. **Start with small files** before testing large datasets
3. **Monitor database performance** during large imports
4. **Check audit logs** for detailed change tracking
5. **Use correlation IDs** to track specific test runs
6. **Test error scenarios** to ensure robust error handling
7. **Verify SCD2 behavior** with update scenarios
