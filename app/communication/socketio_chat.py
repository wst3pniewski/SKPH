from flask_socketio import SocketIO, emit, join_room
from sqlalchemy.exc import SQLAlchemyError

from app.extensions import db
from app.models.message import Message
from app.models.user import User

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
            db.session.commit()

            emit('receive_message', {
                'sender': sender_email,
                'receiver': receiver_email,
                'message': message_content,
                'timestamp': new_message.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
                'sender_profile_picture': sender.profile_picture
            }, room=room)
        else:
            print(f"Sender or receiver not found: {sender_email}, {receiver_email}")
    except SQLAlchemyError as e:
        db.session.rollback()
        print(f"Error handling message: {e}")


@socketio.on('join')
def on_join(data):
    email = data['email']
    receiver = data.get('receiver', None)

    if receiver:
        room = '_'.join(sorted([email, receiver]))
        join_room(room)
        print(f"User {email} joined room {room}")
