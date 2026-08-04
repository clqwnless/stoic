# decrypt.py

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.ciphers.aead import AESGCM


def load_private_key(path):
    with open(path, "rb") as f:
        return serialization.load_pem_private_key(f.read(), password=None);

def decrypt_file(encrypted_bytes, encrypted_aes_key, private_key_file):

    private_key = load_private_key(private_key_file)

    # расшифровываем encrypted aes key

    aes_key = private_key.decrypt(
        encrypted_aes_key,
        padding.OAEP(
            mgf=padding.MGF1(
                algorithm=hashes.SHA256()
            ),
            algorithm=hashes.SHA256(),
            label=None
        )
    )

    # берём и читаем это всё дерьмо (первые 12 байт - nonce ; остальное всё - это уже данные сами)

    nonce           = encrypted_bytes[:12];
    encrypted_data  = encrypted_bytes[12:];

    # создаём машину aes

    aes = AESGCM(aes_key)

    # расшифровываем всё дерьмо

    data = aes.decrypt(
        nonce,
        encrypted_data,
        None
    )

    # возвращаем результат

    return data;


