from flask import (Blueprint, jsonify, redirect, render_template, request,
                   url_for)
from flask_login import current_user, login_required
from sqlalchemy import or_, and_

from app.extensions import db
from app.models.message import Message
from app.models.user import User

bp = Blueprint('chat', __name__,
               template_folder='../templates/communication',
               static_folder='static',
               static_url_path='communication')


@bp.route('/chat')
@login_required
def chat():
    user = User.query.get(current_user.id)
    if not user:
        return redirect(url_for('home'))

    subquery = db.session.query(Message.sender_id, Message.receiver_id).filter(
        or_(Message.sender_id == user.id, Message.receiver_id == user.id)
    ).distinct().subquery()

    chat_users = db.session.query(User).filter(
        or_(User.id == subquery.c.sender_id, User.id == subquery.c.receiver_id),
        User.id != user.id
    ).distinct().all()

    return render_template('communication/chat.jinja', user=user, chat_users=chat_users)


@bp.route('/search-users')
def search_users():
    current_email = request.args.get('current_email')
    query = request.args.get('query', '')

    users = User.query.filter(
        User.email.ilike(f'%{query}%'),
        User.email != current_email
    ).all()
    print([{'email': user.email} for user in users])
    return jsonify([{'email': user.email} for user in users])


@bp.route('/get-messages')
def get_messages():
    sender_email = request.args.get('sender')
    receiver_email = request.args.get('receiver')

    sender = User.query.filter_by(email=sender_email).first()
    receiver = User.query.filter_by(email=receiver_email).first()

    if not sender or not receiver:
        return jsonify([])

    messages = Message.query.filter(
        or_(
            and_(Message.sender_id == sender.id, Message.receiver_id == receiver.id),
            and_(Message.sender_id == receiver.id, Message.receiver_id == sender.id)
        )
    ).order_by(Message.timestamp).all()

    return jsonify([{
        'sender': message.sender.email,
        'sender_profile_picture': message.sender.profile_picture,
        'content': message.content,
        'timestamp': message.timestamp.strftime('%Y-%m-%d %H:%M:%S')
    } for message in messages])


@bp.route('/get-all-users')
def get_all_users():
    current_email = request.args.get('current_email')
    users = User.query.filter(User.email != current_email).all()
    return jsonify([{'email': user.email} for user in users])
