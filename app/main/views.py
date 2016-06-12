import os

from flask_login import login_required

from app.decorators import admin_required, permission_required
from app.models import Permission
from flask import render_template, abort
from . import main
from ..models import User


@main.route('/')
def index():
    return render_template('index.html', emailto=[os.environ.get('FLASKBOOK_ADMIN')])


@main.route('/user/<username>')
def user(username):
    user = User.objects(username=username).first_or_404()
    return render_template('user.html', user=user)


@main.route('/admin')
@login_required
@admin_required
def for_admins_only():
    return 'For administrators only!!!'


@main.route('/moderator')
@login_required
@permission_required(Permission.MODERATE_COMMENTS)
def for_moderators_only():
    return 'For comment moderators!'
