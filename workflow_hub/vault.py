"""Password-derived AES-256-GCM vault; SQLite is decrypted only in memory."""
import contextlib
import getpass
import os
import sqlite3
import threading
from pathlib import Path
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.scrypt import Scrypt
from cryptography.exceptions import InvalidTag

_LOCKS = {}
_LOCKS_GUARD = threading.Lock()


class Vault:
    def __init__(self, root, password=None):
        self.root = Path(root).resolve()
        self.root.mkdir(parents=True,exist_ok=True,mode=0o700)
        self.db = self.root/'database.vault'
        if (self.root/'hub.sqlite3').exists():
            raise ValueError('Legacy plaintext store detected. Use a new encrypted data directory; migration must be reviewed.')
        self.lock_path = self.root/'vault.lock'
        with _LOCKS_GUARD:
            self.lock = _LOCKS.setdefault(str(self.root),threading.RLock())
        password = password or os.environ.get('PALM92_VAULT_PASSWORD')
        if not password:
            password = getpass.getpass('Vault passphrase (12+ characters; no recovery if lost): ')
            if not self.db.exists() and password != getpass.getpass('Confirm new vault passphrase: '):
                raise ValueError('Passphrases do not match')
        if len(password) < 12:
            raise ValueError('Use a passphrase of at least 12 characters')
        with self.exclusive():
            salt_path = self.root/'salt'
            if not salt_path.exists():
                if self.db.exists():
                    raise ValueError('Vault salt missing. Restore the complete backup.')
                salt_path.write_bytes(os.urandom(16))
            salt = salt_path.read_bytes()
        key = Scrypt(salt=salt,length=32,n=2**15,r=8,p=1).derive(password.encode())
        self.cipher = AESGCM(key)
        if self.db.exists():
            self.open_bytes(self.db.read_bytes(),b'database')

    @contextlib.contextmanager
    def exclusive(self):
        with self.lock:
            with self.lock_path.open('a+b') as lockfile:
                if os.name == 'nt':
                    import msvcrt
                    lockfile.seek(0)
                    if not lockfile.read(1):
                        lockfile.write(b'0');lockfile.flush()
                    lockfile.seek(0);msvcrt.locking(lockfile.fileno(),msvcrt.LK_LOCK,1)
                else:
                    import fcntl
                    fcntl.flock(lockfile.fileno(),fcntl.LOCK_EX)
                try:
                    yield
                finally:
                    if os.name == 'nt':
                        lockfile.seek(0);msvcrt.locking(lockfile.fileno(),msvcrt.LK_UNLCK,1)
                    else:
                        fcntl.flock(lockfile.fileno(),fcntl.LOCK_UN)

    def seal(self, raw, purpose):
        nonce = os.urandom(12)
        return b'P92V1'+nonce+self.cipher.encrypt(nonce,raw,purpose)

    def open_bytes(self, raw, purpose):
        if not raw.startswith(b'P92V1'):
            raise ValueError('Unknown vault format')
        try:
            return self.cipher.decrypt(raw[5:17],raw[17:],purpose)
        except InvalidTag as exc:
            raise ValueError('Incorrect passphrase or damaged vault. Nothing was opened.') from exc

    @contextlib.contextmanager
    def connect(self):
        with self.exclusive():
            db = sqlite3.connect(':memory:')
            db.row_factory = sqlite3.Row
            db.execute('PRAGMA temp_store=MEMORY')
            try:
                if self.db.exists():
                    db.deserialize(self.open_bytes(self.db.read_bytes(),b'database'))
                yield db
                db.commit()
                encrypted = self.seal(db.serialize(),b'database')
                temp = self.root/'database.vault.new'
                with temp.open('wb') as f:
                    f.write(encrypted);f.flush();os.fsync(f.fileno())
                os.replace(temp,self.db)
            except Exception:
                db.rollback()
                raise
            finally:
                db.close()
