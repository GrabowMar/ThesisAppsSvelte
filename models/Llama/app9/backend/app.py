# 1. Imports Section
from flask import Flask, jsonify, request
from flask_cors import CORS
import os
import sqlite3
import json

# 2. App Configuration
app = Flask(__name__)
CORS(app)

# 3. Database Models (if needed)
# Create a connection to the SQLite database
def create_connection():
    conn = None
    try:
        conn = sqlite3.connect('inventory.db')
        print(sqlite3.version)
    except sqlite3.Error as e:
        print(e)
    return conn

# Create table
def create_table(conn):
    sql = """CREATE TABLE IF NOT EXISTS items (
                id integer PRIMARY KEY,
                name text NOT NULL,
                category text NOT NULL,
                quantity integer NOT NULL,
                stock_level text NOT NULL
            );"""
    try:
        c = conn.cursor()
        c.execute(sql)
    except sqlite3.Error as e:
        print(e)

# 4. Authentication Logic (if needed)
# No authentication logic is included in this example

# 5. Utility Functions
def get_all_items(conn):
    cur = conn.cursor()
    cur.execute("SELECT * FROM items")
    rows = cur.fetchall()
    return rows

def get_item(conn, id):
    cur = conn.cursor()
    cur.execute("SELECT * FROM items WHERE id=?", (id,))
    row = cur.fetchone()
    return row

def create_item(conn, item):
    sql = """INSERT INTO items(name,category,quantity,stock_level)
             VALUES(?,?,?,?)"""
    cur = conn.cursor()
    cur.execute(sql, item)
    conn.commit()
    return cur.lastrowid

def update_item(conn, item):
    sql = """UPDATE items
             SET name = ?, category = ?, quantity = ?, stock_level = ?
             WHERE id = ?"""
    cur = conn.cursor()
    cur.execute(sql, (item['name'], item['category'], item['quantity'], item['stock_level'], item['id']))
    conn.commit()

def delete_item(conn, id):
    sql = """DELETE FROM items WHERE id=?"""
    cur = conn.cursor()
    cur.execute(sql, (id,))
    conn.commit()

# 6. API Routes
@app.route('/api/items', methods=['GET'])
def get_items():
    conn = create_connection()
    rows = get_all_items(conn)
    items = []
    for row in rows:
        item = {
            'id': row[0],
            'name': row[1],
            'category': row[2],
            'quantity': row[3],
            'stock_level': row[4]
        }
        items.append(item)
    conn.close()
    return jsonify(items)

@app.route('/api/items/<id>', methods=['GET'])
def get_item_by_id(id):
    conn = create_connection()
    row = get_item(conn, int(id))
    if row is None:
        return jsonify({'error': 'Item not found'}), 404
    item = {
        'id': row[0],
        'name': row[1],
        'category': row[2],
        'quantity': row[3],
        'stock_level': row[4]
    }
    conn.close()
    return jsonify(item)

@app.route('/api/items', methods=['POST'])
def create_new_item():
    conn = create_connection()
    new_item = {
        'name': request.json['name'],
        'category': request.json['category'],
        'quantity': request.json['quantity'],
        'stock_level': request.json['stock_level']
    }
    item = (new_item['name'], new_item['category'], new_item['quantity'], new_item['stock_level'])
    create_item(conn, item)
    conn.close()
    return jsonify(new_item), 201

@app.route('/api/items/<id>', methods=['PUT'])
def update_existing_item(id):
    conn = create_connection()
    row = get_item(conn, int(id))
    if row is None:
        return jsonify({'error': 'Item not found'}), 404
    item = {
        'id': int(id),
        'name': request.json['name'],
        'category': request.json['category'],
        'quantity': request.json['quantity'],
        'stock_level': request.json['stock_level']
    }
    update_item(conn, item)
    conn.close()
    return jsonify(item)

@app.route('/api/items/<id>', methods=['DELETE'])
def delete_item_by_id(id):
    conn = create_connection()
    row = get_item(conn, int(id))
    if row is None:
        return jsonify({'error': 'Item not found'}), 404
    delete_item(conn, int(id))
    conn.close()
    return jsonify({'message': 'Item deleted'})

# 7. Error Handlers
@app.errorhandler(404)
def not_found(e):
    return jsonify({'error': 'Not found'}), 404

@app.errorhandler(500)
def internal_server_error(e):
    return jsonify({'error': 'Internal server error'}), 500

if __name__ == '__main__':
    conn = create_connection()
    create_table(conn)
    conn.close()
    app.run(host='0.0.0.0', port=int(os.getenv('PORT', '5017')))
