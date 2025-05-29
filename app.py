from flask import Flask, render_template, request, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from datetime import datetime
import os
import csv

app = Flask(__name__)
app.secret_key = 'bkute_secret_key'

# Cấu hình SQLite
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
UPLOAD_FOLDER = 'static/uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

db = SQLAlchemy(app)

# Mô hình người dùng
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    mssv = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)
    name = db.Column(db.String(100), default='Người dùng BKUTE')
    avatar = db.Column(db.String(200), default='default_avatar.png')

# Tạo bảng nếu chưa tồn tại
with app.app_context():
    db.create_all()

# Trang đăng nhập
@app.route('/')
def login():
    return render_template("login.html", message=None)

@app.route('/login', methods=['POST'])
def do_login():
    mssv = request.form.get('mssv')
    matkhau = request.form.get('matkhau')
    user = User.query.filter_by(mssv=mssv).first()
    if user and check_password_hash(user.password, matkhau):
        session['mssv'] = user.mssv
        return redirect(url_for('dashboard'))
    else:
        return render_template("login.html", message="❌ Sai tài khoản hoặc mật khẩu!")

# Trang đăng ký
@app.route('/register')
def register():
    return render_template("register.html", message=None)

@app.route('/register', methods=['POST'])
def do_register():
    mssv = request.form.get('mssv')
    matkhau = request.form.get('matkhau')
    xacnhan = request.form.get('xacnhan')
    if len(matkhau) < 6:
        return render_template("register.html", message="❌ Mật khẩu phải có ít nhất 6 ký tự!")
    if matkhau != xacnhan:
        return render_template("register.html", message="❌ Mật khẩu xác nhận không trùng khớp!")
    if User.query.filter_by(mssv=mssv).first():
        return render_template("register.html", message="⚠️ Tài khoản đã tồn tại!")

    hashed_pw = generate_password_hash(matkhau)
    new_user = User(mssv=mssv, password=hashed_pw)
    db.session.add(new_user)
    db.session.commit()
    return render_template("login.html", message="✅ Đăng ký thành công! Mời bạn đăng nhập.")

# Dashboard
@app.route('/dashboard')
def dashboard():
    if 'mssv' not in session:
        return redirect(url_for('login'))
    user = User.query.filter_by(mssv=session['mssv']).first()
    return render_template("dashboard.html", user=user)

# Cập nhật thông tin
@app.route('/update_profile', methods=['POST'])
def update_profile():
    if 'mssv' not in session:
        return redirect(url_for('login'))
    user = User.query.filter_by(mssv=session['mssv']).first()
    user.name = request.form.get('fullname')

    if 'avatar' in request.files:
        avatar = request.files['avatar']
        if avatar.filename:
            filename = secure_filename(avatar.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            avatar.save(filepath)
            user.avatar = filename

    db.session.commit()
    return redirect(url_for('dashboard'))

# Gửi góp ý
@app.route('/submit_feedback', methods=['POST'])
def submit_feedback():
    if 'mssv' not in session:
        return redirect(url_for('login'))

    content = request.form.get('feedback')
    mssv = session['mssv']
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    file_path = 'feedback.csv'
    file_exists = os.path.isfile(file_path)

    with open(file_path, mode='a', encoding='utf-8', newline='') as file:
        writer = csv.writer(file)
        if not file_exists:
            writer.writerow(['MSSV', 'Thời gian', 'Nội dung'])
        writer.writerow([mssv, timestamp, content])

    return redirect(url_for('dashboard'))


# Admin xem góp ý
@app.route('/admin/feedback')
def view_feedback():
    if 'mssv' not in session or session['mssv'] != '2111464':
        return "Bạn không có quyền truy cập!", 403

    feedback_list = []
    file_path = 'feedback.csv'
    if os.path.exists(file_path):
        with open(file_path, 'r', encoding='utf-8') as file:
            reader = csv.reader(file)
            next(reader)
            feedback_list = list(reader)

    return render_template("admin_feedback.html", feedbacks=feedback_list)

# Đăng xuất
@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)
