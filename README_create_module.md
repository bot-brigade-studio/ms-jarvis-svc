# FastAPI Module Generator

A CLI tool for generating and deleting CRUD modules in your FastAPI application.

## Field Type Mappings

SQLAlchemy to Pydantic type mappings:

| SQLAlchemy Type | Pydantic Type | Validation |
| --------------- | ------------- | ---------- |
| String          | str           | max_length |
| Text            | str           | None       |
| Integer         | int           | ge=0       |
| Float           | float         | ge=0.0     |
| Boolean         | bool          | None       |
| DateTime        | datetime      | None       |
| JSON            | dict          | None       |
| ARRAY           | List          | None       |
| Numeric         | Decimal       | ge=0.0     |
| UUID            | UUID          | None       |

## Best Practices

1. **Naming Conventions**:

   - Use CamelCase for module names (e.g., UserProfile)
   - Use snake_case for field names (e.g., first_name)

2. **Field Types**:

   - Use appropriate field types for your data
   - Consider adding length constraints for String fields
   - Mark required fields as non-nullable

3. **After Generation**:

   - Review generated files
   - Add custom methods as needed
   - Create and run migrations
   - Add tests

4. **Before Deletion**:
   - Use --check-only to preview changes
   - Backup important custom code
   - Handle database migrations carefully

## Troubleshooting

1. **File Not Found Errors**:

   - Ensure you're running the scripts from project root
   - Check if directory structure matches expected paths

2. **Type Conversion Errors**:

   - Verify field type is supported
   - Check field definition format

3. **Migration Issues**:

   - Review migration files before applying
   - Handle existing data appropriately

4. **Import Errors**:
   - Ensure all required packages are installed
   - Check import paths in generated files

## Example Workflow

1. Create a new module:

```bash
python scripts/create_module.py Product \
    -f "name:String:false:100" \
    -f "price:Numeric:false" \
    -f "description:Text:true"
```

2. Create and run migration:

```bash
alembic revision --autogenerate -m "add_product_table"
alembic upgrade head
```

3. Test the endpoints:

```bash
# Create product
curl -X POST "http://localhost:8000/api/v1/products/" \
     -H "Content-Type: application/json" \
     -d '{"name": "Test Product", "price": 99.99, "description": "Test Description"}'

# Get products
curl "http://localhost:8000/api/v1/products/"
```

4. Delete the module when no longer needed:

```bash
python scripts/delete_module.py Product --check-only
python scripts/delete_module.py Product
```
