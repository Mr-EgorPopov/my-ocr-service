# app.py
from flask import Flask, request, jsonify
from paddleocr import PaddleOCR
from PIL import Image
import io
import re

app = Flask(__name__)

# Загружаем OCR один раз при старте
ocr = PaddleOCR(
    use_angle_cls=False,
    lang='ru',          # Поддержка русского
    use_gpu=False,      # CPU only
    show_log=False
)

@app.route('/ocr', methods=['POST'])
def recognize():
    if 'image' not in request.files:
        return jsonify({"error": "No image provided"}), 400

    file = request.files['image']
    try:
        image = Image.open(file.stream).convert('RGB')
        result = ocr.ocr(image, cls=False)
    except Exception as e:
        return jsonify({"error": f"OCR failed: {str(e)}"}), 500

    if not result or not result[0]:
        return jsonify({"value": 0})

    # Извлекаем весь текст
    text = " ".join([line[1][0] for line in result[0]]).lower()
    text = text.replace('мпн', 'млн').replace('мл', 'млн').replace('тш', 'тыс')

    total = 0

    # Парсинг млн
    if 'млн' in text:
        parts = text.split('млн')[0].strip().split()
        num_str = parts[-1] if parts else ''
        if num_str.isdigit():
            total += int(num_str) * 1_000_000

    # Парсинг тыс
    if 'тыс' in text:
        parts = text.split('тыс')[0].strip().split()
        num_str = parts[-1] if parts else ''
        if num_str.isdigit():
            total += int(num_str) * 1_000

    # Парсинг адены
    all_digits = re.findall(r'\d+', text)
    for d in all_digits:
        val = int(d)
        if val < 1000 and total == 0:
            total += val
        elif 1000 <= val < 1_000_000 and 'тыс' not in text and 'млн' not in text:
            total += val

    return jsonify({"value": total})

@app.route('/health')
def health():
    return jsonify({"status": "ok"})