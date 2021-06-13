import os
import sqlite3
import secrets
from PIL import Image
import requests
import gmplot 
from flask import Flask
from flask import render_template, url_for, flash, redirect, request, abort
from flask_autoindex import AutoIndex
from MedCop import app, db, bcrypt
from MedCop.forms import RegistrationForm, LoginForm, UpdateAccountForm
from MedCop.models import User
from werkzeug.utils import secure_filename
from flask_login import login_user, current_user, logout_user, login_required
ppath = "/"
UPLOAD_FOLDER = os.path.dirname(os.path.abspath(__file__)) + '/uploads/'
ALLOWED_EXTENSIONS = {'pdf', 'txt'}
DIR_PATH = os.path.dirname(os.path.realpath(__file__))
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 8 * 1024 * 1024 
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS
@app.route('/upload', methods=['GET', 'POST'])
@login_required
def upload():
    if request.method == 'POST':
        if 'file' not in request.files:
            print('No file attached in request')
            return redirect(request.url)
        file = request.files['file']
        if file.filename == '':
            print('No file selected')
            return redirect(request.url)
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            flash("Your Report is uploaded successfully",'success')
    return render_template('upload.html')
@app.route("/")
@app.route("/home")
def home():
    return render_template('home.html')


@app.route("/about")
def about():
    return render_template('about.html', title='About')


@app.route("/register", methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = RegistrationForm()
    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        user = User(username=form.username.data, email=form.email.data, password=hashed_password)
        db.session.add(user)
        db.session.commit()
        flash('Your account has been created! You are now able to log in', 'success')
        return redirect(url_for('login'))
    return render_template('register.html', title='Register', form=form)


@app.route("/login", methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and bcrypt.check_password_hash(user.password, form.password.data):
            login_user(user, remember=form.remember.data)
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('home'))
        else:
            flash('Login Unsuccessful. Please check email and password', 'danger')
    return render_template('login.html', title='Login', form=form)

# @app.route("/uploaded_folder", methods=['GET'])
# def uploaded_folder():
#     ppath = "/" 
#     uploaded_folder = Flask(__name__)
#     return AutoIndex(uploaded_folder, browse_root=ppath)  
files_index = AutoIndex(app, os.path.curdir+'/MedCop/uploads', add_url_rules=False)
# Custom indexing
@app.route('/files')
@app.route('/files/<path:path>')
@login_required
def autoindex(path='.'):
    return files_index.render_autoindex(path)

@app.route("/logout")
def logout():
    logout_user()
    return redirect(url_for('home'))


def save_picture(form_picture):
    random_hex = secrets.token_hex(8)
    _, f_ext = os.path.splitext(form_picture.filename)
    picture_fn = random_hex + f_ext
    picture_path = os.path.join(app.root_path, 'static/profile_pics', picture_fn)

    output_size = (125, 125)
    i = Image.open(form_picture)
    i.thumbnail(output_size)
    i.save(picture_path)

    return picture_fn


@app.route("/account", methods=['GET', 'POST'])
@login_required
def account():
    form = UpdateAccountForm()
    if form.validate_on_submit():
        if form.picture.data:
            picture_file = save_picture(form.picture.data)
            current_user.image_file = picture_file
        current_user.username = form.username.data
        current_user.email = form.email.data
        db.session.commit()
        flash('Your account has been updated!', 'success')
        return redirect(url_for('account'))
    elif request.method == 'GET':
        form.username.data = current_user.username
        form.email.data = current_user.email
    image_file = url_for('static', filename='profile_pics/' + current_user.image_file)
    return render_template('account.html', title='Account',
                           image_file=image_file, form=form)

@app.route("/skin")
@login_required
def skin1():
    return redirect('http://localhost:5000',302)
@app.route("/ChatBot")
@login_required
def bot():
    return redirect('http://127.0.0.1:5002',302)
@app.route('/GPS')
@login_required
def locate():
    conn = sqlite3.connect('Doctor_Data.db')
    ip_request = requests.get('https://get.geojs.io/v1/ip.json')
    my_ip = ip_request.json()['ip']
    geo_request_url = 'https://get.geojs.io/v1/ip/geo/' + my_ip + '.json'
    geo_request = requests.get(geo_request_url)
    geo_data = geo_request.json()
    fetch = geo_data['city']
    sql = "SELECT ID,NAME,Hospital,Location,ADDRESS,Mobile FROM Doc_dat WHERE Location = :id"
    param = {'id' : fetch}
    cursor = conn.execute(sql,param)
    data = cursor.fetchall()
    return render_template('doctable.html',data=data)
        
    