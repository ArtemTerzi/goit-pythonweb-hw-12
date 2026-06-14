"""Utility API router.

Defines helper and diagnostic endpoints, such as database health checkers.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from src.conf import messages

from src.database.db import get_db

router = APIRouter(tags=["utils"])


@router.get("/healthchecker")
async def healthchecker(db: AsyncSession = Depends(get_db)):
    """Verifies the health and connectivity of the backend database.

    Executes a simple 'SELECT 1' test query to ensure that the database session
    is active, configured correctly, and capable of handling incoming connections.

    Args:
        db (AsyncSession): Asynchronous database session. Defaults to Depends(get_db).

    Returns:
        dict: A dictionary containing a welcoming success message.

    Raises:
        HTTPException: If the test query fails to return a value or if there is
            an error connecting to the database (500 Internal Server Error).
    """
    try:
        result = await db.execute(text("SELECT 1"))
        result = result.scalar_one_or_none()

        if result is None:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=messages.BAD_CONFIG_DB,
            )
        return {"message": messages.SUCCESSFUL_HEALTHCHECK}
    except Exception as e:
        print(e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=messages.FAILED_CONNECT_TO_DB,
        )
