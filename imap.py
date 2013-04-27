import imaplib
import email

class IMAPConnection:
	def __init__(self,address,port,ssl,username,password):
		self.address = address
		self.port = port
		self.ssl = ssl
		self.username = username

		# connect to mail server
		if ssl == True:
			self.imap = imaplib.IMAP4_SSL(address,port)
		else:
			self.imap = imaplib.IMAP4(address,port)
		# authenticate
		self.imap.login(username,password)

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
		typ, data = self.imap.uid('fetch',self.numbers[self.curnum],'(RFC822)')
		if typ != "OK":
			raise StopIteration
		return IMAPMail(self.mailbox,self.numbers[self.curnum],data[0][1])


class IMAPMail:
	def __init__(self,mailbox,uid,mail):
		self.mailbox = mailbox
		self.uid = uid
		self.mail = email.message_from_string(mail)
		self.subject = self.mail.get('Subject') or ""
		self.sender = self.mail.get('From') or ""
		self.receiver = self.mail.get('To') or ""
		self.date = self.mail.get('Date') or ""

	def __str__(self):
		return self.sender + " " + self.subject + " " + self.date
