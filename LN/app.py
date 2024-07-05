from flask import Flask, request, send_file, render_template, url_for
import pandas as pd
from PIL import Image, ImageDraw, ImageFont
import os

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    file = request.files['file']
    if file:
        df = pd.read_csv(file)
        output_image_paths = generate_id_cards(df)
        
        # Combine all images into one
        combined_all_image = combine_all_id_cards(output_image_paths, allpadding=50)  # Set padding to 50
        combined_all_image_path = os.path.join('static', 'hasil', 'combined_all.png')
        combined_all_image.save(combined_all_image_path, dpi=(300, 300))  # Set DPI to 300
        combined_all_image_url = url_for('static', filename='hasil/combined_all.png')
        
        return render_template('result.html', file_urls=output_image_paths, combined_all_url=combined_all_image_url)

def generate_id_cards(df):
    output_image_paths = []

    for index, row in df.iterrows():
        id_cards = []
        bg_path = os.path.join('static/backgrounds', row["background"])
        font_path = os.path.join('static/fonts', row["font"])

        if not os.path.exists(bg_path):
            raise FileNotFoundError(f"Background file not found: {bg_path}")
        if not os.path.exists(font_path):
            raise FileNotFoundError(f"Font file not found: {font_path}")

        bg = Image.open(bg_path).convert("RGBA")
        draw = ImageDraw.Draw(bg)

        # Calculate text size and position
        name = row['nama']
        max_width = bg.width - 159  # Adjust as needed
        max_height = bg.height - 100  # Adjust as needed
        max_font_size = 100  # Maximum font size
        min_font_size = 20   # Minimum font size

        # Find the appropriate font size
        font_size = max_font_size
        font = ImageFont.truetype(font_path, font_size)
        while font_size > min_font_size:
            lines = []
            words = name.split()
            while words:
                line = ''
                while words and draw.textbbox((0, 0), line + words[0], font=font)[2] <= max_width:
                    line += (words.pop(0) + ' ')
                lines.append(line.strip())

            text_height = sum([draw.textbbox((0, 0), line, font=font)[3] for line in lines])
            if text_height <= max_height:
                break
            font_size -= 1
            font = ImageFont.truetype(font_path, font_size)

        # Calculate total height of text block
        y_text = (bg.height - text_height) // 2

        # Tentukan warna font berdasarkan nama background
        font_color = "white" if "HITAM" in row["background"].upper() else "black"

        for line in lines:
            text_width, text_height = draw.textbbox((0, 0), line, font=font)[2:4]
            x_text = (bg.width - text_width) // 2
            draw.text((x_text, y_text), line, font=font, fill=font_color)  # Gunakan font_color
            y_text += text_height

        # Get the number of sets (pcs) from the CSV
        num_sets = int(row['jumlah'])
        print(f"Generating {num_sets * 45} ID cards for {name}")  # Debugging statement

        # Duplicate the ID card accordingly
        for _ in range(num_sets * 45):  # 45 ID cards per set
            id_cards.append(bg.copy())

        print(f"Total ID cards for {name}: {len(id_cards)}")  # Debugging statement

        # Combine ID cards into one image
        combined_image = combine_id_cards(id_cards, row_padding=30)  # Set row padding to 30
        
        # Save combined image to a temporary file
        output_image_path = os.path.join('static', 'hasil', f'labelnama_{index}.png')
        combined_image.save(output_image_path, dpi=(300, 300))  # Set DPI to 300
        output_image_paths.append(output_image_path)

    return output_image_paths

def combine_id_cards(id_cards, row_padding=30, col_padding=30):
    num_columns = 9  # Jumlah kolom
    num_rows = (len(id_cards) + num_columns - 1) // num_columns  # Hitung jumlah baris yang diperlukan

    card_width, card_height = id_cards[0].size
    combined_width = num_columns * card_width + (num_columns - 1) * col_padding
    combined_height = num_rows * card_height + (num_rows - 1) * row_padding

    combined_image = Image.new('RGBA', (combined_width, combined_height), (255, 255, 255, 0))  # Transparent background

    for index, id_card in enumerate(id_cards):
        row = index // num_columns
        col = index % num_columns
        x_offset = col * (card_width + col_padding)
        y_offset = row * (card_height + row_padding)
        combined_image.paste(id_card, (x_offset, y_offset), id_card)

    return combined_image

def combine_all_id_cards(image_paths, allpadding=50):
    images = [Image.open(image_path) for image_path in image_paths]
    num_rows = len(images)  # Jumlah baris sesuai dengan jumlah gambar

    card_width, card_height = images[0].size
    combined_width = card_width  # Lebar gambar gabungan sama dengan lebar satu ID card
    combined_height = sum(image.size[1] for image in images) + (num_rows - 1) * allpadding

    combined_image = Image.new('RGBA', (combined_width, combined_height), (255, 255, 255, 0))  # Transparent background

    y_offset = 0
    for image in images:
        combined_image.paste(image, (0, y_offset))
        y_offset += image.size[1] + allpadding

    return combined_image

if __name__ == '__main__':
    app.run(debug=True)