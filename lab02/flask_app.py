import os
from flask import Flask, request, jsonify, send_file
import random

app = Flask(__name__)
products = {}
MAX_ID = 10 ** 4
UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


@app.route('/product', methods=['POST'])
def add_product():
    data = request.get_json()
    if not data or 'name' not in data or 'description' not in data:
        return jsonify({'error': 'Invalid input'}), 400

    if len(products) >= MAX_ID:
        return jsonify({'error': 'Product limit reached'}), 409

    product_id = random.randint(1, MAX_ID)
    while product_id in products:
        product_id = random.randint(1, MAX_ID)

    product = {'id': product_id, 'name': data['name'], 'description': data['description'], 'icon': None}
    products[product_id] = product
    return jsonify(product), 201


@app.route('/product/<int:product_id>', methods=['GET'])
def get_product(product_id):
    product = products.get(product_id)
    if not product:
        return jsonify({'error': 'Product not found'}), 404
    return jsonify(product)


@app.route('/product/<int:product_id>', methods=['PUT'])
def update_product(product_id):
    data = request.get_json()
    product = products.get(product_id)
    if not product:
        return jsonify({'error': 'Product not found'}), 404

    if 'name' in data:
        product['name'] = data['name']
    if 'description' in data:
        product['description'] = data['description']

    return jsonify(product)


@app.route('/product/<int:product_id>', methods=['DELETE'])
def delete_product(product_id):
    product = products.pop(product_id, None)
    if not product:
        return jsonify({'error': 'Product not found'}), 404

    if product['icon']:
        os.remove(os.path.join(UPLOAD_FOLDER, product['icon']))

    return jsonify(product)


@app.route('/products', methods=['GET'])
def get_products():
    return jsonify(list(products.values()))


@app.route('/product/<int:product_id>/image', methods=['POST'])
def upload_image(product_id):
    if product_id not in products:
        return jsonify({'error': 'Product not found'}), 404

    if 'icon' not in request.files:
        return jsonify({'error': 'No file provided'}), 400

    file = request.files['icon']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400

    filename = f"product_{product_id}_icon.png"
    filepath = os.path.join(UPLOAD_FOLDER, filename)
    file.save(filepath)

    products[product_id]['icon'] = filename
    return jsonify({'message': 'Image uploaded', 'icon': filename}), 201


@app.route('/product/<int:product_id>/image', methods=['GET'])
def get_image(product_id):
    product = products.get(product_id)
    if not product or not product['icon']:
        return jsonify({'error': 'Image not found'}), 404

    return send_file(os.path.join(UPLOAD_FOLDER, product['icon']))


if __name__ == '__main__':
    app.run(debug=True)
