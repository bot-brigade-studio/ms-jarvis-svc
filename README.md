# MS Jarvis Service

A FastAPI-based Python service for managing bot interactions, character management, chat functionality, and master data operations.

## Project Structure

```
app/
├── api/v1/                    # API version 1 routes and endpoints
│   ├── endpoints/            # API endpoint implementations
│   │   ├── bot.py           # Bot management endpoints
│   │   ├── character.py     # Character management endpoints
│   │   ├── chat.py         # Chat functionality endpoints
│   │   ├── file.py         # File handling endpoints
│   │   └── master.py       # Master data endpoints
│   └── router.py           # Main API router configuration
├── core/                    # Core application components
│   ├── config.py           # Application configuration
│   ├── exceptions.py       # Custom exception definitions
│   ├── logging.py         # Logging configuration
│   └── repository.py      # Base repository implementation
├── database/               # Database management
│   ├── seeders/           # Database seeder implementations
│   └── seeder_registry.py # Seeder registration and management
├── db/                     # Database connection and session management
├── middleware/             # Custom middleware components
│   ├── audit.py           # Audit logging middleware
│   ├── context.py         # Request context middleware
│   └── request_id.py      # Request ID tracking
├── models/                 # Database models and enums
├── repositories/           # Data access repositories
├── schemas/               # Pydantic schemas for data validation
├── services/              # Business logic services
└── utils/                 # Utility functions and helpers
```

## Key Components

### API Endpoints

- **Bot Management**: Handle bot creation, configuration, and management
- **Character Management**: Manage character-related operations
- **Chat Functionality**: Handle chat interactions and message processing
- **File Operations**: Manage file uploads and processing
- **Master Data**: Handle master data operations

### Core Features

- **Configuration Management**: Centralized application configuration
- **Custom Exceptions**: Specialized error handling
- **Logging**: Comprehensive logging system
- **Repository Pattern**: Base implementation for data access

### Database

- **Seeders**: Database seeding functionality
- **Models**: SQLAlchemy models for data structure
- **Session Management**: Database connection handling

### Middleware

- **Audit Logging**: Track and log system activities
- **Request Context**: Manage request-specific context
- **Request ID Tracking**: Unique identifier for request tracing

### Business Logic

- **Services**: Core business logic implementation
- **Repositories**: Data access layer
- **Schemas**: Data validation and serialization

### Utilities

- **DateTime Utils**: Date and time handling
- **Encryption**: Data encryption utilities
- **HTTP Client**: HTTP request handling
- **JSON Encoder**: Custom JSON encoding
- **Pagination**: Data pagination helpers
- **Response Handler**: Standardized response formatting
- **Transaction Management**: Database transaction handling

## Getting Started

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Set up environment variables:
   - Copy `.env.example` to `.env`
   - Configure required environment variables

3. Run database migrations:
   ```bash
   bash scripts/run_migrations.sh
   ```

4. Seed initial data:
   ```bash
   python scripts/seed.py
   ```

5. Start the service:
   ```bash
   bash scripts/start.sh
   ```

## API Documentation

Once the service is running, API documentation is available at:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## Development

### Adding New Migrations

```bash
bash scripts/create_migration.sh "migration_name"
```

### Project Organization

- Use appropriate folders for new features:
  - API endpoints go in `api/v1/endpoints/`
  - Database models in `models/`
  - Business logic in `services/`
  - Data access in `repositories/`
  - Request/response schemas in `schemas/`

### Code Style

- Follow PEP 8 guidelines
- Use type hints
- Document functions and classes
- Implement proper error handling
- Write unit tests for new features
