from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from flask_marshmallow import Marshmallow
from flask_cors import CORS

app = Flask(__name__)
CORS(app)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///microblog.db'
db = SQLAlchemy(app)
ma = Marshmallow(app)

# Define models
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)

    def __init__(self, username, password):
        self.username = username
        self.password = password

class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    content = db.Column(db.Text, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    def __init__(self, title, content, user_id):
        self.title = title
        self.content = content
        self.user_id = user_id

class Like(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    post_id = db.Column(db.Integer, db.ForeignKey('post.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    def __init__(self, post_id, user_id):
        self.post_id = post_id
        self.user_id = user_id

class Comment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    post_id = db.Column(db.Integer, db.ForeignKey('post.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    content = db.Column(db.Text, nullable=False)

    def __init__(self, post_id, user_id, content):
        self.post_id = post_id
        self.user_id = user_id
        self.content = content

# Define schemas
class UserSchema(ma.Schema):
    class Meta:
        fields = ('id', 'username', 'password')

class PostSchema(ma.Schema):
    class Meta:
        fields = ('id', 'title', 'content', 'user_id')

class LikeSchema(ma.Schema):
    class Meta:
        fields = ('id', 'post_id', 'user_id')

class CommentSchema(ma.Schema):
    class Meta:
        fields = ('id', 'post_id', 'user_id', 'content')

# Initialize schemas
user_schema = UserSchema()
users_schema = UserSchema(many=True)
post_schema = PostSchema()
posts_schema = PostSchema(many=True)
like_schema = LikeSchema()
likes_schema = LikeSchema(many=True)
comment_schema = CommentSchema()
comments_schema = CommentSchema(many=True)

# Define routes
@app.route('/register', methods=['POST'])
def register():
    new_user = User(
        username=request.json['username'],
        password=request.json['password']
    )
    db.session.add(new_user)
    db.session.commit()
    return jsonify({'message': 'New user created!'})

@app.route('/login', methods=['POST'])
def login():
    user = User.query.filter_by(username=request.json['username'], password=request.json['password']).first()
    if user:
        return jsonify({'message': 'Logged in successfully!'})
    else:
        return jsonify({'message': 'Invalid credentials!'}), 401

@app.route('/posts', methods=['GET', 'POST'])
def posts():
    if request.method == 'GET':
        all_posts = Post.query.all()
        result = posts_schema.dump(all_posts)
        return jsonify(result)
    elif request.method == 'POST':
        new_post = Post(
            title=request.json['title'],
            content=request.json['content'],
            user_id=request.json['user_id']
        )
        db.session.add(new_post)
        db.session.commit()
        return jsonify({'message': 'New post created!'})

@app.route('/posts/<id>', methods=['GET', 'PUT', 'DELETE'])
def post(id):
    post = Post.query.get(id)
    if post:
        if request.method == 'GET':
            return post_schema.jsonify(post)
        elif request.method == 'PUT':
            post.title = request.json['title']
            post.content = request.json['content']
            db.session.commit()
            return jsonify({'message': 'Post updated!'})
        elif request.method == 'DELETE':
            db.session.delete(post)
            db.session.commit()
            return jsonify({'message': 'Post deleted!'})
    else:
        return jsonify({'message': 'Post not found!'}), 404

@app.route('/likes', methods=['GET', 'POST'])
def likes():
    if request.method == 'GET':
        all_likes = Like.query.all()
        result = likes_schema.dump(all_likes)
        return jsonify(result)
    elif request.method == 'POST':
        new_like = Like(
            post_id=request.json['post_id'],
            user_id=request.json['user_id']
        )
        db.session.add(new_like)
        db.session.commit()
        return jsonify({'message': 'New like created!'})

@app.route('/comments', methods=['GET', 'POST'])
def comments():
    if request.method == 'GET':
        all_comments = Comment.query.all()
        result = comments_schema.dump(all_comments)
        return jsonify(result)
    elif request.method == 'POST':
        new_comment = Comment(
            post_id=request.json['post_id'],
            user_id=request.json['user_id'],
            content=request.json['content']
        )
        db.session.add(new_comment)
        db.session.commit()
        return jsonify({'message': 'New comment created!'})

if __name__ == '__main__':
    app.run(port=5019)
