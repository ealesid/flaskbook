from flask import render_template, flash, redirect, url_for, request, current_app, abort, make_response
from flask_login import login_required, current_user

from app.decorators import admin_required, permission_required
from app.models import Permission
from . import main
from .forms import EditProfileForm, EditProfileAdminForm, PostForm
from ..models import Role, User, Post, Follow, FollowedPosts


@main.route('/', methods=['GET', 'POST'])
def index():
    form = PostForm()
    if current_user.can(Permission.WRITE_ARTICLES) and form.validate_on_submit():
        post = Post(body=form.body.data,
                    author_id=User.objects(username=current_user.username).first())
        post.save()
        return redirect(url_for('.index'))
    page = request.args.get('page', 1, type=int)
    show_followed = False
    if current_user.is_authenticated:
        show_followed = bool(request.cookies.get('show_followed', ''))
    if show_followed:
        current_user.followed_posts
        query = FollowedPosts.objects
    else: query = Post.objects
    pagination = query.order_by('-timestamp').paginate(
        page, per_page=current_app.config['FLASKBOOK_POSTS_PER_PAGE'],
        error_out=False)
    posts = pagination.items
    return render_template(
        'index.html',
        form=form, posts=posts, show_followed=show_followed, pagination=pagination)


@main.route('/user/<username>')
def user(username):
    user = User.objects(username=username).first_or_404()
    page = request.args.get('page', 1, type=int)
    pagination = Post.objects(author_id=user).order_by('-timestamp').paginate(
        page, per_page=current_app.config['FLASKBOOK_POSTS_PER_PAGE'],
        error_out=False)
    posts = pagination.items
    return render_template('user.html', user=user, posts=posts, pagination=pagination)


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


@main.route('/post/<string:id>')
def post(id):
    post = Post.objects(id=id).first()
    return render_template('post.html', posts=[post])


@main.route('/edit/<string:id>', methods=['GET', 'POST'])
@login_required
def edit(id):
    post = Post.objects(id=id).first()
    if current_user != post.author_id and not current_user.can(Permission.ADMINISTER):
        abort(403)
    form = PostForm()
    if form.validate_on_submit():
        post.body = form.body.data
        post.save()
        flash('The post has been updated.')
        return redirect(url_for('.post', id=post.id))
    form.body.data = post.body
    return render_template('edit_post.html', form=form)


@main.route('/follow/<username>')
@login_required
@permission_required(Permission.FOLLOW)
def follow(username):
    user = User.objects(username=username).first()
    if user is None:
        flash('Invalid user')
        return redirect(url_for('.index'))
    if Follow.is_following(current_user.id, user.id).first() is not None:
        flash("You're already following this user.")
        return redirect(url_for('.user', username=username))
    current_user.follow(user)
    flash('You are now following %s.' % username)
    return redirect(url_for('.user', username=username))


@main.route('/unfollow/<username>')
@login_required
@permission_required(Permission.FOLLOW)
def unfollow(username):
    user = User.objects(username=username).first()
    if user is None:
        flash('Invalid user')
        return redirect(url_for('.index'))
    if not current_user.is_following(user):
        flash("You're not following this user.")
        return redirect(url_for('.user', username=username))
    current_user.unfollow(user)
    flash("You're not following %s anymore." % username)
    return redirect(url_for('.user', username=username))


@main.route('/followers/<username>')
def followers(username):
    user = User.objects(username=username).first()
    if user is None:
        flash('Invalid user')
        return redirect(url_for('.index'))
    page = request.args.get('page', 1, type=int)
    pagination = Follow.objects(followed=user).paginate(
        page, per_page=current_app.config['FLASKBOOK_FOLLOWERS_PER_PAGE'],
        error_out=False)
    follows = [{'user': item.follower, 'timestamp': item.timestamp}
               for item in pagination.items]
    return render_template('followers.html', user=user, title='Followers of',
                           endpoint='.followers', pagination=pagination, follows=follows)


@main.route('/followed-by/<username>')
def followed_by(username):
    user = User.objects(username=username).first()
    if user is None:
        flash('Invalid user')
        return redirect(url_for('.index'))
    page = request.args.get('page', 1, type=int)
    pagination = Follow.objects(follower=user).paginate(
        page, per_page=current_app.config['FLASKBOOK_FOLLOWERS_PER_PAGE'],
        error_out=False)
    follows = [{'user': item.followed, 'timestamp': item.timestamp}
               for item in pagination.items]
    return render_template('followers.html', user=user, title='Followed by',
                           endpoint='.followed_by', pagination=pagination, follows=follows)


@main.route('/all')
@login_required
def show_all():
    resp = make_response(redirect(url_for('.index')))
    resp.set_cookie('show_followed', '', max_age=30*24*60*60)
    return resp


@main.route('/followed')
@login_required
def show_followed():
    resp = make_response(redirect(url_for('.index')))
    resp.set_cookie('show_followed', '1', max_age=30*24*60*60)
    return resp
