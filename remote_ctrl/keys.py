from cryptography.fernet import Fernet


def GetKeySeeg():

    key = b"YD5BmaOtvjQ7D-4spu_ChJkmHm59eFuqHyDJ1E63u_g="
    keyEncript = b"gAAAAABnZF0fmGkACky16ks9muCaVgYIijqahL0NoOZJEAet3onypa1h-6kEmmyx4j5Wr3d4GYgyw3xt2YfX612xXspFoePNKKf9iN6A7Nl_9zDsiAIKNKg="
    fernet = Fernet(key)
    keyDecript = fernet.decrypt(keyEncript).decode()
    return keyDecript


def GetKeyRoot():

    key = b"3qpXeogyKKjen6FxSvZKJ0am4PgEX39-o3r1FO-E2B4="
    keyEncript = b"gAAAAABn6qbKsH--ke4dtX193hEDPGT88taMNXA2r-0gUV1J5KOJ4CvaEsGhDSFwewRLbeabWwn1Y5W1FmHJBrtFRlL0GWRwm2Vb3BT6dp22HCk3z5lt3gA="
    fernet = Fernet(key)
    keyDecript = fernet.decrypt(keyEncript).decode()
    return keyDecript


def GenerateKeyAndToken(strPassword):
    # example b'Password'
    key = Fernet.generate_key()
    print("Key: {}".format(key))
    f = Fernet(key)
    token = f.encrypt(strPassword)
    print("Token: {}".format(token))
    print()



