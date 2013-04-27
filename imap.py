import sys
import time
import socket
import imaplib
import email
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
import gpgme
from cStringIO import StringIO
from email.generator import Generator
try:
    from io import BytesIO
except ImportError:
    from StringIO import StringIO as BytesIO

class IMAPConnection:
	def __init__(self,address,port,ssl,username,password):
		self.address = address
		self.port = port
		self.ssl = ssl
		self.username = username

		# connect to mail server
		try:
			if ssl == True:
				self.imap = imaplib.IMAP4_SSL(address,port)
			else:
				self.imap = imaplib.IMAP4(address,port)
		except imaplib.IMAP4.error,socket.error:
			print >> sys.stderr, "Couldn't connect to IMAP Server"
			sys.exit(1)

		# authenticate
		try:
			self.imap.login(username,password)
		except imaplib.IMAP4.error:
			print >> sys.stderr, "Couldn't authenticate on IMAP Server"
			sys.exit(1)

	def __iter__(self):
		return IMAPMailboxIterator(self)

	def __str__(self):
		return "IMAP Server: " + self.address + "\nIMAP Port: " + str(self.port) + "\nIMAP SSL: " + str(self.ssl) + "\nIMAP Username: " + self.username

	def __del__(self):
		self.imap.close()
		self.imap.logout()

class IMAPMailboxIterator:
	def __init__(self,conn):
		self.conn = conn
		self.imap = conn.imap
		typ,self.mailboxlist = self.imap.list()
		self.curnum = -1

	def __iter__(self):
		return self

	def next(self):
		self.curnum += 1
		try: 
			return IMAPMailbox(self.conn,self.mailboxlist[self.curnum].split()[2])
		except IndexError:
			raise StopIteration

class IMAPMailbox:
	def __init__(self,conn,mailbox):
		self.conn = conn
		self.imap = conn.imap
		self.mailbox = mailbox

	def __iter__(self):
		return IMAPMailIterator(self.conn,self.mailbox)

	def __str__(self):
		return str(self.conn) + "\nIMAP Mailbox: " + self.mailbox

class IMAPMailIterator:
	def __init__(self,conn,mailbox):
		self.conn = conn
		self.imap = conn.imap
		self.mailbox = mailbox
		self.mailboxentries = self.imap.select(self.mailbox)
		typ, data = self.imap.uid('search', None, 'ALL')
		self.numbers = data[0].split()
		self.curnum = -1

	def __iter__(self):
		return self

	def next(self):
		self.curnum += 1
		try:
			typ, data = self.imap.uid('fetch',self.numbers[self.curnum],'(RFC822)')
			if "(\\Seen)" in data[0][0]:
				self.seen = False
			else:
				self.seen = True
		except IndexError:
			raise StopIteration
		return IMAPMail(self.conn,self.mailbox,self.seen,self.numbers[self.curnum],data[0][1])


class IMAPMail:
	def __init__(self,conn,mailbox,seen,uid,mail):
		self.imap = conn.imap
		self.mailbox = mailbox
		self.seen = seen
		self.uid = uid
		self.mail = email.message_from_string(mail)
		self.subject = self.mail['Subject'] or ""
		self.sender = self.mail['From'] or ""
		self.receiver = self.mail['To'] or ""
		self.date = self.mail['Date'] or ""

	def isEncrypted(self):
		if self.mail.get_content_type() == "multipart/encrypted":
			return True
		else:
			return False

	def encryptPGP(self,key):
		# encrypt payload of old email
		plaintext = BytesIO(str(self.mail.get_payload()))
		ciphertext = BytesIO()
		ctx = gpgme.Context()
		ctx.armor = True
		try:
			recipient = ctx.get_key(key)
		except:
			print >> sys.stderr, "Couldn't find GPG Key"
			sys.exit(1)
		ctx.encrypt([recipient], gpgme.ENCRYPT_ALWAYS_TRUST, plaintext, ciphertext)
		ciphertext.seek(0)

		# generate new multipart encrypted mail
		multipart = email.mime.multipart.MIMEMultipart("encrypted")
		multipart.preamble = "This is an OpenPGP/MIME encrypted message (RFC 4880 and 3156)"
		del multipart['MIME-Version']
		pgpencrypted = email.mime.application.MIMEApplication("Version: 1","pgp-encrypted",email.encoders.encode_noop)
		pgpencrypted.add_header("Content-Description","PGP/MIME version identification")
		del pgpencrypted['MIME-Version']
		octetstream = email.mime.application.MIMEApplication(ciphertext.getvalue(),"octet-stream",email.encoders.encode_noop,name="encrypted.asc")
		octetstream.add_header("Content-Disposition","inline",filename='encrypted.asc');
		octetstream.add_header("Content-Description","OpenPGP encrypted message")
		del octetstream['MIME-Version']
		multipart.attach(pgpencrypted)
		multipart.attach(octetstream)
		for key in self.mail.keys():
			multipart[key] = self.mail[key]
		multipart.set_param("protocol","application/pgp-encrypted");
		del multipart['Content-Transfer-Encoding']
		
		self.mail = multipart
		return

	def store(self):
		# delete old message
		# self.imap.uid('store',self.uid,'+FLAGS','(\Deleted)')
		self.imap.expunge()
		# store message
		fp = StringIO()
		g = Generator(fp, mangle_from_=False, maxheaderlen=60)
		g.flatten(self.mail)
		text = fp.getvalue()
		if self.seen:
			self.imap.append(self.mailbox,'(\Seen)','',fp.getvalue())
		else:
			self.imap.append(self.mailbox,'(\\Seen)','',fp.getvalue())

	def __str__(self):
		return str(self.mail)
