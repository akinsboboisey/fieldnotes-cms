import os
import re
from datetime import datetime

import markdown as md
from flask import Flask, render_template, redirect, url_for, request, flash, abort
from flask_sqlalchemy import SQLAlchemy
from flask_login import (
    LoginManager, UserMixin, login_user, logout_user,
    login_required, current_user
)
from werkzeug.security import generate_password_hash, check_password_hash

basedir = os.path.abspath(os.path.dirname(__file__))

app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "dev-secret-change-me")
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///" + os.path.join(basedir, "instance", "blog.db")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

os.makedirs(os.path.join(basedir, "instance"), exist_ok=True)

db = SQLAlchemy(app)

login_manager = LoginManager(app)
login_manager.login_view = "login"
login_manager.login_message = "Sign in to reach the dashboard."
login_manager.login_message_category = "notice"


# ---------------------------------------------------------------------------
# Models
# ---------------------------------------------------------------------------

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)

    def set_password(self, raw):
        self.password_hash = generate_password_hash(raw)

    def check_password(self, raw):
        return check_password_hash(self.password_hash, raw)


class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    slug = db.Column(db.String(220), unique=True, nullable=False)
    excerpt = db.Column(db.String(280), nullable=False)
    body_md = db.Column(db.Text, nullable=False)
    tags = db.Column(db.String(200), default="")
    published = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    @property
    def body_html(self):
        return md.markdown(self.body_md, extensions=["fenced_code", "tables"])

    @property
    def tag_list(self):
        return [t.strip() for t in self.tags.split(",") if t.strip()]

    @property
    def reading_minutes(self):
        words = len(re.findall(r"\w+", self.body_md))
        return max(1, round(words / 200))


@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))


def slugify(title):
    slug = re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")
    base = slug
    n = 1
    while Post.query.filter_by(slug=slug).first():
        n += 1
        slug = f"{base}-{n}"
    return slug


# ---------------------------------------------------------------------------
# Public routes
# ---------------------------------------------------------------------------

@app.route("/")
def index():
    posts = Post.query.filter_by(published=True).order_by(Post.created_at.desc()).all()
    return render_template("index.html", posts=posts)


@app.route("/post/<slug>")
def post_detail(slug):
    post = Post.query.filter_by(slug=slug).first_or_404()
    if not post.published and not current_user.is_authenticated:
        abort(404)
    return render_template("post_detail.html", post=post)


@app.route("/tag/<tag>")
def by_tag(tag):
    posts = [p for p in Post.query.filter_by(published=True).order_by(Post.created_at.desc()).all()
             if tag in p.tag_list]
    return render_template("index.html", posts=posts, active_tag=tag)


# ---------------------------------------------------------------------------
# Auth
# ---------------------------------------------------------------------------

@app.route("/admin/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard"))
    if request.method == "POST":
        user = User.query.filter_by(username=request.form.get("username", "")).first()
        if user and user.check_password(request.form.get("password", "")):
            login_user(user)
            return redirect(url_for("dashboard"))
        flash("Wrong username or password.", "error")
    return render_template("login.html")


@app.route("/admin/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("index"))


# ---------------------------------------------------------------------------
# Admin (CMS) routes
# ---------------------------------------------------------------------------

@app.route("/admin")
@login_required
def dashboard():
    posts = Post.query.order_by(Post.created_at.desc()).all()
    return render_template("dashboard.html", posts=posts)


@app.route("/admin/new", methods=["GET", "POST"])
@login_required
def new_post():
    if request.method == "POST":
        title = request.form["title"].strip()
        if not title:
            flash("A post needs a title.", "error")
            return render_template("post_form.html", post=None)
        post = Post(
            title=title,
            slug=slugify(title),
            excerpt=request.form.get("excerpt", "").strip()[:280],
            body_md=request.form.get("body_md", ""),
            tags=request.form.get("tags", ""),
            published="published" in request.form,
        )
        db.session.add(post)
        db.session.commit()
        flash("Post published.", "success")
        return redirect(url_for("dashboard"))
    return render_template("post_form.html", post=None)


@app.route("/admin/edit/<int:post_id>", methods=["GET", "POST"])
@login_required
def edit_post(post_id):
    post = db.session.get(Post, post_id) or abort(404)
    if request.method == "POST":
        post.title = request.form["title"].strip()
        post.excerpt = request.form.get("excerpt", "").strip()[:280]
        post.body_md = request.form.get("body_md", "")
        post.tags = request.form.get("tags", "")
        post.published = "published" in request.form
        db.session.commit()
        flash("Post updated.", "success")
        return redirect(url_for("dashboard"))
    return render_template("post_form.html", post=post)


@app.route("/admin/delete/<int:post_id>", methods=["POST"])
@login_required
def delete_post(post_id):
    post = db.session.get(Post, post_id) or abort(404)
    db.session.delete(post)
    db.session.commit()
    flash("Post deleted.", "notice")
    return redirect(url_for("dashboard"))


# ---------------------------------------------------------------------------
# First-run seed
# ---------------------------------------------------------------------------

def seed_if_empty():
    db.create_all()
    if not User.query.first():
        admin = User(username="admin")
        admin.set_password("changeme123")
        db.session.add(admin)

    if not Post.query.first():
        demo_posts = [
            Post(
                title="Why I Rebuilt My Portfolio as a CMS",
                slug="why-i-rebuilt-my-portfolio-as-a-cms",
                excerpt="Static pages were fine until I wanted to write more than I wanted to redeploy.",
                tags="flask, python, meta",
                body_md=(
                    "Every static portfolio site eventually hits the same wall: you want to "
                    "publish a new post, and instead you're editing HTML by hand.\n\n"
                    "## The fix\n\n"
                    "A tiny CMS built on Flask and SQLite removes that friction entirely. "
                    "Write in Markdown, hit publish, done.\n\n"
                    "```python\n"
                    "@app.route(\"/post/<slug>\")\n"
                    "def post_detail(slug):\n"
                    "    post = Post.query.filter_by(slug=slug).first_or_404()\n"
                    "    return render_template(\"post_detail.html\", post=post)\n"
                    "```\n\n"
                    "No build step, no external CMS subscription, and I own every line of it."
                ),
            ),
            Post(
                title="Notes on Training a Hybrid CNN + Decision Tree Pipeline",
                slug="notes-hybrid-cnn-decision-tree-pipeline",
                excerpt="Combining a ResNet-50 feature extractor with PCA and a decision tree, and what changed.",
                tags="machine-learning, computer-vision",
                body_md=(
                    "Pure CNN pipelines are powerful but heavy. For a defect-classification task "
                    "with a modest dataset, a hybrid approach ended up outperforming a hand-tuned "
                    "baseline by a wide margin.\n\n"
                    "## Pipeline\n\n"
                    "1. Extract features with a pretrained ResNet-50\n"
                    "2. Reduce dimensionality with PCA\n"
                    "3. Classify with a decision tree\n\n"
                    "The result: **80.22%** accuracy versus **65.27%** for the manual baseline. "
                    "Sometimes the win isn't a bigger model, it's a better feature pipeline."
                ),
            ),
            Post(
                title="Deploying a Flask App from a Phone",
                slug="deploying-flask-app-from-phone",
                excerpt="No laptop, no problem. A mobile-first workflow for shipping small Python apps.",
                tags="flask, workflow, mobile",
                body_md=(
                    "Most Flask tutorials assume a desktop terminal open next to your editor. "
                    "That's not always the setup you have.\n\n"
                    "## What actually works\n\n"
                    "- Write and review code in short, reviewable chunks\n"
                    "- Use a host with zero-config Python deploys\n"
                    "- Keep the repo structure simple: one `app.py`, templates, static\n\n"
                    "It's slower than a full IDE, but it's not a blocker."
                ),
            ),
        ]
        db.session.add_all(demo_posts)

    db.session.commit()


with app.app_context():
    seed_if_empty()


if __name__ == "__main__":
    app.run(debug=True)
