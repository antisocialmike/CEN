from typing import Generic, List, TypeVar

from pydantic import BaseModel

DEFAULT_PAGE_SIZE = 20
MAX_PAGE_SIZE = 100

T = TypeVar("T")


class Page(BaseModel, Generic[T]):
    """Un tramo de una lista. Una pagina fuera de rango llega vacia pero con
    su total, para que el cliente sepa a cual volver."""

    items: List[T]
    total: int
    page: int
    page_size: int


def page_offset(page: int, page_size: int) -> int:
    return (page - 1) * page_size
