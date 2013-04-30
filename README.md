# arcane #

Arcane is a set of tools which allows you to encrypt all your existing
unencrypted mails and all your new incoming mail with a GPG key so that
only you can read them.

## Why do I need this? ##

Many email providers store your emails for you on their servers, so
that you can read them anywhere. This also means that your provider,
anyone who hacks the server and the police (in case the server is
seized) can read your private emails.

If all your emails are GPG encrypted, only you can read them because
only you have access to your secret GPG key.

## What could go wrong? ##

* If you lose your secret GPG key you can not decrypt your emails anymore.
Your emails will be lost. Therefore make a backup of your secret GPG key (i.e. print it).
* After encrypting your emails you will (probably) not be able search
the content of your emails  (because they are encrypted). Searching
for sender or subject should still work.
* The metadata of your emails (sender,subject,date) will not be encrypted.
* Your emails will not be more secure during transit (because they are encyrpted
after arriving at the destination). Tell your friends and colleagues to
encrypt their mails _before_ sending them.

## Install ##

### Dependancies ###
* imaplib (Included in the Python Standard Library)
* python-gpgme https://launchpad.net/pygpgme (Should be available in Debian and Ubuntu repositories)

### Debian ###
    # aptitude install python python-gpgme
    # mkdir -p /usr/local/lib && cd /usr/local/lib
    # git clone https://github.com/n0g/arcane.git
    # cd ../bin 
    # ln -s ../lib/arcane/arcane
    # ln -s ../lib/arcane/arcane-encrypt-mail

Afterwards you should be able to call 'arcane' and 'arcane-encrypt-mail'
and get a usage output.

## Step-by-Step Configuration ##

### Generate GPG Key ###
To generate a new GPG key the following command will guide you through
the key generation process:
   $ gpg --gen-key

You will need to use an RSA key for encryption (do not choose any option
that says 'sign only'). A secure key size is 2048 bit and above, 1024
bit RSA keys are considered insecure.

After the generation process your keypair should be visible with the
following command:
   $ gpg --list-secret-keys


### Copy Public GPG Key to Server ###
(If you do not want automatic encryption of incoming emails or do not
have access to your procmail configuration, then you can skip to
'Encrypting Existing Mails')

Export your key into a .pub file:
    $ gpg --export --armor 77FA1F54 > robin-jankins.pub


Copy the public key to your mailserver:
    $ scp robin-jankins.pub robin.jankins@mail.example.com:~/


Import the public key to your keyring on the mailserver:
   $ gpg --import robin-jankins.pub


### Create procmail Configuration ###
Your procmail configuration file probably lies at '~/.procmailrc'. To
encrypt all your incoming mail you will need to add a rule at the top:
    # encryption
    :0 fw
    * <300000
    | arcane-encrypt-mail --key 77FA1F54


The 'f' tells procmail to use this rule as a filter (i.e. the filtered
email will continue to match other rules). The 'w' tells procmail to
continue with the unfiltered mail if arcane-encrypt-mail exits with an
error (i.e. the mail is already encrypted).

Note that you will either have to set the PATH variable so that the
arcane-encrypt-mail script will be found.


### Encrypt Existing Mails ###
Usually the hostname of your mailserver and your user credentials will
be enough to start arcane. In this example the hostname is
'mail.example.com', SSL needs to be used and the user is
'robin.jankins'.

Your GPG key identifier should be in the list you get after executing
'gpg --list-secret-keys'.

Now you have all the details for starting arcane:
    $ arcane -h mail.example.com -s -u robin.jankins -k 77FA1F54

## Quick Start ##

### Usage ###
    arcane -h hostname [-p port] [-s] -u username [-d] -k identifier
        -h,--hostname	Hostname of IMAP4 compatible mailserver
        -p,--port	Optional port number of IMAP4 service
        -s,--ssl	Optional SSL flag (changes default port to 993)
        -u,--username	Username that should be used for authentication
        -k,--key	Public key Identifier that will be used to encrypt the mails
        -m,--mailbox	Optional Mailbox argument which specifies which mailbox should be encrypted
        -d,--decrypt	Optional argument for decryption (useful for key rollover)


### Examples ###
Encrypt all emails on an SSL IMAP compatible mailserver for the user n0g
with the public pgp key 77FA1F54


     ./arcane --hostname mail.example.com --ssl --username robin.jankins --key 77FA1F54

Encrypt only the 'office' mailbox on an SSL IMAP compatible mailserver


     ./arcane --hostname mail.example.com --ssl --mailbox office --username robin.jankins --key 77FA1F54

Example .procmailrc File if you want to encrypt all incoming mails with procmail


    DEFAULT=$HOME/Maildir
    SHELL=/bin/bash
    PATH=/usr/local/bin:/usr/bin

    # encryption
    :0 fw
    * <300000
    | arcane-encrypt-mail --key 77FA1F54

    # your bunch of filter rules
    # ...

    # default rule
    :0
    $DEFAULT

## Known Issues ##
* read/unread state is not preserved (all emails are displayed as read after using this tool)
