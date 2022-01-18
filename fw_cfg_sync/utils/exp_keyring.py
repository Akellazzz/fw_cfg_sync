import keyring

# keyring.set_password("test", "secret_username", "secret_password")

p = keyring.get_password("test", "secret_username")
print(p)
