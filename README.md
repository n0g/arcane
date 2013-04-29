# arcane #

Arcane is an encryption tool which connects to your IMAP account, authenticates as you and encrypts all unencrypted emails with your public GPG key. This way you can make sure you don't store any unencrypted mails on the mail server and you can still read them with any email client that supports PGP/MIME encryption.

**ATTENTION: BE CAREFUL THIS PROGRAM ENCRYPTS ALL YOUR MAILS. WITHOUT THE PGP KEY YOUR EMAILS ARE LOST. MAKE BACKUPS!**

## Advantages ##
* Encrypt all your Mails in case the server is hijacked or your server provider spies on you 
* Is compatible with all mail clients that support PGP/MIME

## Disadvantages ##
* Does not encrypt metadata
* Does not replace transport security
* Depending on your mail client you may not be able to search your emails properly if they are encrypted
* The popular Enigmail Plugin for Thunderbird seems to go haywire if you encrypt a few thousand emails (try disabling autmatic decryption)

## Dependancies ##
* imaplib (Included in the Python Standard Library)
* python-gpgme https://launchpad.net/pygpgme (Should be available in Debian and Ubuntu repositories)

## Known Issues ##
* read/unread state is not preserved (all emails are displayed as read after using this tool)

## Usage ##
    arcane -h hostname [-p port] [-s] -u username [-d] -k identifier
        -h,--hostname	Hostname of IMAP4 compatible mailserver
        -p,--port	Optional port number of IMAP4 service
        -s,--ssl	Optional SSL flag (changes default port to 993)
        -u,--username	Username that should be used for authentication
        -k,--key	Public key Identifier that will be used to encrypt the mails
        -m,--mailbox	Optional Mailbox argument which specifies which mailbox should be encrypted
        -d,--decrypt	Optional argument for decryption (useful for key rollover)


## Example ##
Encrypt all emails on an SSL IMAP compatible mailserver for the user n0g
with the public pgp key 77FA1F54


     ./arcane --hostname mail.example.com --ssl --username n0g --key 77FA1F54

Encrypt only the 'office' mailbox on an SSL IMAP compatible mailserver


     ./arcane --hostname mail.example.com --ssl --mailbox office --username n0g --key 77FA1F54
