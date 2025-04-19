import os
import struct
from PIL import Image


def unpack_font_to_bmp(font_file, output_dir):
    with open(font_file, 'rb') as f:
        data = f.read()

    # Парсим заголовок
    magic = data[:4]  # Первые 4 байта - сигнатура
    num_glyphs = struct.unpack('<I', data[4:8])[0]  # Количество глифов (4-7 байты)
    height = struct.unpack('<I', data[8:12])[0]  # Высота глифа (8-11 байты)
    pointer_table_offset = 16  # Таблица указателей начинается с 16 байта

    print(f"Signature: {magic.hex()}")
    print(f"Total glyphs: {num_glyphs}")
    print(f"Glyph height: {height}")

    # Читаем таблицу указателей (каждый по 4 байта)
    glyph_offsets = []
    for i in range(num_glyphs + 1):  # +1 для определения размера последнего глифа
        offset = struct.unpack('<I', data[pointer_table_offset + i * 4:pointer_table_offset + (i + 1) * 4])[0]
        glyph_offsets.append(offset)

    # Создаем выходную директорию
    os.makedirs(output_dir, exist_ok=True)

    # Обрабатываем каждый глиф
    for glyph_num in range(num_glyphs):
        start = glyph_offsets[glyph_num]
        end = glyph_offsets[glyph_num + 1]

        # Читаем заголовок глифа (первые 4 байта - ширина)
        glyph_width = struct.unpack('<I', data[start:start + 4])[0]
        glyph_data = data[start + 4:end]  # Пиксельные данные

        # Проверяем корректность размера данных
        expected_size = glyph_width * height
        actual_size = len(glyph_data)

        if actual_size < expected_size:
            print(f"Warning: Glyph {glyph_num} incomplete. Expected {expected_size} bytes, got {actual_size}")
            # Дополняем нулями при необходимости
            glyph_data += b'\xFF' * (expected_size - actual_size)
        elif actual_size > expected_size:
            print(f"Warning: Glyph {glyph_num} extra data. Expected {expected_size} bytes, got {actual_size}")
            glyph_data = glyph_data[:expected_size]

        # Создаем изображение
        try:
            img = Image.new('1', (glyph_width, height))

            # Заполняем пиксели
            for y in range(height):
                for x in range(glyph_width):
                    pos = y * glyph_width + x
                    if pos < len(glyph_data):
                        # 0xFF - белый, другие значения - черный
                        pixel = 0 if glyph_data[pos] == 0xFF else 1
                        img.putpixel((x, y), pixel)

            # Сохраняем BMP
            filename = os.path.join(output_dir, f"glyph_{glyph_num:04d}_{glyph_width}x{height}.bmp")
            img.save(filename)
            print(f"Saved {filename}")

        except Exception as e:
            print(f"Error processing glyph {glyph_num}: {str(e)}")


unpack_font_to_bmp(r'game\fonts\bigfont.fnt', r'game\fonts\bigfontfnt\out')
unpack_font_to_bmp(r'game\fonts\bigfont.fnt', r'game\fonts\bigfontfnt\out')
unpack_font_to_bmp(r'game\fonts\bigfont.fnt', r'game\fonts\bigfontfnt\out')
