from __future__ import annotations
import uuid
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Optional

@dataclass
class Order:
    user_id: str
    item_description: str
    item_quantity: int
    item_price: Decimal
    total_value: Optional[Decimal] = None
    id: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    def __post_init__(self) -> None:
        if self.id is None:
            self.id = str(uuid.uuid4())
        self._validate()
        if self.total_value is None:
            self.total_value = self.calculate_total()

    def _validate(self) -> None:
        if not self.user_id or not self.user_id.strip():
            raise ValueError('user_id cannot be empty.')
        if not self.item_description or not self.item_description.strip():
            raise ValueError('item_description cannot be empty.')
        if self.item_quantity is None or self.item_quantity <= 0:
            raise ValueError('item_quantity must be a positive integer.')
        if self.item_price is None or self.item_price <= 0:
            raise ValueError('item_price must be a positive value.')

    def calculate_total(self) -> Decimal:
        return Decimal(str(self.item_quantity)) * Decimal(str(self.item_price))

    def update(self, item_description: Optional[str]=None, item_quantity: Optional[int]=None, item_price: Optional[Decimal]=None) -> None:
        if item_description is not None:
            if not item_description.strip():
                raise ValueError('item_description cannot be empty.')
            self.item_description = item_description
        if item_quantity is not None:
            if item_quantity <= 0:
                raise ValueError('item_quantity must be a positive integer.')
            self.item_quantity = item_quantity
        if item_price is not None:
            if item_price <= 0:
                raise ValueError('item_price must be a positive value.')
            self.item_price = Decimal(str(item_price))
        self.total_value = self.calculate_total()
        self.updated_at = datetime.utcnow()
