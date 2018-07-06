
import logging
from flask import Blueprint, current_app, render_template, flash, redirect, \
                  url_for
from flask_login import login_required, current_user
from werkzeug import generate_password_hash

from bootstrap import db
from web.views.common import admin_permission
from web import models
from web.forms import UserForm

logger = logging.getLogger(__name__)

admin_bp = Blueprint('admin_bp', __name__, url_prefix='/admin')


@admin_bp.route('/users', methods=['GET'])
@login_required
@admin_permission.require(http_exception=403)
def list_users():
    users = models.User.query.all()
    return render_template('admin/users.html', users=users)


@admin_bp.route('/user/create', methods=['GET'])
@admin_bp.route('/user/edit/<int:user_id>', methods=['GET'])
@login_required
@admin_permission.require(http_exception=403)
def form_user(user_id=None):
    """Return a form to create and edit a user."""
    action = "Add a user"
    head_titles = [action]
    form = UserForm()
    if user_id is None:
        return render_template('admin/edit_user.html', action=action,
                               head_titles=head_titles, form=form)

    user = models.User.query.filter(models.User.id == user_id).first()
    form = UserForm(obj=user)
    action = "Edit user"
    head_titles = [action]
    head_titles.append(user.login)
    return render_template('admin/edit_user.html', action=action,
                           head_titles=head_titles,
                           form=form, user=user)


@admin_bp.route('/user/create', methods=['POST'])
@admin_bp.route('/user/edit/<int:user_id>', methods=['POST'])
@login_required
def process_user_form(user_id=None):
    """Edit a user."""
    form = UserForm()

    if not form.validate():
        return render_template('admin/edit_user.html', form=form)

    if user_id is not None:
        user = models.User.query.filter(models.User.id == user_id).first()
        form.populate_obj(user)
        if form.password.data:
            user.pwdhash = generate_password_hash(form.password.data)
        db.session.commit()
        flash('User {} successfully updated.'.
                format(form.login.data), 'success')
        return redirect(url_for('admin_bp.form_user', user_id=user.id))

    # Create a new user
    new_user = models.User(login=form.login.data,
                           public_profile=form.public_profile.data,
                           is_active=form.is_active.data,
                           is_admin=form.is_admin.data,
                           is_api=form.is_api.data,
                           pwdhash=generate_password_hash(form.password.data))
    db.session.add(new_user)
    db.session.commit()
    flash('User %(user_login)s successfully created.'.
            format(user_login=new_user.login), 'success')

    return redirect(url_for('admin_bp.form_user', user_id=new_user.id))


@admin_bp.route('/user/toggle/<int:user_id>', methods=['GET'])
@login_required
@admin_permission.require(http_exception=403)
def toggle_user(user_id=None):
    """Activate/deactivate a user."""
    user = models.User.query.filter(models.User.id == user_id).first()
    if user.id == current_user.id:
        flash('You can not do this change to your own user.', 'danger')
    else:
        user.is_active = not user.is_active
        db.session.commit()
        flash('User {status}.'.format(status='activated' if user.is_active else 'deactivated'), 'success')
    return redirect(url_for('admin_bp.list_users'))


@admin_bp.route('/user/delete/<int:user_id>', methods=['GET'])
@login_required
@admin_permission.require(http_exception=403)
def delete_user(user_id=None):
    """Delete a user."""
    user = models.User.query.filter(models.User.id == user_id).first()
    if user.id == current_user.id:
        flash('You can not delete your own user.', 'danger')
    else:
        db.session.delete(user)
        db.session.commit()
        flash('User deleted.', 'success')
    return redirect(url_for('admin_bp.list_users'))


@admin_bp.route('/stats', methods=['GET'])
@login_required
@admin_permission.require(http_exception=403)
def list_stats():
    stats = models.Stat.query.all()
    return render_template('admin/stats.html', stats=stats)
