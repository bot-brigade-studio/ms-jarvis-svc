# app/core/transaction.py
from functools import wraps
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.exceptions import APIError

def transaction_handler():
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Get the db session from the service instance
            service_instance = args[0]  # self in service class
            db: AsyncSession = service_instance.repository.db

            try:
                # Execute the function
                result = await func(*args, **kwargs)
                # Commit the transaction
                await db.commit()
                return result
            except Exception as e:
                # Rollback on error
                await db.rollback()
                # Re-raise API errors
                if isinstance(e, APIError):
                    raise e
                # Wrap other errors
                raise APIError(
                    message=f"Transaction failed: {str(e)}",
                    status_code=500
                )
        return wrapper
    return decorator