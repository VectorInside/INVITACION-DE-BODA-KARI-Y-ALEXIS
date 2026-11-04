"""Servidor de revisión: RSVP, álbum moderado y panel privado. Python 3 + Pillow."""
import argparse
import base64
import hashlib
import hmac
import io
import json
import os
import secrets
import sqlite3
import time
from http.cookies import SimpleCookie
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlsplit

from PIL import Image, ImageOps, UnidentifiedImageError

ROOT = Path(__file__).resolve().parent
Image.MAX_IMAGE_PIXELS = 30_000_000


def password_hash(password, salt):
    return hashlib.pbkdf2_hmac('sha256', password.encode(), bytes.fromhex(salt), 300_000).hex()


class WeddingServer(ThreadingHTTPServer):
    daemon_threads = True

    def __init__(self, address, data_dir):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True, mode=0o700)
        (self.data_dir / 'photos').mkdir(exist_ok=True, mode=0o700)
        config_file = self.data_dir / 'auth.json'
        if not config_file.exists():
            password = secrets.token_urlsafe(18)
            salt = secrets.token_hex(24)
            config_file.write_text(json.dumps({'salt': salt, 'hash': password_hash(password, salt)}))
            os.chmod(config_file, 0o600)
            access = self.data_dir / 'ACCESO-PRIVADO.txt'
            access.write_text('Panel: http://127.0.0.1:%s/admin\nContraseña: %s\n\nAcceso local de revisión. No compartir este archivo ni incluirlo en el sitio publicado.\n' % (address[1], password))
            os.chmod(access, 0o600)
        self.auth = json.loads(config_file.read_text())
        self.sessions = {}
        self.failures = {}
        self.submissions = {}
        with self.db() as db:
            db.executescript('''
            CREATE TABLE IF NOT EXISTS rsvps (
              id TEXT PRIMARY KEY, edit_hash TEXT NOT NULL, name TEXT NOT NULL,
              attendance TEXT NOT NULL, companions INTEGER NOT NULL,
              updated INTEGER NOT NULL);
            CREATE TABLE IF NOT EXISTS photos (
              id TEXT PRIMARY KEY, name TEXT NOT NULL, caption TEXT NOT NULL,
              status TEXT NOT NULL DEFAULT 'pending', created INTEGER NOT NULL);
            ''')
        super().__init__(address, Handler)

    def db(self):
        db = sqlite3.connect(self.data_dir / 'wedding.sqlite3', timeout=10)
        db.row_factory = sqlite3.Row
        return db


class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(ROOT / 'dist'), **kwargs)

    def log_message(self, fmt, *args):
        # Sin nombres, contraseñas, tokens ni contenido enviado en registros.
        pass

    def end_headers(self):
        if getattr(self, 'clear_admin_cookie', False):
            self.send_header('Set-Cookie', 'ka_admin=; HttpOnly; SameSite=Strict; Path=/; Max-Age=0')
        self.send_header('X-Content-Type-Options', 'nosniff')
        self.send_header('Referrer-Policy', 'strict-origin-when-cross-origin')
        self.send_header('X-Frame-Options', 'SAMEORIGIN')
        if self.path.startswith(('/api/', '/admin', '/media/')):
            self.send_header('Cache-Control', 'no-store')
        super().end_headers()

    def send_json(self, status, value):
        raw = json.dumps(value, ensure_ascii=False).encode()
        self.send_response(status)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Content-Length', str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)

    def session(self):
        try:
            cookie = SimpleCookie(self.headers.get('Cookie', ''))
            token = cookie['ka_admin'].value
            session = self.server.sessions.get(token)
            if session and session['expires'] > time.time():
                return session
        except (KeyError, ValueError):
            pass
        return None

    def do_GET(self):
        path = urlsplit(self.path).path
        if path == '/api/photos':
            with self.server.db() as db:
                rows = db.execute("SELECT id,name,caption FROM photos WHERE status='approved' ORDER BY created DESC LIMIT 150").fetchall()
            return self.send_json(200, {'photos': [dict(r) for r in rows]})
        if path == '/api/admin/session':
            session = self.session()
            return self.send_json(200, {'authenticated': bool(session), 'csrf': session['csrf'] if session else None})
        if path == '/api/admin/dashboard':
            if not self.session():
                return self.send_json(401, {'error': 'Inicia sesión para ver el panel.'})
            with self.server.db() as db:
                guests = [dict(r) for r in db.execute('SELECT id,name,attendance,companions,updated FROM rsvps ORDER BY updated DESC')]
                photos = [dict(r) for r in db.execute('SELECT * FROM photos ORDER BY created DESC')]
            attending = [g for g in guests if g['attendance'] == 'yes']
            companions = sum(g['companions'] for g in attending)
            return self.send_json(200, {'guests': guests, 'photos': photos, 'totals': {
                'confirmed': len(attending), 'companions': companions,
                'people': len(attending) + companions,
                'declined': len(guests) - len(attending),
                'pending': sum(p['status'] == 'pending' for p in photos)}})
        if path.startswith('/api/'):
            return self.send_json(404, {'error': 'No encontrado.'})
        if path.startswith('/media/'):
            photo_id = path.removeprefix('/media/').removesuffix('.jpg')
            if len(photo_id) != 32 or any(c not in '0123456789abcdef' for c in photo_id):
                return self.send_error(404)
            with self.server.db() as db:
                photo = db.execute('SELECT status FROM photos WHERE id=?', (photo_id,)).fetchone()
            if not photo or (photo['status'] != 'approved' and not self.session()):
                return self.send_error(404)
            raw = (self.server.data_dir / 'photos' / (photo_id + '.jpg')).read_bytes()
            self.send_response(200)
            self.send_header('Content-Type', 'image/jpeg')
            self.send_header('Content-Length', str(len(raw)))
            self.end_headers()
            self.wfile.write(raw)
            return
        if path in ('/admin', '/admin/', '/admin.html'):
            # Cada nueva entrada al panel exige de nuevo la contraseña.
            session = self.session()
            if session:
                session['expires'] = 0
            self.clear_admin_cookie = True
            self.path = '/admin.html'
        # Nunca ofrecer listados de carpetas.
        return super().do_GET()

    def list_directory(self, path):
        self.send_error(404)
        return None

    def do_POST(self):
        path = urlsplit(self.path).path
        # Solicitudes mutables desde el mismo origen; sin CORS público.
        origin = self.headers.get('Origin', '')
        if not origin or urlsplit(origin).netloc != self.headers.get('Host'):
            return self.send_json(403, {'error': 'Solicitud no permitida.'})
        if self.headers.get('Content-Type', '').split(';')[0] != 'application/json':
            return self.send_json(415, {'error': 'Formato no permitido.'})
        try:
            length = int(self.headers.get('Content-Length', 0))
            if length < 2 or length > 12_000_000:
                return self.send_json(413, {'error': 'El archivo es demasiado grande.'})
            data = json.loads(self.rfile.read(length))
            if not isinstance(data, dict):
                raise ValueError()
            return self.handle_post(path, data)
        except (ValueError, TypeError, KeyError, UnidentifiedImageError, Image.DecompressionBombError, Image.DecompressionBombWarning):
            return self.send_json(400, {'error': 'Revisa los datos. Usa una imagen JPG, PNG o WebP válida.'})

    def handle_post(self, path, data):
        if path == '/api/admin/login':
            ip = self.client_address[0]
            now = time.time()
            attempts = [t for t in self.server.failures.get(ip, []) if now-t < 900]
            self.server.failures[ip] = attempts
            if len(attempts) >= 6:
                return self.send_json(429, {'error': 'Demasiados intentos. Espera 15 minutos.'})
            password = data.get('password', '')
            if not isinstance(password, str) or len(password) > 200 or not hmac.compare_digest(password_hash(password, self.server.auth['salt']), self.server.auth['hash']):
                attempts.append(now)
                return self.send_json(401, {'error': 'La contraseña no es correcta.'})
            token = secrets.token_urlsafe(32)
            session = {'expires': now + 8*3600, 'csrf': secrets.token_urlsafe(32)}
            self.server.sessions[token] = session
            self.server.failures.pop(ip, None)
            self.send_response(200)
            self.send_header('Set-Cookie', 'ka_admin=%s; HttpOnly; SameSite=Strict; Path=/; Max-Age=28800%s' % (token, '; Secure' if origin_https(self) else ''))
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            return self.wfile.write(json.dumps({'csrf': session['csrf']}).encode())
        if path.startswith('/api/admin/'):
            session = self.session()
            if not session:
                return self.send_json(401, {'error': 'Vuelve a iniciar sesión.'})
            if not hmac.compare_digest(self.headers.get('X-CSRF-Token', ''), session['csrf']):
                return self.send_json(403, {'error': 'Actualiza el panel e intenta de nuevo.'})
            if path == '/api/admin/logout':
                session['expires'] = 0
                return self.send_json(200, {'ok': True})
            if path == '/api/admin/moderate':
                if data.get('status') not in ('approved', 'hidden'):
                    raise ValueError()
                with self.server.db() as db:
                    cursor = db.execute('UPDATE photos SET status=? WHERE id=?', (data['status'], str(data.get('id', ''))))
                return self.send_json(200 if cursor.rowcount else 404, {'ok': bool(cursor.rowcount)})
        if path == '/api/rsvp':
            name = clean(data.get('name'), 80)
            attendance = data.get('attendance')
            companions = data.get('companions')
            if attendance not in ('yes', 'no') or type(companions) is not int or not 0 <= companions <= 20:
                raise ValueError()
            if attendance == 'no':
                companions = 0
            token = data.get('editToken')
            if not isinstance(token, str) or not 32 <= len(token) <= 128:
                raise ValueError()
            digest = hashlib.sha256(token.encode()).hexdigest()
            with self.server.db() as db:
                row = db.execute('SELECT id FROM rsvps WHERE edit_hash=?', (digest,)).fetchone()
                ref = row['id'] if row else 'KA-' + secrets.token_hex(6).upper()
                db.execute('INSERT INTO rsvps VALUES (?,?,?,?,?,?) ON CONFLICT(id) DO UPDATE SET name=excluded.name,attendance=excluded.attendance,companions=excluded.companions,updated=excluded.updated', (ref, digest, name, attendance, companions, int(time.time())))
            return self.send_json(200, {'reference': ref, 'companions': companions})
        if path == '/api/photos':
            name = clean(data.get('name'), 80)
            caption = clean(data.get('caption'), 240)
            if data.get('consent') is not True:
                raise ValueError()
            ip = self.client_address[0]
            now = time.time()
            recent = [t for t in self.server.submissions.get(ip, []) if now-t < 3600]
            if len(recent) >= 20:
                return self.send_json(429, {'error': 'Ya recibimos varias fotos. Intenta más tarde.'})
            encoded = data.get('image')
            if not isinstance(encoded, str) or len(encoded) > 11_000_000:
                raise ValueError()
            raw = base64.b64decode(encoded, validate=True)
            if len(raw) > 8_000_000:
                raise ValueError()
            with Image.open(io.BytesIO(raw)) as original:
                if original.format not in ('JPEG', 'PNG', 'WEBP'):
                    raise ValueError()
                image = ImageOps.exif_transpose(original).convert('RGB')
                image.thumbnail((1800, 1800))
                photo_id = secrets.token_hex(16)
                image.save(self.server.data_dir / 'photos' / (photo_id+'.jpg'), 'JPEG', quality=85, optimize=True)
            with self.server.db() as db:
                db.execute('INSERT INTO photos VALUES (?,?,?,?,?)', (photo_id, name, caption, 'pending', int(now)))
            recent.append(now)
            self.server.submissions[ip] = recent
            return self.send_json(201, {'ok': True})
        return self.send_json(404, {'error': 'No encontrado.'})


def clean(value, limit):
    if not isinstance(value, str) or not value.strip() or len(value.strip()) > limit:
        raise ValueError()
    return value.strip()


def origin_https(handler):
    return urlsplit(handler.headers.get('Origin', '')).scheme == 'https'


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--port', type=int, default=8741)
    parser.add_argument('--data-dir', type=Path, default=ROOT / '.private')
    args = parser.parse_args()
    server = WeddingServer(('127.0.0.1', args.port), args.data_dir)
    print('Invitación: http://127.0.0.1:%s/ | Panel: /admin' % args.port, flush=True)
    print('Acceso privado guardado fuera del sitio, en .private/ACCESO-PRIVADO.txt', flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        server.server_close()
