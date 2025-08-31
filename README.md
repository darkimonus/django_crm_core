# django_crm_core

## Architecture Overview

This project is a Django-based CRM core system designed with modularity and scalability in mind. The architecture consists of several key components:

- **cockpit/**: Contains the main Django project configuration and management scripts.
- **crm/**: The core CRM application, including models, views, APIs, services, and management commands.
- **test_data/**: Sample and test data files used for testing and development.

The system uses Django's ORM for data modeling and includes services for business logic, audit trails, and data ingestion.

## Quick Setup

To quickly set up the development environment and run the project, use the provided `Makefile`:

```bash
make build
make up
```

## Management Commands

For advanced operations and batch processing, refer to the `MANAGEMENT_COMMANDS.md` file. It contains detailed instructions on available management commands and how to use them.

## Example CURL Sequences

Below are example CURL commands to interact with the API endpoints:

### Example 1: Get list of entities
```bash
curl -X GET http://localhost:8000/api/entities/ -H "Accept: application/json"
```

### Example 2: Create a new entity
```bash
curl -X POST http://localhost:8000/api/entities/ \
  -H "Content-Type: application/json" \
  -d '{"name": "New Entity", "type": "customer"}'
```

### Example 3: Update an entity
```bash
curl -X PUT http://localhost:8000/api/entities/1/ \
  -H "Content-Type: application/json" \
  -d '{"name": "Updated Entity"}'
```

### Example 4: Delete an entity
```bash
curl -X DELETE http://localhost:8000/api/entities/1/
```

Replace `http://localhost:8000` with your actual server address and port if needed.

## Security

To test the API endpoints, you need to create a superuser account. You can do this using the management command:

```bash
make manage createsuperuser
```

After creating the superuser, obtain a JWT access token by authenticating at the endpoint:

```
POST /api/auth/token/
```

Use this token in the Authorization header as a Bearer token to access protected endpoints.

---

For more detailed API documentation, please refer to the codebase or .
