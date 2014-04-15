""" GPG Encryption/Decryption Abstraction

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
import os
import sys
import types
from util import Util
from io import BytesIO
import email
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email.mime.application import MIMEApplication
try:
	import gpgme
except ImportError:
	print >> sys.stderr, "Please install python library 'gpgme'"
	sys.exit(1)

class GPGEncryption:
	def encryptPGP(self,mail,keys):
		# initialize variables for encryption
		plaintext = BytesIO(self._extractMIMEPayload(mail))
		ciphertext = BytesIO()
		ctx = gpgme.Context()
		ctx.armor = True
		recipients = list()

		# find public keys
		for key in keys:
			try:
				recipients.append(ctx.get_key(key))
			except:
				print >> sys.stderr, "Couldn't find GPG Key"
				sys.exit(1)
		# encrypt data
		try:
			octx.encrypt(recipients, gpgme.ENCRYPT_ALWAYS_TRUST, plaintext, ciphertext)
		except:
			print >> sys.stderr, "Encryption failed."
			sys.exit(1)

		# package encrypted data in valid PGP/MIME
		ciphertext.seek(0)
		return self._generatePGPMIME(mail,ciphertext.getvalue())

	def _extractMIMEPayload(self,mail):
		# Email is non multipart
		if type(mail.get_payload()) == types.StringType:
			# duplicate content-type and charset
			mimemail = MIMEBase(mail.get_content_maintype(),mail.get_content_subtype(),charset=mail.get_content_charset())
			mimemail.set_payload(mail.get_payload())
			# copy transfer encoding
			if mail.has_key('Content-Transfer-Encoding'):
				del mimemail['Content-Transfer-Encoding']
				mimemail['Content-Transfer-Encoding'] = mail['Content-Transfer-Encoding']
		# for a multipart email just add every sub message
		else:
			mimemail = MIMEMultipart("mixed")
			for payload in mail.get_payload():
				mimemail.attach(payload)

		return Util.flattenMessage(mimemail)

	def _generatePGPMIME(self,mail, ciphertext):
		# intialize multipart email and set preamble
		multipart = MIMEMultipart("encrypted")
		multipart.preamble = "This is an OpenPGP/MIME encrypted message (RFC 4880 and 3156)"

		# first part is the Version Information
		del multipart['MIME-Version']
		pgpencrypted = MIMEApplication("Version: 1","pgp-encrypted",email.encoders.encode_noop)
		pgpencrypted.add_header("Content-Description","PGP/MIME version identification")
		del pgpencrypted['MIME-Version']

		# the second part contains the encrypted content
		octetstream = MIMEApplication(ciphertext,"octet-stream",email.encoders.encode_noop,name="encrypted.asc")
		octetstream.add_header("Content-Disposition","inline",filename='encrypted.asc');
		octetstream.add_header("Content-Description","OpenPGP encrypted message")
		del octetstream['MIME-Version']
		multipart.attach(pgpencrypted)
		multipart.attach(octetstream)

		# copy headers from original email
		for key in mail.keys():
			multipart[key] = mail[key]
		multipart.set_param("protocol","application/pgp-encrypted");
		del multipart['Content-Transfer-Encoding']
		
		return multipart

class GPGDecryption:
	def passphrase_cb(self,uid_hint, passphrase_info, prev_was_bad, fd):
		os.write(fd,self.passphrase)
		os.write(fd,'\n')

	def decryptPGP(self,mail,key,passphrase):
		# extract pgp message
		ciphertext = BytesIO(str(self._extractPGPMessage(mail)))
		ctx = gpgme.Context()
		ctx.armor = True

		# decrypt
		self.passphrase = passphrase
		ctx.passphrase_cb = self.passphrase_cb
		plaintext = BytesIO()
		try:
			ctx.decrypt(ciphertext, plaintext)
		except Gpgme.error as err:
			print >> sys.stderr, "Couldn't decrypt data, bad passphrase?"
			sys.exit(1)
		
		# package message again
		decryptedmail = email.message_from_string(plaintext.getvalue())
		# copy headers from original email
		for key in mail.keys():
			if key == "Content-Type" or key == "Content-Transfer-Encoding":
				continue
			decryptedmail[key] = mail[key]
		return decryptedmail

	def _extractPGPMessage(self,mail):
		# TODO: replace error message with exceptions
		encrypted = ""
		submessages = mail.get_payload()
		for msg in submessages:
			if msg.get_content_subtype() == "pgp-encrypted":
				# check version information
				if not msg.get_payload() == "Version: 1":
					print >> sys.stderr, "Couldn't decrypt message, wrong  PGP Version information"
					return
			if msg.get_content_subtype() == "octet-stream":
				encrypted = msg.get_payload()

		if encrypted == "":
			print >> sys.stderr, "Couldn't decrypt message, no data found"
			return

		return encrypted
