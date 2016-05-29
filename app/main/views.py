import os
from datetime import datetime
from flask import render_template, redirect, session, url_for, current_app
from . import main
from .forms import NameForm
from ..models import User
from ..email import send_email

@main.route('/', methods=['GET', 'POST'])
def index():
    form = NameForm()
    if form.validate_on_submit():
        user = User.objects(username__exact=form.name.data).first()
        if user is None:
            user = User(username=form.name.data)
            user.save()
            session['known'] = False
            if current_app.config['FLASKBOOK_ADMIN']:
                send_email(current_app.config['FLASKBOOK_ADMIN'], 'New user', 'mail/new_user', user=user)
        else: session['known'] = True
        session['name'] = form.name.data
        form.name.data = ''
        return redirect(url_for('main.index'))
    return render_template('index.html',
                           form=form,
                           name=session.get('name'),
                           known=session.get('known', False),
                           current_time=datetime.utcnow(),
                           emailto=[os.environ.get('FLASKBOOK_ADMIN')])
