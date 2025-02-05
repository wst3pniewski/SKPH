from ssl import socket_error
from flask import current_app as app
from flask_socketio import SocketIO, emit, join_room
from sqlalchemy.exc import SQLAlchemyError

from app.extensions import db
from app.models.message import Message
from app.models.user import User
from app.models.notification import Notification

socketio = SocketIO()


@socketio.on('send_message')
def handle_message(data):
    try:
        sender_email = data['sender']
        receiver_email = data['receiver']
        message_content = data['message']

        room = '_'.join(sorted([sender_email, receiver_email]))

        sender = User.query.filter_by(email=sender_email).first()
        receiver = User.query.filter_by(email=receiver_email).first()

        if sender and receiver:
            new_message = Message(
                sender_id=sender.id,
                receiver_id=receiver.id,
                content=message_content
            )
            db.session.add(new_message)

            new_notification = Notification(
                user_id=receiver.id,
                message=f"New message from {sender_email}: {message_content}"
            )

            db.session.add(new_notification)

            db.session.commit()

            emit('receive_message', {
                'sender': sender_email,
                'receiver': receiver_email,
                'message': message_content,
                'timestamp': new_message.timestamp.strftime('%H:%M %d-%m-%Y'),
                'sender_profile_picture': sender.profile_picture
            }, room=room)

            emit('new_message', {
                'sender': sender_email,
                'receiver': receiver_email,
                'timestamp': new_message.timestamp.strftime('%H:%M %d-%m-%Y')
            }, room=receiver_email)
        else:
            app.logger.warning(f"Sender or receiver not found: {sender_email}, {receiver_email}")
    except SQLAlchemyError as e:
        db.session.rollback()
        app.logger.error(f"Error handling message: {e}")


@socketio.on('join')
def on_join(data):
    email = data['email']
    receiver = data.get('receiver', None)

    if receiver:
        room = '_'.join(sorted([email, receiver]))
        join_room(room)
        app.logger.info(f"User {email} joined room {room}")


@socketio.on('join_room')
def handle_join_room(user_email):
    if user_email:
        join_room(user_email)
        app.logger.info(f"User {user_email} joined their personal room.")
    else:
        app.logger.error(f'No user email provided for joining room.')


@socketio.on('connect')
def handle_connect():
    emit('request_user_email')
