from flask import render_template, flash, redirect, url_for, request
from app import app, db
from app.forms import LoginForm, RegisterForm, EditProfileForm, PostForm
from flask_login import current_user, login_user, logout_user, login_required
from app.models import User, Post
from datetime import datetime

@app.before_request
def before_request():
    if current_user.is_authenticated:
        current_user.last_seen = datetime.utcnow()
        db.session.commit()

@app.route('/')
def index():
    return render_template('index.html', title='Welcome Page')

@app.route('/explore')
@login_required
def explore():
    page = request.args.get('page', 1, type=int)
    posts = Post.query.order_by(Post.timestamp.desc()).paginate(page, app.config['POSTS_PER_PAGE'], False)
    next_url = url_for('explore', page=posts.next_num) \
        if posts.has_next else None
    prev_url = url_for('explore', page=posts.prev_num)  \
        if posts.has_prev else None
    return render_template('explore.html', title='Let\'s Explore!', posts=posts.items, next_url=next_url, prev_url=prev_url)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form  = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user is None or not user.check_password(form.password.data):
            flash('Invalid Input, Please Try Again')
            return redirect(url_for('login'))
        login_user(user, remember=form.remember_me.data)
        return redirect(url_for('home'))
    return render_template('login.html', title='Login Page', form=form)

@app.route('/logout')
@ login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = RegisterForm()
    if form.validate_on_submit():
        user = User(username=form.username.data, first_name=form.first_name.data, 
        last_name=form.last_name.data, email=form.email.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('Congrats! You have been registered!')
        return redirect(url_for('login'))
    return render_template('register.html', title='Register', form=form)

@app.route('/user_profile/<username>')
@login_required
def user_profile(username):
    page = request.args.get('page', 1, type=int)
    user = User.query.filter_by(username=username).first_or_404()
    posts = user.posts.order_by(Post.timestamp.desc()).paginate(page, app.config['POSTS_PER_PAGE'], False)
    next_url = url_for('user_profile', username=user.username, page=posts.next_num) \
        if posts.has_next else None
    prev_url = url_for('user_profile', username=user.username, page=posts.prev_num) \
        if posts.has_prev else None
    return render_template('user_profile.html', user=user, posts=posts.items, next_url=next_url, prev_url=prev_url)

@app.route('/home', methods=['GET', 'POST'])
@ login_required
def home():
    page = request.args.get('page', 1, type=int)
    posts = current_user.followed_posts().paginate(
        page, app.config['POSTS_PER_PAGE'], False)
    next_url = url_for('home', page=posts.next_num) \
        if posts.has_next else None
    prev_url = url_for('home', page=posts.prev_num) \
        if posts.has_prev else None   
    form = PostForm()
    if form.validate_on_submit():
        db.session.add(Post(body=form.body.data, user_id=current_user.id, timestamp=datetime.utcnow()))
        db.session.commit()
        flash('You\'ve just added a new post')
        return redirect(url_for('home'))
    return render_template('home.html', title='Homepage', form=form, posts=posts.items, next_url=next_url, prev_url=prev_url)

@app.route('/edit_profile', methods=['GET', 'POST'])
@ login_required
def edit_profile():
    form = EditProfileForm()
    if form.validate_on_submit():
        if not User.query.filter_by(username=form.username.data).first():
            current_user.username = form.username.data
            current_user.about_me = form.about_me.data
            db.session.commit()
            flash('Your profile has been successfully updated!')
            return redirect(url_for('user_profile', username=current_user.username))
        elif current_user.username == form.username.data:
            return redirect(url_for('user_profile', username=current_user.username))
        else:
            flash('Username used by someone else')
            return redirect(url_for('edit_profile'))
    elif request.method == 'GET':
        form.username.data = current_user.username
        form.about_me.data = current_user.about_me
    return render_template('edit_profile.html', form=form, title='Edit Profile')

@app.route('/follow/<username>')
@ login_required
def follow(username):
    user = User.query.filter_by(username=username).first()
    if user is None:
        flash('User doesn\'t exist')
        return redirect(url_for('home'))
    elif user == current_user:
        flash('You can\'t follow yourself!')
        return redirect(url_for('user_profile', username=username))
    current_user.follow(user)
    db.session.commit()
    flash(f'You are now following {username}')
    return redirect(url_for('user_profile', username=username))

@app.route('/unfollow/<username>')
@login_required
def unfollow(username):
    user = User.query.filter_by(username=username).first()
    if user is None:
        flash('User doesn\'t exist')
        return redirect(url_for('home'))
    elif user == current_user:
        flash('You can\'t unfollow yourself!')
        return redirect(url_for('user_profile', username=username))
    current_user.unfollow(user)
    db.session.commit()
    flash(f'You have unfollowed {username}')
    return redirect(url_for('user_profile', username=username))

@app.route('/delete_post/<int:id>')
@login_required
def delete_post(id):
    db.session.delete(Post.query.get(id))
    db.session.commit()
    return redirect(url_for('home'))

@app.route('/edit_post/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_post(id):
    post = Post.query.get_or_404(id)
    if request.method == 'POST':
        post.body = request.form['body']
        db.session.commit()
        return redirect(url_for('home'))
    else:
        return render_template('edit_post.html', post=post, title='Edit Post')

        