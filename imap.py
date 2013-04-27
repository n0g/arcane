import imaplib

class IMAPConnection:
	def __init__(self,address,port,ssl,username,password):
		# connect to mail server
		if ssl == True:
			self.imap = imaplib.IMAP4_SSL(address,port)
		else:
			self.imap = imaplib.IMAP4(address,port)
		# authenticate
		self.imap.login(username,password)

class IMAPMail:
	def __init__(self,mailbox,number,mail):
		self.mailbox = mailbox
		self.number = number
		self.mail = mail

	def __str__(self):
		return "Mailbox: " + self.mailbox + " Number: " + str(self.number) + "\n" + self.mail

class IMAPIterator:
	def __init__(self,conn):
		self.imap = conn.imap
		# TODO: fetch list of mailboxes

	def __iter__(self):
		self.selectMailbox("INBOX")
		return self

	def next(self):
		self.curnum += 1
		if self.curnum >= self.mailboxentries:
			# TODO: select next mailbox
			return None
		typ, data = self.imap.fetch(self.numbers[self.curnum],'(RFC822)')
		return IMAPMail(self.mailbox,self.curnum,data[0][1])

	def selectMailbox(self,mailbox):
		self.mailbox = mailbox
		self.mailboxentries = self.imap.select(self.mailbox)
		typ, data = self.imap.search(None, 'ALL')

		if typ != "OK":
			print >> sys.stderr, "Couldn't select Mailbox %s" % (self.mailbox)
			return

		self.numbers = data[0].split()
		self.curnum = -1

	""" Destructor closes mailbox and logs out """
	def __del__(self):
		self.imap.close()
		self.imap.logout()
