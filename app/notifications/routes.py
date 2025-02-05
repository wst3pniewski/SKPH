from flask import Blueprint, jsonify
from flask_login import current_user, login_required

from app.extensions import db
from app.models.notification import Notification

bp = Blueprint('notifications', __name__, url_prefix='/notifications')


@bp.route('/unread', methods=['GET'])
@login_required
def get_unread_notifications():
    notifications = Notification.query.filter_by(user_id=current_user.id, is_read=False).all()
    return jsonify([{
        'id': n.id,
        'message': n.message,
        'timestamp': n.timestamp.strftime('%Y-%m-%d %H:%M:%S')
    } for n in notifications])


@bp.route('/mark_as_read/<int:notification_id>', methods=['POST'])
@login_required
def mark_as_read(notification_id):
    notification = Notification.query.filter_by(id=notification_id, user_id=current_user.id).first()
    if notification:
        notification.is_read = True
        db.session.commit()
        return jsonify({'status': 'success'})
    return jsonify({'status': 'error', 'message': 'Notification not found'}), 404
