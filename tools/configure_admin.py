"""Configura la contraseña sin incluir datos reales en el repositorio."""
import argparse
import getpass
import hashlib
import json
import os
import secrets
from pathlib import Path


def configure(data_dir, password, port=8741):
    if not password or len(password) > 200:
        raise ValueError('La contraseña debe tener entre 1 y 200 caracteres.')
    data_dir.mkdir(parents=True, exist_ok=True, mode=0o700)
    salt = secrets.token_hex(24)
    digest = hashlib.pbkdf2_hmac('sha256', password.encode(), bytes.fromhex(salt), 300_000).hex()
    path = data_dir / 'auth.json'
    path.write_text(json.dumps({'salt': salt, 'hash': digest}), encoding='utf-8')
    os.chmod(path, 0o600)
    path = data_dir / 'ACCESO-PRIVADO.txt'
    path.write_text(f'Panel: http://127.0.0.1:{port}/admin\nContraseña: {password}\n\nNo incluir este archivo en la carpeta pública ni en Git.\n', encoding='utf-8')
    os.chmod(path, 0o600)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--data-dir', type=Path, default=Path(__file__).resolve().parents[1] / '.private')
    parser.add_argument('--port', type=int, default=8741)
    args = parser.parse_args()
    password = getpass.getpass('Contraseña del panel (consulta la acordada en README.md): ')
    confirmation = getpass.getpass('Repite la contraseña: ')
    if password != confirmation:
        parser.error('Las contraseñas no coinciden.')
    configure(args.data_dir, password, args.port)
    print('Acceso configurado. Inicia o reinicia server.py para aplicarlo. Los invitados y las fotos se conservan.')
