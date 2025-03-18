from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS

app = Flask(__name__)
CORS(app)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///wiki.db'
db = SQLAlchemy(app)

class Page(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    content = db.Column(db.Text, nullable=False)
    version = db.Column(db.Integer, nullable=False)

@app.route('/pages', methods=['GET'])
def get_pages():
    pages = Page.query.all()
    return jsonify([{'id': page.id, 'title': page.title, 'content': page.content} for page in pages])

@app.route('/pages/<int:page_id>', methods=['GET'])
def get_page(page_id):
    page = Page.query.get_or_404(page_id)
    return jsonify({'id': page.id, 'title': page.title, 'content': page.content})

@app.route('/pages', methods=['POST'])
def create_page():
    data = request.json
    new_page = Page(title=data['title'], content=data['content'], version=1)
    db.session.add(new_page)
    db.session.commit()
    return jsonify({'id': new_page.id, 'title': new_page.title, 'content': new_page.content})

@app.route('/pages/<int:page_id>', methods=['PUT'])
def update_page(page_id):
    data = request.json
    page = Page.query.get_or_404(page_id)
    page.title = data['title']
    page.content = data['content']
    page.version += 1
    db.session.commit()
    return jsonify({'id': page.id, 'title': page.title, 'content': page.content})

@app.route('/pages/<int:page_id>', methods=['DELETE'])
def delete_page(page_id):
    page = Page.query.get_or_404(page_id)
    db.session.delete(page)
    db.session.commit()
    return jsonify({'message': 'Page deleted'})

if __name__ == '__main__':
    db.create_all()
    app.run(port=5115)
