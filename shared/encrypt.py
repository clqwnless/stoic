# encrypt.py

import os

from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives import hashes


def load_public_key(path):
    # загружаем public key (возвращает str судя по всем ) из файла
    with open(path, "rb") as f:
        return serialization.load_pem_public_key(f.read())


def encrypt_file(raw_bytes, public_key_file):

    # берем aes key
    aes_key = AESGCM.generate_key(bit_length=256)

    # создаем саму машину шифрования

    aes = AESGCM(aes_key)

    # это просто идентификатор хуй его знает для чего он зато работает
    # просто один и тот же aes может использоваться для разных картинок
    # а nonce как бы задаёт по типу операции что то.

    nonce = os.urandom(12)

    encrypted_data = aes.encrypt(
        nonce,
        raw_bytes,
        None
    )
    
    # сохраняем данные (там первые 12 байт это nonce - остальное все уже encrypted_data)

    encrypted_file = nonce + encrypted_data;

    # теперь aes шифруем с помощью rsa (по сути это и будет ключ который мы потом расшифруем и с помощью которого (aes) уже сможем расшифровать картинку имея его и nonce)

    public_key = load_public_key(
        public_key_file
    )

    encrypted_aes_key = public_key.encrypt(
        aes_key,
        padding.OAEP(
            mgf=padding.MGF1(
                algorithm=hashes.SHA256()
            ),
            algorithm=hashes.SHA256(),
            label=None
        )
    )
    
    return encrypted_file, encrypted_aes_key;
    



