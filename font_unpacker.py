import os
import struct
from PIL import Image


def unpack_font_to_bmp(font_file, output_dir):
    """
    На вход подается путь к файлу шрифта
    На выходе в каталог складываются bmp изображения каждого символа
    """
    with open(font_file, 'rb') as f:
        data = f.read()

    # Парсим заголовок
    magic = data[:4]  # заголовок всегда одинаковый 4 байта - 0x312E0000
    num_glyphs = struct.unpack('<I', data[4:8])[0]  # количество букв шрифта
    height = struct.unpack('<I', data[8:12])[0]  # высота шрифта
    pointer_table_offset = 16  # смещение от начала файла до таблицы указателей на каждую букву шрифта

    print(f"Signature: {magic.hex()}")
    print(f"Total glyphs: {num_glyphs}")
    print(f"Glyph height: {height}")

    # Читаем таблицу указателей
    glyph_offsets = []
    for i in range(num_glyphs + 1):
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
        glyph_data = data[start + 4:end]

        # Проверяем корректность размера данных
        expected_size = glyph_width * height
        actual_size = len(glyph_data)

        if actual_size < expected_size:
            print(f"Warning: Glyph {glyph_num} incomplete. Expected {expected_size} bytes, got {actual_size}")
            glyph_data += b'\xFF' * (expected_size - actual_size)
        elif actual_size > expected_size:
            print(f"Warning: Glyph {glyph_num} extra data. Expected {expected_size} bytes, got {actual_size}")
            glyph_data = glyph_data[:expected_size]

        # Создаем изображение
        try:
            img = Image.new('1', (glyph_width, height))

            # Заполняем пиксели
            if glyph_width == 0:
                img = Image.new('1', (1, 1), color=1)  # 1 = белый
                filename = os.path.join(output_dir, f"glyph_{glyph_num:04d}_empty.bmp")
                img.save(filename)
                print(f"Saved empty {filename}")
                continue

            for y in range(height):
                for x in range(glyph_width):
                    pos = y * glyph_width + x
                    if pos < len(glyph_data):
                        pixel = 0 if glyph_data[pos] == 0xFF else 1
                        img.putpixel((x, y), pixel)

            # Сохраняем BMP
            filename = os.path.join(output_dir, f"glyph_{glyph_num:04d}_{glyph_width}x{height}.bmp")
            img.save(filename)
            print(f"Saved {filename}")

        except Exception as e:
            print(f"Error processing glyph {glyph_num}: {str(e)}")


if __name__ == "__main__":
    # unpack all 3 fonts
    unpack_font_to_bmp(r'game\fonts\bigfont.fnt', r'game\fonts\bigfont')  # big
    unpack_font_to_bmp(r'game\fonts\bgoutfnt.fnt', r'game\fonts\bgoutfnt')  # big bold
    unpack_font_to_bmp(r'game\fonts\smfont.fnt', r'game\fonts\smfont')  # small
