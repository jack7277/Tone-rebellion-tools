import os
import struct
import argparse


class CobFile:
    def __init__(self, dirname, filename):
        self.path = dirname
        self.name = filename
        self.size = 0
        self.offset = 0


class CobArchive:
    """Класс для работы с COB архивами (упаковка/распаковка)"""

    def __init__(self, filename=None):
        self.filename = filename
        self.files = []

        if filename and os.path.isfile(filename):
            self._handle = open(filename, 'rb')
            self._read_header()
        else:
            self._handle = None

    def _read_header(self):
        """Чтение заголовка COB архива"""
        self._handle.seek(0, os.SEEK_SET)
        # первые 4 байта - количество файлов
        count = struct.unpack('<i', self._handle.read(4))[0]
        if count < 1:
            return

        # Чтение путей файлов внутри cob файла, размер блока на путь+имя = 50 байт
        for _ in range(count):
            path_bytes = self._handle.read(50).partition(b'\0')[0]
            path = path_bytes.decode('cp1251')  # Используем однобайтовую кодировку
            dirname, filename = os.path.split(path.replace('\\', '/'))
            self.files.append(CobFile(dirname, filename))

        # Чтение смещений файлов, таблица указателей (32бит) на начало каждого файла
        self.files[0].offset = struct.unpack('<I', self._handle.read(4))[0]
        for i in range(1, count):
            self.files[i].offset = struct.unpack('<I', self._handle.read(4))[0]
            self.files[i - 1].size = self.files[i].offset - self.files[i - 1].offset

        # Определяем размер последнего файла
        self._handle.seek(0, os.SEEK_END)
        self.files[count - 1].size = self._handle.tell() - self.files[count - 1].offset
        self._handle.seek(0, os.SEEK_SET)

    def extract(self, output_dir=None):
        """Распаковка архива"""
        if not self.files:
            print("No files to extract!")
            return

        if output_dir is None:
            # Просто выводим список файлов
            for i, file in enumerate(self.files):
                print("{:3}:  {:10}  {}".format(i + 1, file.size, os.path.join(file.path, file.name)))
            return

        # Создаем директории и извлекаем файлы
        for i, file in enumerate(self.files):
            dest_path = os.path.join(output_dir, file.path, file.name)
            os.makedirs(os.path.dirname(dest_path), exist_ok=True)

            self._handle.seek(file.offset)
            with open(dest_path, 'wb') as fout:
                fout.write(self._handle.read(file.size))

            print("Extracted: {}".format(dest_path))

    def pack(self, input_dir, output_file):
        """Упаковка директории в COB архив"""
        self.filename = output_file
        self.file_entries = []

        # Рекурсивно собираем все файлы
        for root, _, files in os.walk(input_dir):
            for file in files:
                full_path = os.path.join(root, file)
                rel_path = os.path.relpath(full_path, input_dir)
                archive_path = rel_path.replace('/', '\\')

                self.files.append({
                    'path': archive_path,
                    'size': os.path.getsize(full_path),
                    'original_path': full_path
                })

        if not self.files:
            print("No files to pack!")
            return

        # Вычисляем смещение начала данных
        data_start = 4 + len(self.files) * (50 + 4)

        with open(output_file, 'wb') as fout:
            # Количество файлов
            fout.write(struct.pack('<I', len(self.files)))

            # Записываем пути файлов (максимум 50 байт)
            for entry in self.files:
                path_bytes = entry['path'].encode('cp1251')
                if len(path_bytes) > 49:
                    path_bytes = path_bytes[:49]

                path_bytes += b'\0' * (50 - len(path_bytes))
                fout.write(path_bytes)

            # Записываем смещения файлов
            current_offset = data_start
            for entry in self.files:
                fout.write(struct.pack('<I', current_offset))
                current_offset += entry['size']

            # Записываем данные файлов
            for entry in self.files:
                with open(entry['original_path'], 'rb') as fin:
                    fout.write(fin.read())

        print("Packed {} files into {}".format(len(self.files), output_file))

    def close(self):
        """Закрытие файлового дескриптора"""
        if self._handle:
            self._handle.close()


def main():
    parser = argparse.ArgumentParser(description='COB Archive Packer/Unpacker (Windows 95 compatible)')
    subparsers = parser.add_subparsers(dest='command', required=True)

    # Парсер для распаковки
    extract_parser = subparsers.add_parser('extract', help='Extract files from COB archive')
    extract_parser.add_argument('cob_file', help='COB archive file to extract')
    extract_parser.add_argument('-d', '--directory', help='Output directory (optional)')

    # Парсер для упаковки
    pack_parser = subparsers.add_parser('pack', help='Pack files into COB archive')
    pack_parser.add_argument('output_file', help='Output COB archive file')
    pack_parser.add_argument('input_dir', help='Input directory to pack')

    args = parser.parse_args()

    if args.command == 'extract':
        cob = CobArchive(args.cob_file)
        cob.extract(args.directory)
        cob.close()
    elif args.command == 'pack':
        cob = CobArchive()
        cob.pack(args.input_dir, args.output_file)


if __name__ == "__main__":
    main()