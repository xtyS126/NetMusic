# app.py
import os
import uuid
from datetime import datetime
from flask import Flask, render_template, url_for, redirect, flash, request, send_from_directory, abort, session
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from flask_wtf import FlaskForm
from sqlalchemy import select
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from mutagen.mp3 import MP3
from config import Config

# 应用配置
app = Flask(__name__)
app.config.from_object(Config)
db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'


# 初始化数据库
def init_db():
    with app.app_context():
        db.create_all()
        admin_exists = User.query.filter_by(username=app.config['ADMIN_USERNAME']).first()
        if not admin_exists:
            admin = User(
                username=app.config['ADMIN_USERNAME'],
                password_hash=generate_password_hash(app.config['ADMIN_PASSWORD']),
                is_admin=True
            )
            db.session.add(admin)
            db.session.commit()
        print("数据库初始化完成！")


# 数据库模型
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)
    musics = db.relationship('Music', backref='user', lazy=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class Music(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    original_name = db.Column(db.String(200))
    filename = db.Column(db.String(100))
    stored_name = db.Column(db.String(100), unique=True)
    duration = db.Column(db.Integer)
    upload_time = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)


# 表单类
class LoginForm(FlaskForm):
    username = StringField('用户名', validators=[DataRequired()])
    password = PasswordField('密码', validators=[DataRequired()])
    submit = SubmitField('登录')


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


# 路由
@app.route('/')
def index():
    return render_template('index.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user and user.check_password(form.password.data):
            login_user(user)
            return redirect(url_for('index'))
        flash('无效的用户名或密码', 'danger')
    return render_template('login.html', form=form)


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))


@app.route('/upload', methods=['GET', 'POST'])
def upload():
    if request.method == 'POST':
        if not os.path.exists(app.config['UPLOAD_FOLDER']):
            os.makedirs(app.config['UPLOAD_FOLDER'])

        file = request.files.get('file')
        if not file or file.filename == '':
            flash('请选择要上传的文件', 'danger')
            return redirect(url_for('upload'))

        if not file.filename.lower().endswith('.mp3'):
            flash('仅支持MP3格式文件', 'danger')
            return redirect(url_for('upload'))

        try:
            original_name = file.filename
            safe_name = secure_filename(original_name)
            unique_name = f"{uuid.uuid4()}.mp3"
            save_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_name)
            file.save(save_path)

            try:
                audio = MP3(save_path)
                duration = int(audio.info.length)
            except Exception as e:
                print(f"解析音频失败: {str(e)}")
                duration = None

            # 修改用户ID获取方式
            user_id = current_user.id if current_user.is_authenticated else None
            
            # 创建音乐记录时保留user_id字段
            music = Music(
                original_name=original_name,
                filename=safe_name,
                stored_name=unique_name,
                duration=duration,
                user_id=user_id  # 允许匿名用户时为None
            )
            db.session.add(music)
            db.session.commit()
            flash('上传成功！', 'success')
            return redirect(url_for('music_list'))
        except Exception as e:
            db.session.rollback()
            if os.path.exists(save_path):
                os.remove(save_path)
            flash(f'上传失败: {str(e)}', 'danger')
            return redirect(url_for('upload'))
    return render_template('upload.html')


@app.route('/music')
def music_list():
    page = request.args.get('page', 1, type=int)
    per_page = 10
    search_query = request.args.get('q', '')
    query = Music.query.order_by(Music.upload_time.desc())

    if search_query:
        query = query.filter(Music.original_name.ilike(f'%{search_query}%'))

    pagination = query.paginate(page=page, per_page=per_page)
    return render_template('music_list.html',
                           musics=pagination.items,
                           pagination=pagination,
                           search_query=search_query)


@app.route('/play/<filename>')
def play(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)


@app.route('/admin', methods=['GET', 'POST'])
@login_required
def admin():
    if not current_user.is_admin:
        abort(403)
    return redirect(url_for('admin_panel'))


@app.route('/delete/<int:music_id>', methods=['POST'])  # 确保这个路由在admin_panel之前定义
@login_required
def delete_music(music_id):
    music = Music.query.get_or_404(music_id)
    if not current_user.is_admin and music.user_id != current_user.id:
        abort(403)
    try:
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], music.stored_name)
        if os.path.exists(file_path):
            os.remove(file_path)
        db.session.delete(music)
        db.session.commit()
        flash('删除成功', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'删除失败: {str(e)}', 'danger')
    return redirect(url_for('music_list'))


# 保持其他路由顺序不变
@app.route('/admin/panel')
@login_required
def admin_panel():
    if not current_user.is_admin:
        abort(403)
    users = User.query.paginate(page=request.args.get('page', 1, type=int), per_page=10)
    musics = Music.query.all()
    return render_template('admin.html',
                           users=users,
                           music_list=musics,
                           pagination=users)


# 新增用户删除路由
@app.route('/admin/delete-user/<int:user_id>', methods=['POST'])
@login_required
def delete_user(user_id):
    if not current_user.is_admin:
        abort(403)
    user = User.query.get_or_404(user_id)
    try:
        for music in user.musics:
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], music.stored_name)
            if os.path.exists(file_path):
                os.remove(file_path)
            db.session.delete(music)
        db.session.delete(user)
        db.session.commit()
        flash('用户及其文件已删除', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'删除失败: {str(e)}', 'danger')
    return redirect(url_for('admin_panel'))


if __name__ == '__main__':
    init_db()
    app.run(debug=True, port=3355)
