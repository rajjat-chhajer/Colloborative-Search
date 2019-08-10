from .models import User, get_todays_recent_posts
from flask import Flask, request, session, redirect, url_for, render_template, flash

app = Flask(__name__)

@app.route('/')
def index():
    posts = get_todays_recent_posts()
    return render_template('index.html', posts=posts)


@app.route('/register', methods=['GET','POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        if len(username) < 1:
            flash('Your username must be at least one character.')
        elif len(password) < 5:
            flash('Your password must be at least 5 characters.')
        elif not User(username).register(password):
            flash('A user with that username already exists.')
        else:
            session['username'] = username
            flash('Logged in.')
            return redirect(url_for('index'))

    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        if not User(username).verify_password(password):
            flash('Invalid login.')
        else:
            session['username'] = username
            flash('Logged in.')
            return redirect(url_for('index'))

    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('username', None)
    flash('Logged out.')
    return redirect(url_for('index'))

@app.route('/add_post', methods=['POST'])
def add_post():
    title = request.form['title']
    tags = request.form['tags']
    text = request.form['text']

    if not title:
        flash('You must give your post a title.')
    elif not tags:
        flash('You must give your post at least one tag.')
    elif not text:
        flash('You must give your post a text body.')
    else:
        User(session['username']).add_post(title, tags, text)

    return redirect(url_for('index'))

@app.route('/add_reply/<post_id>', methods=['POST'])
def add_reply(post_id):
    username = session.get('username')
    text = request.form['reply']
    if not username:
        flash('You must be logged in to reply to a post.')
    elif not text:
        flash('You must give your post a text body.')
    else:
        User(username).add_reply(post_id,text)

    return redirect(url_for('index'))


@app.route('/indexpost/<post_id>')
def indexpost(post_id):
    username = session.get('username')
    posts = User(username).show_post(post_id)
    answers = User(username).show_ans(post_id)
    return render_template('show_post.html', posts=posts , answers= answers)


@app.route('/show_post/<post_id>', methods=['POST'])
def show_post(post_id):
    username = session.get('username')
    text = request.form['reply']
    if not username:
        flash('You must be logged in to reply to a post.')
    elif not text:
        flash('You must give your post a text body.')
    else:
        User(username).add_reply(post_id,text)
	return redirect(url_for('indexpost', post_id=post_id ))

@app.route('/show_answers/<post_id>', methods=['GET'])
def show_answers(post_id):
    username = session.get('username')
    if not username:
        flash('You must be logged in to reply to a post.')
	return redirect(url_for('login'))
    else:
        return redirect(url_for('indexpost', post_id=post_id ))


@app.route('/like_post/<post_id>/<reply_id>')
def like_post(post_id,reply_id):
    username = session.get('username')

    if not username:
        flash('You must be logged in to like a post.')
        return redirect(url_for('login'))

    User(username).like_post(post_id , reply_id)

    flash('Liked post.')
    return redirect(url_for('indexpost', post_id=post_id ))

@app.route('/search_posts', methods=['POST'])
def search_posts():
    username = session.get('username')
    searchtag = request.form['tag']
    if not username:
        flash('You must be logged in to search a post.')
	return redirect(url_for('login'))
    elif not searchtag:
        flash('You must give a searchtag.')
    else:
        posts = User(username).search_posts(searchtag)
        return render_template('search.html', posts=posts)

@app.route('/profile/<username>')
def profile(username):
    logged_in_username = session.get('username')
    user_being_viewed_username = username

    user_being_viewed = User(user_being_viewed_username)
    posts = user_being_viewed.get_recent_posts()

    similar = []
    common = []

    if logged_in_username:
        logged_in_user = User(logged_in_username)

        if logged_in_user.username == user_being_viewed.username:
            similar = logged_in_user.get_similar_users()
        else:
            common = logged_in_user.get_commonality_of_user(user_being_viewed)

    return render_template(
        'profile.html',
        username=username,
        posts=posts,
        similar=similar,
        common=common
    )
