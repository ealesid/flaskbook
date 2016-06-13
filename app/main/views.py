import os

from flask import render_template, flash, redirect, url_for
from flask_login import login_required, current_user

from app.decorators import admin_required, permission_required
from app.models import Permission
from . import main
from .forms import EditProfileForm, EditProfileAdminForm
from ..models import Role, User


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


@main.route('/edit-profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
    form = EditProfileForm()
    if form.validate_on_submit():
        current_user.name = form.name.data
        current_user.location = form.location.data
        current_user.about_me = form.about_me.data
        current_user.save()
        flash('Your profile has been updated')
        return redirect(url_for('.user', username=current_user.username))
    form.name.data = current_user.name
    form.location.data = current_user.location
    form.about_me.data = current_user.about_me
    return render_template('edit_profile.html', form=form)


@main.route('/edit-profile/<userid>', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_profile_admin(userid):
    user = User.objects(username=userid).first()
    form = EditProfileAdminForm(user=user)
    if form.validate_on_submit():
        user.email = form.email.data
        user.username = form.username.data
        user.confirmed = form.confirmed.data
        user.role = Role.objects(name=form.role.data).first()
        user.name = form.name.data
        user.location = form.location.data
        user.about_me = form.about_me.data
        user.save()
        flash('The profile has been updated.')
        return redirect(url_for('.user', username=user.username))
    form.email.data = user.email
    form.username.data = user.username
    form.confirmed.data = user.confirmed
    form.role.data = user.role.name
    form.name.data = user.name
    form.location.data = user.location
    form.about_me.data = user.about_me
    return render_template('edit_profile.html', form=form, user=user)
