from __future__ import annotations
import logging
from flask import Blueprint, g, jsonify, request
from app.application.use_cases import OrderUseCases
from app.infrastructure.jwt_auth import jwt_required

logger = logging.getLogger(__name__)
orders_bp = Blueprint('orders', __name__, url_prefix='/api/v1/orders')
_use_cases: OrderUseCases | None = None

def init_routes(use_cases: OrderUseCases) -> None:
    global _use_cases
    _use_cases = use_cases

@orders_bp.route('', methods=['POST'])
@jwt_required
def create_order():
    data = request.get_json()
    if not data:
        return (jsonify({'error': 'Request body is required.'}), 400)
    required_fields = ['item_description', 'item_quantity', 'item_price']
    missing = [f for f in required_fields if f not in data]
    if missing:
        return (jsonify({'error': f"Missing required fields: {', '.join(missing)}"}), 400)
    try:
        order = _use_cases.create_order(user_id=g.current_user_id, item_description=data['item_description'], item_quantity=data['item_quantity'], item_price=data['item_price'])
        return (jsonify({'id': order.id, 'user_id': order.user_id, 'item_description': order.item_description, 'item_quantity': order.item_quantity, 'item_price': str(order.item_price), 'total_value': str(order.total_value), 'created_at': order.created_at.isoformat() if order.created_at else None, 'updated_at': order.updated_at.isoformat() if order.updated_at else None}), 201)
    except ValueError as e:
        return (jsonify({'error': str(e)}), 400)
    except Exception as e:
        logger.error('Error creating order: %s', e)
        return (jsonify({'error': 'Internal server error.'}), 500)

@orders_bp.route('', methods=['GET'])
@jwt_required
def list_orders():
    skip = request.args.get('skip', 0, type=int)
    limit = request.args.get('limit', 100, type=int)
    orders = _use_cases.list_orders(skip=skip, limit=limit)
    return (jsonify(orders), 200)

@orders_bp.route('/search', methods=['GET'])
@jwt_required
def search_orders():
    q = request.args.get('q')
    if not q:
        return (jsonify({'error': 'Query parameter "q" is required.'}), 400)
    results = _use_cases.search_orders(q)
    return (jsonify(results), 200)

@orders_bp.route('/user/<string:user_id>', methods=['GET'])
@jwt_required
def list_orders_by_user(user_id: str):
    skip = request.args.get('skip', 0, type=int)
    limit = request.args.get('limit', 100, type=int)
    orders = _use_cases.list_orders_by_user(user_id, skip=skip, limit=limit)
    return (jsonify(orders), 200)

@orders_bp.route('/<string:order_id>', methods=['GET'])
@jwt_required
def get_order(order_id: str):
    order = _use_cases.get_order(order_id)
    if not order:
        return (jsonify({'error': f'Order with id {order_id} not found.'}), 404)
    return (jsonify(order), 200)

@orders_bp.route('/<string:order_id>', methods=['PUT'])
@jwt_required
def update_order(order_id: str):
    data = request.get_json()
    if not data:
        return (jsonify({'error': 'Request body is required.'}), 400)
    try:
        order = _use_cases.update_order(order_id=order_id, item_description=data.get('item_description'), item_quantity=data.get('item_quantity'), item_price=data.get('item_price'))
    except ValueError as e:
        return (jsonify({'error': str(e)}), 400)
    if not order:
        return (jsonify({'error': f'Order with id {order_id} not found.'}), 404)
    return (jsonify({'id': order.id, 'user_id': order.user_id, 'item_description': order.item_description, 'item_quantity': order.item_quantity, 'item_price': str(order.item_price), 'total_value': str(order.total_value), 'created_at': order.created_at.isoformat() if order.created_at else None, 'updated_at': order.updated_at.isoformat() if order.updated_at else None}), 200)

@orders_bp.route('/<string:order_id>', methods=['DELETE'])
@jwt_required
def delete_order(order_id: str):
    deleted = _use_cases.delete_order(order_id)
    if not deleted:
        return (jsonify({'error': f'Order with id {order_id} not found.'}), 404)
    return (jsonify({'message': f'Order {order_id} deleted successfully.'}), 200)

