"""
VendorOS - Base Repository
Generic async CRUD repository that all domain repositories inherit from.
Uses the Repository Pattern to keep database logic out of service/route layers.
"""

from typing import Any, Dict, Generic, List, Optional, Tuple, Type, TypeVar
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.connection import Base

ModelT = TypeVar("ModelT", bound=Base)


class BaseRepository(Generic[ModelT]):
    """
    Generic async repository providing standard CRUD operations.

    Parameters
    ----------
    model:
        The SQLAlchemy ORM model class.
    db:
        An active async database session.
    """

    def __init__(self, model: Type[ModelT], db: AsyncSession) -> None:
        self.model = model
        self.db = db

    # ── Create ────────────────────────────────────────────────────────────────

    async def create(self, **kwargs: Any) -> ModelT:
        """Instantiate, persist, and return a new model instance."""
        instance = self.model(**kwargs)
        self.db.add(instance)
        await self.db.flush()
        await self.db.refresh(instance)
        return instance

    # ── Read ──────────────────────────────────────────────────────────────────

    async def get_by_id(self, record_id: UUID) -> Optional[ModelT]:
        """Return the model instance for *record_id*, or ``None``."""
        result = await self.db.execute(
            select(self.model).where(self.model.id == record_id)  # type: ignore[attr-defined]
        )
        return result.scalar_one_or_none()

    async def get_all(
        self,
        offset: int = 0,
        limit: int = 20,
        filters: Optional[List[Any]] = None,
    ) -> Tuple[List[ModelT], int]:
        """
        Return a paginated list and total count.

        Parameters
        ----------
        offset:   Number of rows to skip.
        limit:    Maximum rows to return.
        filters:  SQLAlchemy column expressions to apply as WHERE clauses.

        Returns
        -------
        (items, total)
        """
        query = select(self.model)
        count_query = select(func.count()).select_from(self.model)

        if filters:
            for f in filters:
                query = query.where(f)
                count_query = count_query.where(f)

        total_result = await self.db.execute(count_query)
        total: int = total_result.scalar_one()

        result = await self.db.execute(query.offset(offset).limit(limit))
        items = list(result.scalars().all())

        return items, total

    # ── Update ────────────────────────────────────────────────────────────────

    async def update(self, record_id: UUID, data: Dict[str, Any]) -> Optional[ModelT]:
        """
        Apply *data* dict (field→value) to the record and return the refreshed instance.
        Returns ``None`` if the record does not exist.
        """
        instance = await self.get_by_id(record_id)
        if instance is None:
            return None
        for field, value in data.items():
            if value is not None:
                setattr(instance, field, value)
        self.db.add(instance)
        await self.db.flush()
        await self.db.refresh(instance)
        return instance

    # ── Delete ────────────────────────────────────────────────────────────────

    async def delete(self, record_id: UUID) -> bool:
        """
        Delete the record for *record_id*.
        Returns ``True`` if deleted, ``False`` if not found.
        """
        instance = await self.get_by_id(record_id)
        if instance is None:
            return False
        await self.db.delete(instance)
        await self.db.flush()
        return True