import os
import re
from typing import Dict, List, Optional, Any
import click
from jinja2 import Environment, FileSystemLoader

# SQLAlchemy to Pydantic type mapping
SQL_TO_PYDANTIC_TYPES = {
    # String types
    'String': 'str',
    'Text': 'str',
    'Unicode': 'str',
    'UnicodeText': 'str',
    'VARCHAR': 'str',
    'CHAR': 'str',
    
    # Numeric types
    'Integer': 'int',
    'BigInteger': 'int',
    'SmallInteger': 'int',
    'Float': 'float',
    'Numeric': 'Decimal',
    'DECIMAL': 'Decimal',
    
    # Boolean type
    'Boolean': 'bool',
    
    # DateTime types
    'DateTime': 'datetime',
    'Date': 'date',
    'Time': 'time',
    'TIMESTAMP': 'datetime',
    
    # JSON types
    'JSON': 'dict',
    'JSONB': 'dict',
    
    # Array types
    'ARRAY': 'List',
    
    # UUID type
    'UUID': 'UUID',
}

def get_pydantic_type(sql_type: str) -> tuple[str, Optional[str]]:
    """
    Convert SQLAlchemy type to Pydantic type and return any necessary import
    Returns: (type_name, import_statement)
    """
    base_type = sql_type.split('(')[0] if '(' in sql_type else sql_type
    
    if base_type in SQL_TO_PYDANTIC_TYPES:
        pydantic_type = SQL_TO_PYDANTIC_TYPES[base_type]
        
        # Define necessary imports
        if pydantic_type == 'datetime':
            return pydantic_type, 'from datetime import datetime'
        elif pydantic_type == 'date':
            return pydantic_type, 'from datetime import date'
        elif pydantic_type == 'time':
            return pydantic_type, 'from datetime import time'
        elif pydantic_type == 'Decimal':
            return pydantic_type, 'from decimal import Decimal'
        elif pydantic_type == 'UUID':
            return pydantic_type, 'from uuid import UUID'
        elif pydantic_type == 'List':
            return pydantic_type, 'from typing import List'
        
        return pydantic_type, None
    
    return 'Any', 'from typing import Any'

def generate_field_validation(field: Dict) -> str:
    """Generate Pydantic field validation based on field type and constraints"""
    validations = []
    
    if field['type'] == 'String' and field.get('length'):
        validations.append(f'max_length={field["length"]}')
    
    if field['type'] in ['Integer', 'SmallInteger', 'BigInteger']:
        validations.append('ge=0')
    
    if field['type'] in ['Float', 'Numeric', 'DECIMAL']:
        validations.append('ge=0.0')
    
    if not field.get('nullable', True):
        validations.append('...')  # Required field
    else:
        validations.append('None')
    
    if validations:
        return ' = Field(' + ', '.join(validations) + ')'
    
    return ''

# Templates as strings
TEMPLATES = {
    "model": '''from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, Float, Numeric
from sqlalchemy.sql import func
from app.db.base import Base

class {{name}}(Base):
    __tablename__ = "{{table_name}}"

    id = Column(Integer, primary_key=True)
{% for field in fields %}
    {{field.name}} = Column({{field.type}}{% if field.length %}({{field.length}}){% endif %}{% if field.nullable %}, nullable=True{% endif %})
{% endfor %}
    created_at = Column(
        DateTime(timezone=True), 
        server_default=func.now(),
        nullable=False
    )
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False
    )
''',

    "schema": '''{% set imports = [] -%}
from typing import Optional
from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field
{%- for field in fields %}
{%- set type_info = get_pydantic_type(field.type) %}
{%- if type_info[1] and type_info[1] not in imports %}
{{ type_info[1] }}
{%- set _ = imports.append(type_info[1]) %}
{%- endif %}
{%- endfor %}

class {{name}}Base(BaseModel):
    """Base schema for {{name}}"""
{%- for field in fields %}
    {%- set type_info = get_pydantic_type(field.type) %}
    {{field.name}}: {% if field.nullable %}Optional[{{type_info[0]}}]{% else %}{{type_info[0]}}{% endif %}{{ generate_field_validation(field) }}
{%- endfor %}

class {{name}}Create({{name}}Base):
    """Schema for creating a new {{name}}"""
    pass

class {{name}}Update(BaseModel):
    """Schema for updating an existing {{name}}"""
{%- for field in fields %}
    {%- set type_info = get_pydantic_type(field.type) %}
    {{field.name}}: Optional[{{type_info[0]}}] = None
{%- endfor %}

    model_config = ConfigDict(from_attributes=True)

class {{name}}InDB({{name}}Base):
    """Schema for {{name}} response"""
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
''',

    "repository": '''from typing import Optional, List, Tuple
from sqlalchemy import select, func
from app.core.repository import BaseRepository
from app.models.{{snake_name}} import {{name}}
from app.schemas.{{snake_name}} import {{name}}Create, {{name}}Update

class {{name}}Repository(BaseRepository[{{name}}, {{name}}Create, {{name}}Update]):
    """Repository for {{name}} model with custom methods"""
    
    pass
''',

    "service": '''from typing import Optional, List, Tuple
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.repositories.{{snake_name}} import {{name}}Repository
from app.models.{{snake_name}} import {{name}}
from app.schemas.{{snake_name}} import {{name}}Create, {{name}}Update
from app.core.exceptions import APIError

class {{name}}Service:
    def __init__(self, db: AsyncSession = Depends(get_db)):
        self.repository = {{name}}Repository({{name}}, db)

    async def create(self, schema: {{name}}Create) -> {{name}}:
        return await self.repository.create(schema)

    async def get(self, id: int) -> {{name}}:
        item = await self.repository.get(id)
        if not item:
            raise APIError(f"{{name}} with id {id} not found", status_code=404)
        return item

    async def get_multi(
        self, 
        skip: int = 0, 
        limit: int = 10
    ) -> Tuple[List[{{name}}], int]:
        return await self.repository.get_multi(skip=skip, limit=limit)

    async def update(self, id: int, schema: {{name}}Update) -> {{name}}:
        item = await self.repository.update(id=id, schema=schema)
        if not item:
            raise APIError(f"{{name}} with id {id} not found", status_code=404)
        return item

    async def delete(self, id: int) -> bool:
        if not await self.repository.delete(id=id):
            raise APIError(f"{{name}} with id {id} not found", status_code=404)
        return True
''',

    "endpoint": '''from typing import Optional
from fastapi import APIRouter, Depends, Query
from app.services.{{snake_name}} import {{name}}Service
from app.schemas.{{snake_name}} import {{name}}InDB, {{name}}Create, {{name}}Update
from app.utils.response_handler import response
from app.schemas.response import StandardResponse

router = APIRouter()

@router.post("/", response_model=StandardResponse[{{name}}InDB])
async def create_{{snake_name}}(
    schema: {{name}}Create,
    service: {{name}}Service = Depends()
):
    item = await service.create(schema)
    return response.success(
        data={{name}}InDB.model_validate(item),
        message="{{name}} created successfully"
    )

@router.get("/", response_model=StandardResponse[list[{{name}}InDB]])
async def get_{{snake_name}}s(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    service: {{name}}Service = Depends()
):
    items, total = await service.get_multi(skip=skip, limit=limit)
    return response.success(
        data=[{{name}}InDB.model_validate(item) for item in items],
        message="{{name}}s retrieved successfully",
        meta={
            "skip": skip,
            "limit": limit,
            "total": total
        }
    )

@router.get("/{id}", response_model=StandardResponse[{{name}}InDB])
async def get_{{snake_name}}(
    id: int,
    service: {{name}}Service = Depends()
):
    item = await service.get(id)
    return response.success(
        data={{name}}InDB.model_validate(item),
        message="{{name}} retrieved successfully"
    )

@router.put("/{id}", response_model=StandardResponse[{{name}}InDB])
async def update_{{snake_name}}(
    id: int,
    schema: {{name}}Update,
    service: {{name}}Service = Depends()
):
    item = await service.update(id, schema)
    return response.success(
        data={{name}}InDB.model_validate(item),
        message="{{name}} updated successfully"
    )

@router.delete("/{id}", response_model=StandardResponse[None])
async def delete_{{snake_name}}(
    id: int,
    service: {{name}}Service = Depends()
):
    await service.delete(id)
    return response.success(
        message="{{name}} deleted successfully"
    )
''',
}

def to_snake_case(name: str) -> str:
    """Convert CamelCase to snake_case"""
    name = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
    return re.sub('([a-z0-9])([A-Z])', r'\1_\2', name).lower()

def create_file(content: str, output_path: str, context: Dict):
    """Create a file from template content"""
    # Create Jinja2 environment with the template string
    template = Environment().from_string(content)
    rendered_content = template.render(**context)
    
    # Ensure directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    with open(output_path, 'w') as f:
        f.write(rendered_content)
    
    click.echo(f"Created {output_path}")

def update_init_file(directory: str, module_name: str):
    """Update __init__.py file with new import"""
    init_path = os.path.join(directory, '__init__.py')
    import_line = f"from .{module_name} import *\n"
    
    if os.path.exists(init_path):
        with open(init_path, 'r') as f:
            content = f.read()
        if import_line not in content:
            with open(init_path, 'a') as f:
                f.write(import_line)
    else:
        with open(init_path, 'w') as f:
            f.write(import_line)

def update_router(name: str, snake_name: str):
    """Update main router with new endpoint"""
    router_path = 'app/api/v1/router.py'
    import_line = f"from app.api.v1.endpoints import {snake_name}\n"
    router_line = f"api_router.include_router({snake_name}.router, prefix='/{snake_name}s', tags=['{snake_name}s'])\n"
    
    if not os.path.exists(router_path):
        # Create router file if it doesn't exist
        with open(router_path, 'w') as f:
            f.write("""from fastapi import APIRouter

api_router = APIRouter()
""")
    
    with open(router_path, 'r') as f:
        content = f.readlines()
    
    if import_line not in content:
        # Find the last import
        last_import = -1
        for i, line in enumerate(content):
            if line.startswith('from'):
                last_import = i
        
        content.insert(last_import + 1 if last_import >= 0 else 0, import_line)
        
        # Find the last router.include_router line or the api_router definition
        last_router = -1
        for i, line in enumerate(content):
            if 'include_router' in line or 'api_router = APIRouter()' in line:
                last_router = i
        
        content.insert(last_router + 1, router_line)
        
        with open(router_path, 'w') as f:
            f.writelines(content)

@click.command()
@click.argument('name')
@click.option('--fields', '-f', multiple=True, help='Field definitions in format: name:type:nullable:length')
def generate_crud(name: str, fields: List[str]):
    """Generate CRUD boilerplate for a new model"""
    snake_name = to_snake_case(name)
    table_name = f"{snake_name}s"
    
    # Parse fields
    parsed_fields = []
    for field in fields:
        parts = field.split(':')
        field_name = parts[0]
        field_type = parts[1]
        nullable = len(parts) > 2 and parts[2].lower() == 'true'
        length = parts[3] if len(parts) > 3 else None
        
        parsed_fields.append({
            'name': field_name,
            'type': field_type,
            'nullable': nullable,
            'length': length,
            'optional': nullable,
        })
    
    context = {
        'name': name,
        'snake_name': snake_name,
        'table_name': table_name,
        'fields': parsed_fields,
        'get_pydantic_type': get_pydantic_type,
        'generate_field_validation': generate_field_validation
    }
    
    # Generate files
    create_file(TEMPLATES['model'], f'app/models/{snake_name}.py', context)
    create_file(TEMPLATES['schema'], f'app/schemas/{snake_name}.py', context)
    create_file(TEMPLATES['repository'], f'app/repositories/{snake_name}.py', context)
    create_file(TEMPLATES['service'], f'app/services/{snake_name}.py', context)
    create_file(TEMPLATES['endpoint'], f'app/api/v1/endpoints/{snake_name}.py', context)
    
    # Update __init__.py files
    update_init_file('app/models', snake_name)
    update_init_file('app/schemas', snake_name)
    update_init_file('app/repositories', snake_name)
    update_init_file('app/services', snake_name)
    
    # Update router
    update_router(name, snake_name)
    
    click.echo(f"\nSuccessfully generated CRUD for {name}!")
    click.echo("\nNext steps:")
    click.echo("1. Review and adjust the generated files")
    click.echo("2. Create and run database migrations:")
    # click.echo("   alembic revision --autogenerate -m " + f'"add_{snake_name}_table"')
    # click.echo("   alembic upgrade head")

if __name__ == '__main__':
    generate_crud()