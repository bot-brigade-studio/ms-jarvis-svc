# app/core/repository.py

from typing import Generic, TypeVar, Type, Optional, List, Any, Dict, Tuple, Union
from uuid import UUID
from sqlalchemy import distinct, select, tuple_, update, delete, and_, or_, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload, load_only
from sqlalchemy.sql import Select
from pydantic import BaseModel
from app.db.base import Base
from app.core.exceptions import APIError
from app.models.base import current_tenant_id, current_user_id

ModelType = TypeVar("ModelType", bound=Base) # type: ignore
CreateSchemaType = TypeVar("CreateSchemaType", bound=BaseModel)
UpdateSchemaType = TypeVar("UpdateSchemaType", bound=BaseModel)

class BaseRepository(Generic[ModelType, CreateSchemaType, UpdateSchemaType]):
    """
    Enhanced Base Repository with support for relationships and complex queries
    """
    
    def __init__(self, model: Type[ModelType], db: AsyncSession):
        self.model = model
        self.db = db
        self.has_soft_delete = hasattr(model, 'deleted_at')

    def _get_model_data(self, schema: Union[BaseModel, Dict[str, Any]]) -> dict:
        """Convert input schema to dictionary data"""
        if isinstance(schema, BaseModel):
            return schema.model_dump(exclude_unset=True)
        return schema

    async def create(
        self, 
        schema: Union[CreateSchemaType, Dict[str, Any]],
        relationships: Dict[str, Any] = None
    ) -> ModelType:
        """
        Create a new record with optional relationships
        """
        try:
            # Convert schema to dict if it's a Pydantic model
            model_data = self._get_model_data(schema)
            
            # Create model instance
            db_obj = self.model(**model_data)
            
            # Handle relationships if provided
            if relationships:
                for rel_name, rel_value in relationships.items():
                    setattr(db_obj, rel_name, rel_value)
            
            self.db.add(db_obj)
            await self.db.flush()
            await self.db.refresh(db_obj)
            return db_obj
            
        except Exception as e:
            await self.db.rollback()
            raise APIError(f"Create operation failed: {str(e)}")

    def _build_query(
        self,
        joins: List[str] = None,
        filters: Dict[str, Any] = None,
        search_fields: Dict[str, str] = None,
        search_term: str = None,
        order_by: List[str] = None,
        load_options: List[str] = None,
        select_fields: List[str] = None,
        is_tenant_scoped: bool = False,
        with_deleted: bool = False
    ) -> Select:
        """
        Build a complex query with joins, filters, and eager loading
        """
        # Start with base query
        query = select(self.model)
        
        if select_fields:
            # Convert field names to ORM attributes
            orm_attrs = [getattr(self.model, field) for field in select_fields]
            query = select(self.model).options(
                load_only(*orm_attrs)
            )
        else:
            query = select(self.model)

        # Apply joins if specified
        if joins:
            for join in joins:
                relationship = getattr(self.model, join)
                query = query.join(relationship)

        # Apply eager loading options
        if load_options:
            for option in load_options:
                # Support nested relationships with dots
                if '.' in option:
                    # Handle nested eager loading
                    parts = option.split('.')
                    current_model = self.model
                    loader = None
                    
                    for part in parts:
                        attr = getattr(current_model, part)
                        if loader is None:
                            loader = joinedload(attr)
                        else:
                            loader = loader.joinedload(attr)
                        # Update current_model to the related model for next iteration
                        current_model = attr.property.mapper.class_
                    
                    query = query.options(loader)
                else:
                    attr = getattr(self.model, option)
                    query = query.options(joinedload(attr))
        # Apply filters
        if filters:
            filter_conditions = []
            for key, value in filters.items():
                if '.' in key:
                    # Handle relationship filtering
                    relation_path = key.split('.')
                    current_model = self.model
                    
                    # Navigate through the relationships to get the final attribute
                    for i, path in enumerate(relation_path):
                        if i == len(relation_path) - 1:
                            # Last item is the actual column
                            filter_conditions.append(getattr(current_model, path) == value)
                        else:
                            # Get the relationship model
                            current_model = getattr(current_model, path).property.mapper.class_
                else:
                    if isinstance(value, list):
                        filter_conditions.append(getattr(self.model, key).in_(value))
                    else:
                        filter_conditions.append(getattr(self.model, key) == value)
            
            if filter_conditions:
                query = query.where(and_(*filter_conditions))

        # Apply search if specified
        if search_term and search_fields:
            search_conditions = []
            for field, search_type in search_fields.items():
                if search_type == 'exact':
                    search_conditions.append(getattr(self.model, field) == search_term)
                elif search_type == 'contains':
                    search_conditions.append(getattr(self.model, field).ilike(f'%{search_term}%'))
            if search_conditions:
                query = query.where(or_(*search_conditions))

        # Apply ordering
        if order_by:
            for order_field in order_by:
                direction = 'desc' if order_field.startswith('-') else 'asc'
                field = order_field.lstrip('-')
                query = query.order_by(
                    getattr(getattr(self.model, field), direction)()
                )
                
        if is_tenant_scoped and hasattr(self.model, 'tenant_id') and current_tenant_id.get():        
            query = query.where(and_(
                self.model.tenant_id == current_tenant_id.get()
            ))
        
        if not with_deleted and self.has_soft_delete:
            query = query.where(self.model.deleted_at.is_(None))

        return query

    async def get(
        self,
        id: Optional[UUID] = None,
        filters: Dict[str, Any] = None,
        joins: List[str] = None,
        load_options: List[str] = None,
        select_fields: List[str] = None,
        is_tenant_scoped: bool = False,
        with_deleted: bool = False
    ) -> Optional[ModelType]:
        """
        Get a record by ID with optional relationship loading
        """
        
        if not id and not filters:
            raise ValueError("Either id or filters must be provided")
        
        query = self._build_query(joins=joins, load_options=load_options, select_fields=select_fields, filters=filters, is_tenant_scoped=is_tenant_scoped, with_deleted=with_deleted)
        if id:
            query = query.where(self.model.id == id)
        result = await self.db.execute(query)
        return result.unique().scalar_one_or_none()

    async def get_multi(
        self,
        *,
        skip: int = 0,
        limit: int = 100,
        joins: List[str] = None,
        filters: Dict[str, Any] = None,
        search_fields: Dict[str, str] = None,
        search_term: str = None,
        order_by: List[str] = None,
        load_options: List[str] = None,
        select_fields: List[str] = None,
        is_tenant_scoped: bool = False,
        with_deleted: bool = False
    ) -> Tuple[List[ModelType], int]:
        """
        Get multiple records with comprehensive querying options
        """

        count_query = self._build_count_query(
            joins=joins,
            filters=filters,
            search_fields=search_fields,
            search_term=search_term,
            is_tenant_scoped=is_tenant_scoped,
            with_deleted=with_deleted
        )
        total = await self.db.scalar(count_query)

        # Build query
        query = self._build_query(
            joins=joins,
            filters=filters,
            search_fields=search_fields,
            search_term=search_term,
            order_by=order_by,
            load_options=load_options,
            select_fields=select_fields,
            is_tenant_scoped=is_tenant_scoped,
            with_deleted=with_deleted
        )
    
        # Apply pagination
        query = query.offset(skip).limit(limit)

        # Execute query
        result = await self.db.execute(query)
    
        return result.unique().scalars().all(), total
    
    def _build_count_query(
        self,
        joins: List[str] = None,
        filters: Dict[str, Any] = None,
        search_fields: Dict[str, str] = None,
        search_term: str = None,
        is_tenant_scoped: bool = False,
        with_deleted: bool = False
    ) -> Select:
        """
        Build an optimized count query
        """
        # Start with simple count query
        # Check if model has an id column
        has_id = hasattr(self.model, 'id')
        
        # Build appropriate count expression
        if has_id:
            # For tables with id column
            count_expr = func.count(distinct(self.model.id))
        else:
            # For many-to-many tables, count all columns that make up the primary key
            primary_key_columns = self.model.__table__.primary_key.columns
            if len(primary_key_columns) > 1:
                # For composite primary keys, use distinct on all key columns
                count_expr = func.count(distinct(
                    tuple_(*[getattr(self.model, col.name) for col in primary_key_columns])
                ))
            else:
                # For single column primary key
                count_expr = func.count(distinct(
                    getattr(self.model, next(iter(primary_key_columns)).name)
                ))

        # Start with optimized count query
        query = select(count_expr)

        # Apply joins if specified
        if joins:
            for join in joins:
                relationship = getattr(self.model, join)
                query = query.join(relationship)

        # Apply filters
        if filters:
            filter_conditions = []
            for key, value in filters.items():
                if '.' in key:
                    # Handle relationship filtering
                    relation_path = key.split('.')
                    current_model = self.model
                    for i, path in enumerate(relation_path):
                        if i == len(relation_path) - 1:
                            filter_conditions.append(getattr(current_model, path) == value)
                        else:
                            current_model = getattr(current_model, path).property.mapper.class_
                else:
                    if isinstance(value, list):
                        filter_conditions.append(getattr(self.model, key).in_(value))
                    else:
                        filter_conditions.append(getattr(self.model, key) == value)
            
            if filter_conditions:
                query = query.where(and_(*filter_conditions))

        # Apply search if specified
        if search_term and search_fields:
            search_conditions = []
            for field, search_type in search_fields.items():
                if search_type == 'exact':
                    search_conditions.append(getattr(self.model, field) == search_term)
                elif search_type == 'contains':
                    search_conditions.append(getattr(self.model, field).ilike(f'%{search_term}%'))
            if search_conditions:
                query = query.where(or_(*search_conditions))
                
        if is_tenant_scoped and hasattr(self.model, 'tenant_id') and current_tenant_id.get():        
            query = query.where(and_(
                self.model.tenant_id == current_tenant_id.get()
            ))

        if not with_deleted and self.has_soft_delete:
            query = query.where(self.model.deleted_at.is_(None))

        return query

    async def update(
        self,
        id: UUID,
        schema: Union[UpdateSchemaType, Dict[str, Any]],
        relationships: Dict[str, Any] = None
    ) -> Optional[ModelType]:
        """
        Update a record with optional relationship updates
        """
        try:
            # Convert schema to dict if it's a Pydantic model
            update_data = self._get_model_data(schema)

            # Update main record
            stmt = (
                update(self.model)
                .where(self.model.id == id)
                .values(**update_data)
                .returning(self.model)
            )
            result = await self.db.execute(stmt)
            updated_obj = result.scalar_one_or_none()

            if updated_obj and relationships:
                # Update relationships
                for rel_name, rel_value in relationships.items():
                    setattr(updated_obj, rel_name, rel_value)
                await self.db.flush()
                await self.db.refresh(updated_obj)

            return updated_obj

        except Exception as e:
            await self.db.rollback()
            raise APIError(f"Update operation failed: {str(e)}")

    async def delete(
        self,
        id: Optional[UUID] = None,
        filters: Optional[Dict[str, Any]] = None,
        force: bool = False
    ) -> bool:
        """
        Delete record(s) by ID or filters with optional force delete
        
        Args:
            id: Optional UUID of the record to delete
            filters: Optional dictionary of filters to delete by
            force: If True, performs hard delete even for soft-deleteable models
            
        Returns:
            bool: True if any records were deleted, False otherwise
            
        Raises:
            APIError: If delete operation fails
            ValueError: If neither id nor filters are provided
        """
        try:
            if id is None and not filters:
                raise ValueError("Either id or filters must be provided")

            # Build where clause
            conditions = []
            if id is not None:
                conditions.append(self.model.id == id)
            if filters:
                conditions.extend(getattr(self.model, k) == v for k, v in filters.items())

            if self.has_soft_delete and not force:
                # Soft delete
                stmt = (
                    update(self.model)
                    .where(and_(*conditions))
                    .values(deleted_at=func.now(), deleted_by=current_user_id.get())
                )
            else:
                # Hard delete
                stmt = delete(self.model).where(and_(*conditions))

            result = await self.db.execute(stmt)
            return result.rowcount > 0

        except Exception as e:
            await self.db.rollback()
            raise APIError(f"Delete operation failed: {str(e)}")

    async def exists(
        self,
        filters: Dict[str, Any]
    ) -> bool:
        """
        Check if records exist with given filters
        """
        query = self._build_query(filters=filters)
        result = await self.db.execute(
            select(func.count()).select_from(query.subquery())
        )
        return result.scalar() > 0

    async def count(
        self,
        filters: Dict[str, Any] = None
    ) -> int:
        """
        Count records with optional filters
        """
        query = self._build_query(filters=filters)
        result = await self.db.execute(
            select(func.count()).select_from(query.subquery())
        )
        return result.scalar()