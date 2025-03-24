from typing import Optional, Union
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.asymmetric import padding, rsa
from cryptography.hazmat.backends import default_backend
from cryptography.fernet import Fernet
import base64


class Encryption:
    def __init__(
        self,
        public_key_path: Optional[str] = "./keys/public_key.pem",
        private_key_path: Optional[str] = "./keys/private_key.pem",
        symmetric_key: Optional[bytes] = None,
    ):
        self._public_key = None
        self._private_key = None
        self._symmetric_key = symmetric_key
        self._fernet = None

        if public_key_path:
            self.load_public_key(public_key_path)
        if private_key_path:
            self.load_private_key(private_key_path)
        if symmetric_key:
            self._fernet = Fernet(symmetric_key)

    def load_public_key(self, key_path: str) -> None:
        """Load RSA public key from file"""
        try:
            with open(key_path, "rb") as key_file:
                self._public_key = serialization.load_pem_public_key(
                    key_file.read(), backend=default_backend()
                )
        except Exception as e:
            raise ValueError(f"Failed to load public key: {e}")

    def load_private_key(self, key_path: str, password: Optional[bytes] = None) -> None:
        """Load RSA private key from file"""
        try:
            with open(key_path, "rb") as key_file:
                self._private_key = serialization.load_pem_private_key(
                    key_file.read(), password=password, backend=default_backend()
                )
        except Exception as e:
            raise ValueError(f"Failed to load private key: {e}")

    @staticmethod
    def generate_key_pair(
        key_size: int = 2048,
        public_path: str = "public_key.pem",
        private_path: str = "private_key.pem",
    ) -> tuple[str, str]:
        """Generate new RSA key pair and save to files"""
        private_key = rsa.generate_private_key(
            public_exponent=65537, key_size=key_size, backend=default_backend()
        )
        public_key = private_key.public_key()

        # Save private key
        with open(private_path, "wb") as f:
            f.write(
                private_key.private_bytes(
                    encoding=serialization.Encoding.PEM,
                    format=serialization.PrivateFormat.PKCS8,
                    encryption_algorithm=serialization.NoEncryption(),
                )
            )

        # Save public key
        with open(public_path, "wb") as f:
            f.write(
                public_key.public_bytes(
                    encoding=serialization.Encoding.PEM,
                    format=serialization.PublicFormat.SubjectPublicKeyInfo,
                )
            )

        return public_path, private_path

    @staticmethod
    def generate_symmetric_key() -> bytes:
        """Generate new symmetric key for Fernet encryption"""
        return Fernet.generate_key()

    def encrypt_asymmetric(self, data: Union[str, bytes]) -> str:
        """Encrypt data using RSA public key"""
        if not self._public_key:
            raise ValueError("Public key not loaded")

        if isinstance(data, str):
            data = data.encode()

        encrypted = self._public_key.encrypt(
            data,
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None,
            ),
        )
        return encrypted.hex()

    def decrypt_asymmetric(self, encrypted_data: str) -> str:
        """Decrypt data using RSA private key"""
        if not self._private_key:
            raise ValueError("Private key not loaded")

        try:
            decrypted = self._private_key.decrypt(
                bytes.fromhex(encrypted_data),
                padding.OAEP(
                    mgf=padding.MGF1(algorithm=hashes.SHA256()),
                    algorithm=hashes.SHA256(),
                    label=None,
                ),
            )
            return decrypted.decode()
        except Exception as e:
            raise ValueError(f"Decryption failed: {e}")

    def encrypt_symmetric(self, data: Union[str, bytes]) -> str:
        """Encrypt data using symmetric key (Fernet)"""
        if not self._fernet:
            raise ValueError("Symmetric key not set")

        if isinstance(data, str):
            data = data.encode()

        encrypted = self._fernet.encrypt(data)
        return base64.b64encode(encrypted).decode()

    def decrypt_symmetric(self, encrypted_data: str) -> str:
        """Decrypt data using symmetric key (Fernet)"""
        if not self._fernet:
            raise ValueError("Symmetric key not set")

        try:
            decoded = base64.b64decode(encrypted_data)
            decrypted = self._fernet.decrypt(decoded)
            return decrypted.decode()
        except Exception as e:
            raise ValueError(f"Symmetric decryption failed: {e}")
