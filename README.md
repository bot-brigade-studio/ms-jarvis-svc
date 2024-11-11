# FastAPI Microservice Boilerplate

A production-ready FastAPI boilerplate with async SQLAlchemy, structured for maintainability and scalability.

## Table of Contents

1. [Project Structure](#project-structure)
2. [Setup and Installation](#setup-and-installation)
3. [Database Configuration](#database-configuration)
4. [Creating New APIs](#creating-new-apis)
5. [Development Workflow](#development-workflow)
6. [Testing](#testing)
7. [Deployment](#deployment)

## Project Structure

```

├── app/
│ ├── **init**.py
│ ├── main.py # FastAPI application initialization
│ ├── api/ # API endpoints
│ │ ├── **init**.py
│ │ ├── v1/ # API version 1
│ │ │ ├── **init**.py
│ │ │ ├── endpoints/ # API route handlers
│ │ │ └── router.py # Router configuration
│ ├── core/ # Core functionality
│ │ ├── **init**.py
│ │ ├── config.py # Configuration settings
│ │ ├── security.py # Security utilities
│ │ ├── exceptions.py # Custom exceptions
│ │ └── repository.py # Base repository class
│ ├── db/ # Database configuration
│ │ ├── **init**.py
│ │ ├── base.py # SQLAlchemy base setup
│ │ └── session.py # Database session management
│ ├── models/ # SQLAlchemy models
│ ├── schemas/ # Pydantic models
│ ├── services/ # Business logic
│ ├── utils/ # Utility functions
│ └── repositories/ # Database queries
├── tests/ # Test files
├── alembic/ # Database migrations
├── docker/ # Docker configuration
├── scripts/ # Utility scripts
├── .env # Environment variables
├── .env.example # Example environment variables
├── requirements.txt # Project dependencies
└── README.md # Project documentation

```

## Setup and Installation

### Prerequisites

- Python 3.9+
- PostgreSQL
- Docker (optional)

### Local Development Setup

1. Clone the repository:

```bash
git clone <repository-url>
cd <project-name>
```

2. Create and activate virtual environment:

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:

```bash
pip install -r requirements.txt
```

4. Copy environment example and configure:

```bash
cp .env.example .env
# Edit .env with your configuration
```

5. Create database:

```sql
CREATE DATABASE your_database_name;
```

6. Run migrations:

```bash
alembic upgrade head
```

7. Start the application:

```bash
uvicorn app.main:app --reload
```

### Docker Setup

1. Build and run with Docker Compose:

```bash
docker-compose up --build
```

## Database Configuration

### Environment Variables

```env
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/dbname
```

### Database Migration Workflow

1. Initial setup:

```bash
alembic init alembic
```

2. Create new migration:

```bash
alembic revision --autogenerate -m "description of changes"
```

3. Apply migrations:

```bash
alembic upgrade head
```

4. Rollback migrations:

```bash
alembic downgrade -1  # Rollback one migration
alembic downgrade base  # Rollback all migrations
```

## Creating New APIs

### 1. Create Model (`app/models/example.py`)

```python
from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.sql import func
from app.db.base import Base

class ExampleModel(Base):
    __tablename__ = "example_table"

    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
```

### 2. Create Schema (`app/schemas/example.py`)

```python
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict

class ExampleBase(BaseModel):
    name: str

class ExampleCreate(ExampleBase):
    pass

class ExampleUpdate(BaseModel):
    name: Optional[str] = None

class Example(ExampleBase):
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
```

### 3. Create Repository (`app/repositories/example.py`)

```python
from app.core.repository import BaseRepository
from app.models.example import ExampleModel
from app.schemas.example import ExampleCreate, ExampleUpdate

class ExampleRepository(BaseRepository[ExampleModel, ExampleCreate, ExampleUpdate]):
    pass
```

### 4. Create Service (`app/services/example.py`)

```python
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.repositories.example import ExampleRepository
from app.models.example import ExampleModel
from app.schemas.example import ExampleCreate, ExampleUpdate

class ExampleService:
    def __init__(self, db: AsyncSession = Depends(get_db)):
        self.repository = ExampleRepository(ExampleModel, db)

    async def create(self, schema: ExampleCreate):
        return await self.repository.create(schema)

    async def get(self, id: int):
        return await self.repository.get(id)
```

### 5. Create API Endpoint (`app/api/v1/endpoints/example.py`)

```python
from fastapi import APIRouter, Depends
from app.services.example import ExampleService
from app.schemas.example import Example, ExampleCreate
from app.utils.response_handler import success_response

router = APIRouter()

@router.post("/", response_model=Example)
async def create_example(
    schema: ExampleCreate,
    service: ExampleService = Depends()
):
    item = await service.create(schema)
    return success_response(
        data=Example.model_validate(item),
        message="Example created successfully"
    )
```

### 6. Register Router (`app/api/v1/router.py`)

```python
from fastapi import APIRouter
from app.api.v1.endpoints import example

api_router = APIRouter()
api_router.include_router(example.router, prefix="/examples", tags=["examples"])
```

## Development Workflow

1. Create new feature branch:

```bash
git checkout -b feature/feature-name
```

2. Make changes and create migration if needed:

```bash
alembic revision --autogenerate -m "description"
```

3. Apply migrations:

```bash
alembic upgrade head
```

4. Run tests:

```bash
pytest
```

5. Commit changes:

```bash
git add .
git commit -m "feat: add feature description"
```

## Testing

### Running Tests

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_api/test_example.py

# Run with coverage report
pytest --cov=app tests/
```

### Example Test File

```python
# tests/test_api/test_example.py
import pytest
from httpx import AsyncClient
from app.main import app

@pytest.mark.asyncio
async def test_create_example():
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post(
            "/api/v1/examples/",
            json={"name": "test"}
        )
        assert response.status_code == 200
        assert response.json()["success"] is True
```

## Deployment

### Docker Deployment

1. Build image:

```bash
docker build -t app-name .
```

2. Run container:

```bash
docker run -p 8000:8000 app-name
```

### Environment Variables for Production

```env
PROJECT_NAME=YourProjectName
VERSION=1.0.0
API_V1_STR=/api/v1
DATABASE_URL=postgresql+asyncpg://user:password@host:5432/dbname
DEBUG=False
```

## API Documentation

- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## Contributing

1. Fork the repository
2. Create your feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## Best Practices

1. **Code Style**

   - Follow PEP 8
   - Use type hints
   - Document functions and classes

2. **API Design**

   - Use appropriate HTTP methods
   - Implement proper error handling
   - Follow REST principles

3. **Database**

   - Always create migrations for changes
   - Use appropriate indexes
   - Handle transactions properly

4. **Testing**
   - Write tests for new features
   - Maintain good test coverage
   - Use meaningful test names

## Common Issues and Solutions

1. **Migration Issues**

   ```bash
   # Reset migrations
   rm -rf alembic/versions/*
   alembic revision --autogenerate -m "initial"
   alembic upgrade head
   ```

2. **Database Connection Issues**

   - Check DATABASE_URL format
   - Verify database credentials
   - Ensure database server is running

3. **Import Errors**
   - Check Python path
   - Verify virtual environment activation
   - Check package installation

## Support

For support, please open an issue in the repository or contact the maintainers.

python scripts/create_module.py Category \
 -f "name:String:false:100" \
 -f "description:Text:true" \
 -f "is_active:Boolean:false" \
 -f "parent_id:Integer:true"
