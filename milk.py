from flask import Flask, request, render_template, session, redirect, url_for, flash
from flask_mail import Mail, Message
from functools import wraps
from datetime import timedelta, date
from itertools import cycle, count
from collections import OrderedDict
from passlib.hash import sha256_crypt
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from wtforms import StringField, IntegerField, PasswordField, DateField, SelectField, TextField, validators
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
import atexit


app = Flask(__name__)
app.config.from_pyfile('config.py')
db = SQLAlchemy(app)
mail = Mail(app)
cron = BackgroundScheduler(
	jobstores={'default': SQLAlchemyJobStore(url=app.config['SQLALCHEMY_DATABASE_URI'])}
	)


# Decorator for admin login requirements
def login_required(f):
	@wraps(f)
	def decorated_function(*args, **kwargs):
		if not session.get('admin'):
			return redirect(url_for('login'))
		return f(*args, **kwargs)
	return decorated_function


class Settings(db.Model):
	id = db.Column(db.Integer, primary_key=True)
	user = db.Column(db.String(20), default='admin')
	passwd = db.Column(db.String(100), nullable=False, default=sha256_crypt.encrypt('admin'))
	offset = db.Column(db.Integer, nullable=False, default=0)
	period = db.Column(db.Integer, nullable=False, default=7)
	starts = db.Column(db.Date, nullable=False, default=date(2018,1,1))
	display = db.Column(db.String(50), default='Milk App')
	subject = db.Column(db.String(100), default='Reminder: Buy Milk')
	body = db.Column(db.Text, nullable=False, default='Please buy milk. Thank you!')
	hour = db.Column(db.Integer, nullable=False, default=7)


class Milkmen(db.Model):
	id = db.Column(db.Integer, primary_key=True)
	name = db.Column(db.String(20), nullable=False)
	email = db.Column(db.String(50))
	active = db.Column(db.Boolean, default=True)


class LoginForm(FlaskForm):
	user = StringField('', [validators.DataRequired()])
	passwd = PasswordField('', [validators.DataRequired()])


class UserForm(FlaskForm):
	name = StringField('', [validators.DataRequired()])
	email = StringField('')


class ChangePasswordForm(FlaskForm):
	user = StringField('', [validators.DataRequired()])
	passwd = PasswordField('Password', [
		validators.DataRequired(),
		validators.Length(min=6, message='Too short!'), 
		validators.EqualTo('passwd2', message='Passwords must match!'),
		])
	passwd2 = PasswordField('', [validators.DataRequired()])


class SettingsForm(FlaskForm):
	offset = IntegerField('Offset')
	starts = DateField('Start Date', [validators.DataRequired()])
	period = SelectField(
		label='How Frequently', 
		choices=[('1', 'Everyday'), ('2', 'Every 2 days'), ('3', 'Every 3 days'), ('7', 'Weekly'), ('14', 'Bi-Weekly')],
		)


class EmailForm(FlaskForm):
	display = StringField('From Name', [validators.DataRequired()])
	subject = StringField('Subject', [validators.DataRequired()])
	body = TextField('E-Mail Body', [validators.DataRequired()])
	hour = SelectField('Send Time At', choices=[(h, '{}:00'.format(h.zfill(2))) for h in map(str,range(24))])


# Milkman finder algorithm
def milkmen(get_first=False):
	D = []
	s = Settings.query.one_or_none()
	milkmen = Milkmen.query.filter_by(active=True)
	for p,d in zip(cycle(milkmen), count(s.period * s.offset, s.period)):
		new_date = s.starts + timedelta(days=d)
		if new_date > (date.today() - timedelta(days=s.period)):
			p.buy_date = new_date
			D.append(p)
			if len(D) == milkmen.count() or get_first:
				break
	return D


@app.route('/')
def index():
	return render_template("index.html", data=milkmen())


@app.route('/admin', methods=['GET', 'POST'])
def login():
	if session.get('admin'):
		return redirect('/dashboard')
	form = LoginForm(request.form)
	if request.method == 'POST' and form.validate_on_submit():
		U = Settings.query.filter_by(user=form.user.data).first()
		if U and sha256_crypt.verify(form.passwd.data, U.passwd):
			session.update({'admin': True})
			return redirect('/dashboard')
		else:
			flash('Wrong login credentials!', category='danger')
	return render_template('login.html', form=form)


@app.route('/dashboard', methods=['GET', 'POST'])
@login_required
def dashboard():
	settings = Settings.query.get_or_404(1)
	form = SettingsForm(request.form, obj=settings)
	if request.method == 'POST' and 'controls' in request.form and form.validate_on_submit():
		form.populate_obj(settings)
		db.session.commit()
		return redirect('/dashboard')
	if request.method == 'POST' and 'move_offset' in request.form:
		move = request.form.get('move_offset')
		if move == 'up': settings.offset -= 1
		if move == 'down': settings.offset += 1
		db.session.commit()
		return redirect('/dashboard')
	return render_template('dashboard.html', form=form, data=milkmen())


@app.route('/change-password', methods=['GET', 'POST'])
@login_required
def change_password():
	settings = Settings.query.get_or_404(1)
	form = ChangePasswordForm(request.form)
	form.user.data = settings.user
	if request.method == 'POST' and form.validate_on_submit():
		settings.user = request.form.get('user')
		settings.passwd = sha256_crypt.encrypt(request.form.get('passwd'))
		db.session.commit()
		flash('Your login detalils were changed!', category='success')
		return redirect('/change-password')
	return render_template('change_pw.html', form=form)


@app.route('/manage', methods=['GET', 'POST'])
@login_required
def user_manage():
	form = UserForm(request.form)
	if request.method == 'POST':
		if 'active_user' in request.form:
			user = Milkmen.query.get_or_404(request.form.get('active_user'))
			user.active = not user.active
		elif 'del_user' in request.form:
			user = Milkmen.query.get_or_404(request.form.get('del_user'))
			db.session.delete(user)
		elif 'add_user' in request.form and form.validate_on_submit():
			new = Milkmen(name=form.name.data, email=form.email.data)
			db.session.add(new)
		db.session.commit()
		return redirect('/manage')
	users = Milkmen.query.all()
	return render_template('manage.html', users=users, form=form, action='Add')


@app.route('/manage/<int:user>', methods=['GET', 'POST'])
@login_required
def user_edit(user=None):
	user = Milkmen.query.get_or_404(user)
	form = UserForm(request.form, obj=user)
	if request.method == 'POST' and form.validate_on_submit():
		form.populate_obj(user)
		db.session.commit()
		return redirect('/manage')
	users = Milkmen.query.all()
	return render_template('manage.html', users=users, form=form, action='Save')


@app.route('/email-settings', methods=['GET', 'POST'])
@login_required
def email_settings():
	settings = Settings.query.get_or_404(1)
	form = EmailForm(request.form, obj=settings)
	if request.method == 'POST' and form.validate_on_submit():
		form.populate_obj(settings)
		db.session.commit()
		job = cron.get_jobs()[0]
		cron.reschedule_job(job.id, trigger='cron', hour=settings.hour, minute=0)
		flash('Success! E-Mail Settings updated.', category='success')
		return redirect('/email-settings')
	return render_template('email.html', form=form)


@app.route('/logout')
def logout():
	session.clear()
	return redirect('/')


def send_mail():
	settings = Settings.query.get_or_404(1)
	milkman = milkmen(get_first=True)[0]
	if milkman.email and milkman.buy_date == date.today():
		msg = Message(
			subject=settings.subject,
			sender=(settings.display, app.config['MAIL_USERNAME']),
			recipients=[milkman.email],
		)
		msg.body = settings.body.format(name=milkman.name)
		with app.app_context():
			mail.send(msg)


@app.before_first_request
def start_cron():
	atexit.register(lambda: cron.shutdown(wait=False))
	settings = Settings.query.get_or_404(1)
	cron.add_job(send_mail, 'cron', hour=settings.hour, minute=0)
	cron.start()


# Initialises the DB and creates the admin user; run from CLI
def init_db():
	db.init_app(app)
	db.create_all()
	if not Settings.query.one_or_none():
		db.session.add(Settings())
		db.session.commit()


if __name__ == '__main__':
	app.run(debug=True)
