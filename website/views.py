from flask import Blueprint, render_template, request, flash, redirect, url_for, jsonify
from flask_login import login_required, current_user
from .models import Post, User, Comment, Like
from . import db



views = Blueprint("views", __name__)


@views.route("/")
@views.route("/home")
@login_required
def home():
    email = request.form.get('email')
    users = User.query.all()
    user = User.query.filter_by(email=email).first()
    my_post = Post.query.filter_by(user=user).all()
    count = len(my_post)
    all_posts = Post.query.all()
    return render_template('home.html', count=count, user=current_user, posts=all_posts, users=users)




@views.route("/search", methods=['GET', 'POST'])
@login_required
def search():
    username = request.form.get("username")
    user = User.query.filter_by(username=username).first()
    my_post = Post.query.filter_by(user=user).all()
    count = len(my_post)
    users = User.query.all()
    return render_template('search.html', users=users, user=current_user, count=count, title=username)



@views.route("/create-post", methods=['GET', 'POST'])
@login_required
def create_post():
    if request.method == "POST":
        text = request.form.get('text')

        if not text:
            flash('Post cannot be empty', category='error')
        else:
            post = Post(text=text, author=current_user.id)
            db.session.add(post)
            db.session.commit()
            flash('Post created!', category='success')
            return redirect(url_for('views.home'))

    return render_template('create_post.html', user=current_user)


@views.route("/delete-post/<id>")
@login_required
def delete_post(id):
    post = Post.query.filter_by(id=id).first()

    if not post:
        flash("Post does not exist.", category='error')
    elif current_user.id != post.id:
        flash('You do not have permission to delete this post.', category='error')
    else:
        db.session.delete(post)
        db.session.commit()
        flash('Post deleted.', category='success')

    return redirect(url_for('views.home'))


@views.route("/posts/<username>")
@login_required
def posts(username):
    user = User.query.filter_by(username=username).first()

    if not user:
        flash('No user with that username exists.', category='error')
        return redirect(url_for('views.home'))

    posts = user.posts
    return render_template("posts.html", user=current_user, posts=posts, username=username)


@views.route("/create-comment/<post_id>", methods=['POST'])
@login_required
def create_comment(post_id):
    text = request.form.get('text')

    if not text:
        flash('Comment cannot be empty.', category='error')
    else:
        post = Post.query.filter_by(id=post_id)
        if post:
            comment = Comment(
                text=text, author=current_user.id, post_id=post_id)
            db.session.add(comment)
            db.session.commit()
        else:
            flash('Post does not exist.', category='error')

    return redirect(url_for('views.home'))


@views.route("/delete-comment/<comment_id>")
@login_required
def delete_comment(comment_id):
    comment = Comment.query.filter_by(id=comment_id).first()

    if not comment:
        flash('Comment does not exist.', category='error')
    elif current_user.id != comment.author and current_user.id != comment.post.author:
        flash('You do not have permission to delete this comment.', category='error')
    else:
        db.session.delete(comment)
        db.session.commit()

    return redirect(url_for('views.home'))

@views.route("/like-post/<post_id>", methods=['POST'])
@login_required
def like(post_id):
    post = Post.query.filter_by(id=post_id).first()
    like = Like.query.filter_by(
        author=current_user.id, post_id=post_id).first()

    if not post:
        return jsonify({'error': 'Post does not exist.'}, 400)
    elif like:
        db.session.delete(like)
        db.session.commit()
    else:
        like = Like(author=current_user.id, post_id=post_id)
        db.session.add(like)
        db.session.commit()

    return jsonify({"likes": len(post.likes), "liked": current_user.id in map(lambda x: x.author, post.likes)})



@login_required
@views.route('/profile/<username>', methods=['GET', 'POST'])
def profile(username):
    user = User.query.filter_by(username=username).first_or_404()
    posts = Post.query.filter_by(user=user).order_by(Post.date_created.desc()).all()
    count = len(posts)
    return render_template('profile.html', title=username, user=user, posts=posts, count=count)





@views.route('/unfollow/<username>')
@login_required
def unfollow(username):
    user = User.query.filter_by(username=username).first()
    if user is None:
        flash('User {} not found.'.format(username))
        return redirect(url_for('views.home'))
    if user == current_user:
        flash('You cannot unfollow yourself!')
        return redirect(url_for('views.profile', username=username))
    current_user.unfollow(user)
    db.session.commit()
    flash('You are not following {}.'.format(user.username))
    return redirect(url_for('views.profile', username=username, user=user))





@views.route('/follow/<username>', methods=['GET'])
@login_required
def follow(username):
    user = User.query.filter_by(username=username).first()
    if user is None:
        flash('User {} not found.'.format(user.username))
        return redirect(url_for('views.home'))
    if user == current_user:
        flash('You cannot follow yourself')
        return redirect(url_for('views.profile', username=username))
    current_user.follow(user)
    db.session.commit()
    flash('You are following {}!'.format(user.username))
    return redirect(url_for('views.profile', username=username, user=user))




@views.route('/profile_update', methods=['GET', 'POST'])
def profile_update():
    if current_user.is_authenticated:
        user_details = current_user.user_variables()
        user = User.query.filter_by(id=current_user.id).first()
        if request.method == 'POST':
            updated_values_dict = request.form.to_dict()
            for k, v in updated_values_dict.items():
                if k == 'update_username':
                    user.username = v.rstrip()
                if k == 'update_password':
                    user.password = v.rstrip()
            db.session.commit()
            return redirect(url_for('views.profile_update'))
    return render_template('profile_update.html', user_details=user_details, user=current_user)