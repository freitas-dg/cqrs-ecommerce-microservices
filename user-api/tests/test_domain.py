import pytest
from app.domain.entities import User

class TestUserEntity:

    def test_create_valid_user(self):
        user = User(name='Douglas Freitas', cpf='52998224725', email='douglas@example.com', phone_number='+5511999998888')
        assert user.name == 'Douglas Freitas'
        assert user.cpf == '52998224725'
        assert user.email == 'douglas@example.com'
        assert user.phone_number == '+5511999998888'
        assert isinstance(user.id, str)
        assert len(user.id) == 36

    def test_reject_empty_name(self):
        with pytest.raises(ValueError, match='name cannot be empty'):
            User(name='', cpf='52998224725', email='a@b.com', phone_number='123456789')

    def test_reject_invalid_cpf(self):
        with pytest.raises(ValueError, match='Invalid CPF'):
            User(name='Test', cpf='00000000000', email='a@b.com', phone_number='123456789')

    def test_reject_invalid_cpf_length(self):
        with pytest.raises(ValueError, match='Invalid CPF'):
            User(name='Test', cpf='123', email='a@b.com', phone_number='123456789')

    def test_reject_invalid_email(self):
        with pytest.raises(ValueError, match='Invalid email'):
            User(name='Test', cpf='52998224725', email='not-an-email', phone_number='123456789')

    def test_reject_empty_phone(self):
        with pytest.raises(ValueError, match='Phone number cannot be empty'):
            User(name='Test', cpf='52998224725', email='a@b.com', phone_number='')

    def test_update_valid_fields(self):
        user = User(name='Original Name', cpf='52998224725', email='original@test.com', phone_number='+5511111111111')
        user.update(name='New Name', email='new@test.com')
        assert user.name == 'New Name'
        assert user.email == 'new@test.com'
        assert user.updated_at is not None

    def test_update_rejects_invalid_email(self):
        user = User(name='Test', cpf='52998224725', email='a@b.com', phone_number='123456789')
        with pytest.raises(ValueError, match='Invalid email'):
            user.update(email='bad-email')

    def test_update_partial_fields(self):
        user = User(name='Test', cpf='52998224725', email='a@b.com', phone_number='123456789')
        user.update(name='Updated Name')
        assert user.name == 'Updated Name'
        assert user.email == 'a@b.com'
