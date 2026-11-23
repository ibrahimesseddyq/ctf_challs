# TO DO: Change the decrypted message so it starts nicely like a sentence! Maybe it should start with 'TARGET'? 

ENCRYPTED_MEMORY = [
    120,
    109,
    126,
    107,
    105,
    120,
    115,
    96,
    101,
    98,
    105,
    22,
    12,
    29,
    25,
    25,
    31,
]

KEY = 0x00


def decrypt_sector(data, key):
  decrypted_chars = []
  for byte in data:
    decrypted_chars.append(chr(byte ^ key))
  return "".join(decrypted_chars)


if __name__ == "__main__":
  print("Attempting memory sector recovery...")
  result = decrypt_sector(ENCRYPTED_MEMORY, KEY)
  print(f"Recovered data: {result}")
