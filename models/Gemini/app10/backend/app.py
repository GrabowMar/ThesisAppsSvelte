from flask import Flask, jsonify, request
from flask_cors import CORS
import os
import datetime

app = Flask(__name__)
CORS(app)

# In-memory data store (replace with a database in a real application)
posts = []
users = {
    'default_user': {'username': 'default_user', 'bio': 'A default user.', 'profile_picture': 'https://via.placeholder.com/150'}
}
next_post_id = 1


# Utility function to format datetime
def format_datetime(dt):
    return dt.strftime("%Y-%m-%d %H:%M:%S")

# API Routes

@app.route('/api/posts', methods=['GET'])
def get_posts():
    query = request.args.get('q')  # Get search query
    filtered_posts = posts

    if query:
        filtered_posts = [
            post for post in posts
            if query.lower() in post['content'].lower() or query.lower() in post['author'].lower()
        ]

    # Sort posts by timestamp in descending order
    sorted_posts = sorted(filtered_posts, key=lambda x: x['timestamp'], reverse=True)

    return jsonify(sorted_posts)


@app.route('/api/posts', methods=['POST'])
def create_post():
    global next_post_id
    data = request.get_json()
    content = data.get('content')
    author = data.get('author', 'default_user') # Default author

    if not content:
        return jsonify({'error': 'Content is required'}), 400

    new_post = {
        'id': next_post_id,
        'author': author,
        'content': content,
        'likes': 0,
        'comments': [],
        'timestamp': datetime.datetime.now()  # Store the datetime object
    }
    next_post_id += 1
    posts.append(new_post)
    return jsonify(new_post), 201


@app.route('/api/posts/<int:post_id>', methods=['GET'])
def get_post(post_id):
    post = next((post for post in posts if post['id'] == post_id), None)
    if post:
        # Convert datetime to string before sending
        post['timestamp'] = format_datetime(post['timestamp'])
        return jsonify(post)
    return jsonify({'error': 'Post not found'}), 404


@app.route('/api/posts/<int:post_id>', methods=['PUT'])
def update_post(post_id):
    post = next((post for post in posts if post['id'] == post_id), None)
    if not post:
        return jsonify({'error': 'Post not found'}), 404

    data = request.get_json()
    content = data.get('content')
    if not content:
        return jsonify({'error': 'Content is required'}), 400

    post['content'] = content
    return jsonify(post)


@app.route('/api/posts/<int:post_id>', methods=['DELETE'])
def delete_post(post_id):
    global posts
    posts = [post for post in posts if post['id'] != post_id]
    return jsonify({'message': 'Post deleted'})


@app.route('/api/posts/<int:post_id>/like', methods=['POST'])
def like_post(post_id):
    post = next((post for post in posts if post['id'] == post_id), None)
    if not post:
        return jsonify({'error': 'Post not found'}), 404

    post['likes'] += 1
    return jsonify(post)


@app.route('/api/posts/<int:post_id>/comment', methods=['POST'])
def add_comment(post_id):
    post = next((post for post in posts if post['id'] == post_id), None)
    if not post:
        return jsonify({'error': 'Post not found'}), 404

    data = request.get_json()
    comment = data.get('comment')
    if not comment:
        return jsonify({'error': 'Comment text is required'}), 400

    post['comments'].append(comment)
    return jsonify(post)


@app.route('/api/users/<string:username>', methods=['GET'])
def get_user(username):
    user = users.get(username)
    if user:
        return jsonify(user)
    return jsonify({'error': 'User not found'}), 404


@app.route('/api/users/<string:username>', methods=['PUT'])
def update_user(username):
    user = users.get(username)
    if not user:
        return jsonify({'error': 'User not found'}), 404

    data = request.get_json()
    bio = data.get('bio')
    profile_picture = data.get('profile_picture')

    if bio:
        user['bio'] = bio
    if profile_picture:
        user['profile_picture'] = profile_picture

    return jsonify(user)


# Error Handlers
@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Not found'}), 404

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.getenv('PORT', '5419')))
