from __future__ import annotations
import re
import uuid
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

@dataclass
class User:
    name: str
    cpf: str
    email: str
    phone_number: str
    id: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    def __post_init__(self) -> None:
        if self.id is None:
            self.id = str(uuid.uuid4())
        self._validate()

    def _validate(self) -> None:
        if not self.name or not self.name.strip():
            raise ValueError('User name cannot be empty.')
        if not self._is_valid_cpf(self.cpf):
            raise ValueError(f'Invalid CPF: {self.cpf}')
        if not self._is_valid_email(self.email):
            raise ValueError(f'Invalid email: {self.email}')
        if not self.phone_number or not self.phone_number.strip():
            raise ValueError('Phone number cannot be empty.')

    @staticmethod
    def _is_valid_cpf(cpf: str) -> bool:
        cpf_digits = re.sub('\\D', '', cpf)
        if len(cpf_digits) != 11:
            return False
        if cpf_digits == cpf_digits[0] * 11:
            return False
        for i in range(9, 11):
            total = sum((int(cpf_digits[num]) * (i + 1 - num) for num in range(0, i)))
            digit = total * 10 % 11 % 10
            if digit != int(cpf_digits[i]):
                return False
        return True

    @staticmethod
    def _is_valid_email(email: str) -> bool:
        pattern = '^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}$'
        return bool(re.match(pattern, email))

    def update(self, name: Optional[str]=None, email: Optional[str]=None, phone_number: Optional[str]=None) -> None:
        if name is not None:
            if not name.strip():
                raise ValueError('User name cannot be empty.')
            self.name = name
        if email is not None:
            if not self._is_valid_email(email):
                raise ValueError(f'Invalid email: {email}')
            self.email = email
        if phone_number is not None:
            if not phone_number.strip():
                raise ValueError('Phone number cannot be empty.')
            self.phone_number = phone_number
        self.updated_at = datetime.utcnow()
