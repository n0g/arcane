""" IMAP Abstraction

This Module allows easy Abstraction of an IMAP Connection, Mailboxes and
E-Mails. It provides Iterators so that we can easily iterate over all
E-Mails.

The E-Mail class also contains code for the extraction, encryption and
repackaging of Payload. Which should probably be moved to a different
module.

The MIT License (MIT)

Copyright (c) 2013 Matthias Fassl <mf@n0g.at>

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
THE SOFTWARE.

"""
import sys
import types
import time
import socket
import imaplib
import email
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
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
		self.seen = True

	def __iter__(self):
		return self

	def next(self):
		self.curnum += 1
		try:
			typ, data = self.imap.uid('fetch',self.numbers[self.curnum],'(RFC822)')
			if data == None:
				return StopIteration
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

	def isEncrypted(self):
		if self.mail.get_content_type() == "multipart/encrypted":
			return True
		else:
			return False


	def encryptPGP(self,key):
		# initialize variables for encryption
		plaintext = BytesIO(self._extractMIMEPayload(self.mail))
		ciphertext = BytesIO()
		ctx = gpgme.Context()
		ctx.armor = True
		# find public key
		try:
			recipient = ctx.get_key(key)
		except:
			print >> sys.stderr, "Couldn't find GPG Key"
			sys.exit(1)
		# encrypt data
		ctx.encrypt([recipient], gpgme.ENCRYPT_ALWAYS_TRUST, plaintext, ciphertext)
		ciphertext.seek(0)
		# package encrypted data in valid PGP/MIME
		self.mail = self._generatePGPMIME(ciphertext.getvalue())
		return

	def _extractMIMEPayload(self,mail):
		# in case the mail only consists of one message
		# it is assumed that a message consisting of one part is a text
		# (not html) message
		if type(mail.get_payload()) == types.StringType:
			# TODO: copy content-type and content-transfer-encoding
			mimemail = MIMEText(str(mail.get_payload()))
			if mail.has_key('Content-Transfer-Encoding'):
				del mimemail['Content-Transfer-Encoding']
				mimemail['Content-Transfer-Encoding'] = mail['Content-Transfer-Encoding']
		# this gets easier if the message is a multipart message to
		# begin with (because all content type and transfer encoding
		# headers stay the same)
		else:
			mimemail = MIMEMultipart("mixed")
			for payload in mail.get_payload():
				mimemail.attach(payload)
		fp = StringIO()
		g = Generator(fp, mangle_from_=False, maxheaderlen=60)
		g.flatten(mimemail)
		return fp.getvalue()

	def _generatePGPMIME(self,ciphertext):
		# intialize multipart email and set preamble
		multipart = email.mime.multipart.MIMEMultipart("encrypted")
		multipart.preamble = "This is an OpenPGP/MIME encrypted message (RFC 4880 and 3156)"

		# first part is the Version Information
		del multipart['MIME-Version']
		pgpencrypted = email.mime.application.MIMEApplication("Version: 1","pgp-encrypted",email.encoders.encode_noop)
		pgpencrypted.add_header("Content-Description","PGP/MIME version identification")
		del pgpencrypted['MIME-Version']

		# the second part contains the encrypted content
		octetstream = email.mime.application.MIMEApplication(ciphertext,"octet-stream",email.encoders.encode_noop,name="encrypted.asc")
		octetstream.add_header("Content-Disposition","inline",filename='encrypted.asc');
		octetstream.add_header("Content-Description","OpenPGP encrypted message")
		del octetstream['MIME-Version']
		multipart.attach(pgpencrypted)
		multipart.attach(octetstream)

		# copy headers from original email
		for key in self.mail.keys():
			multipart[key] = self.mail[key]
		multipart.set_param("protocol","application/pgp-encrypted");
		del multipart['Content-Transfer-Encoding']
		
		return multipart

	def store(self):
		# delete old message
		self.imap.uid('store',self.uid,'+FLAGS','(\Deleted)')
		self.imap.expunge()
		# convert message to string
		fp = StringIO()
		g = Generator(fp, mangle_from_=False, maxheaderlen=60)
		g.flatten(self.mail)
		# store message
		if self.seen:
			self.imap.append(self.mailbox,'(\Seen)','',fp.getvalue())
		else:
			self.imap.append(self.mailbox,'(\\Seen)','',fp.getvalue())

	def __str__(self):
		return str(self.mail)
