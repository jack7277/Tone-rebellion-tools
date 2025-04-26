import os
import struct

from PIL import Image


def pack_bmp_to_font(input_dir: str, output_file: str) -> None:
    # Получаем и сортируем BMP файлы
    bmp_files = sorted(
        [f for f in os.listdir(input_dir) if f.lower().endswith('.bmp')]
    )

    if not bmp_files:
        raise ValueError("No BMP files found in input directory")

    # Определяем высоту шрифта из первого непустого файла
    height = 0
    for bmp_file in bmp_files:
        if '_empty' in bmp_file.lower():
            continue
        try:
            with Image.open(os.path.join(input_dir, bmp_file)) as img:
                if img.size != (1, 1):
                    height = img.height
                    break
        except:
            continue

    if height == 0:
        raise ValueError("Could not determine font height")

    # Подготовка структур данных
    header = bytearray()  # заголовок шрифта
    pointer_table = bytearray()  # таблица 32х битных указателей
    glyph_data = bytearray()  # данные каждой буквы

    # Формируем заголовок (16 байт)
    header.extend(struct.pack('<I', 0x00002E31))  # Сигнатура
    header.extend(struct.pack('<I', len(bmp_files)))  # Количество глифов
    header.extend(struct.pack('<I', height))  # Высота шрифта
    header.extend(struct.pack('<I', 0x000000FF))  # Вторая сигнатура

    # Начальное смещение данных глифов
    data_start_offset = 16 + 4 * len(bmp_files)
    current_offset = data_start_offset  # начало таблицы смещений 0x0000 0398 (920)

    for bmp_file in bmp_files:
        file_path = os.path.join(input_dir, bmp_file)
        is_empty = '_empty' in bmp_file.lower()

        try:
            with Image.open(file_path) as img:
                # Получаем параметры изображения
                width = img.width
                if is_empty:
                    # Обработка пустых глифов
                    # Пустые BMP заменяются в шрифте на 0x00000000, 4 нуля
                    glyph = struct.pack('<I', 0)
                else:
                    # Формируем данные глифа
                    pixels = list(img.convert('L').getdata())
                    glyph = bytearray()
                    glyph.extend(struct.pack('<I', width))  # Ширина (32 бит число)
                    glyph.extend(bytes(0xFF if p < 128 else 0xF3 for p in pixels))  # Пиксели

                # Добавляем в таблицу указателей
                pointer_table.extend(struct.pack('<I', current_offset))

                # Добавляем данные глифа
                glyph_data.extend(glyph)
                # корректирую смещение до следующего блока символа
                current_offset += len(glyph)

        except Exception as e:
            print(str(e))
            raise ValueError(f"Error BMP processing, check image {bmp_file}")

    # Записываем файл шрифтов
    with open(output_file, 'wb') as f:
        f.write(header)  # 16 байт заголовка
        f.write(pointer_table)  # Таблица указателей
        f.write(glyph_data)  # Данные глифов

    print(f"\nSuccessfully packed {output_file}")
    print(f"Total glyphs: {len(bmp_files)}")
    print(f"Font height: {height}px")
    print(f"Data starts at: 0x{data_start_offset:04X}")
    print(f"First glyph pointer: 0x{struct.unpack('<I', pointer_table[:4])[0]:04X}")
    print(f"Total file size: {current_offset} bytes")


if __name__ == "__main__":
    pack_bmp_to_font(r'game\fonts\bigfont', 'bigfont.fnt')
    pack_bmp_to_font(r'game\fonts\bgoutfnt', 'bgoutfnt.fnt')
    pack_bmp_to_font(r'game\fonts\smfont', 'smfont.fnt')
