# arcane #

Arcane is an encryption tool which connects to your IMAP account, authenticates as you and encrypts all unencrypted emails with your public GPG key. This way you can make sure you don't store any unencrypted mails on the mail server and you can still read them with any email client that supports PGP/MIME encryption.

On the negative side be aware that this only encrypts your mail body and not any of your metadata. Sender, Recipients, Date and Subject all stay unencrypted!

**ATTENTION: BE CAREFUL THIS PROGRAM CAN DELETE YOUR EMAILS AND/OR
DESTROY THEM BEYOND USE. MAKE A BACKUP BEFORE TRYING THIS ENCRYPTION
TOOL! REALLY. **

## Usage ##
    arcane -h hostname [-p port] [-s] -u username
        -h,--hostname	Hostname of IMAP4 compatible mailserver
        -p,--port	Optional port number of IMAP4 service
        -s,--ssl	Optional SSL flag (changes default port to 993)
        -u,--username	Username that should be used for authentication
        -k,--key	Public key Identifier that will be used to encrypt the mails


## Example ##
     ./arcane --hostname mail.example.com --port 993 --ssl --username n0g --key 77FA1F54
