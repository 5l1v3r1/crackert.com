#!/usr/bin/env python
# 

import cgi
import json
import re
import os
import urllib
import sqlite3
import smtplib
from email.mime.text import MIMEText
from time import time
import base64
import random


# init values
msg = ""
arguments = cgi.FieldStorage()

dblocation = '/var/www/crackert.com/database/crackert.db'

googlesecret = "<oldproject>"
googleapiurl = "https://www.google.com/recaptcha/api/siteverify?"

emaillogin = '<alsosecret>'
emailpassword = "<oldproject>"

registrationmailfile = '/var/www/crackert.com/views/registrationemail'
newdomainmailfile = '/var/www/crackert.com/views/newdomainemail'

mainpageview = '/var/www/crackert.com/views/mainpage'
messageview = '/var/www/crackert.com/views/message'

generatecharset = "123abqrsjcdewxyzfghi9kmnop45678tuv"

illegalsubdomains = ['www','mail', 'ns1', 'ns2', 'admin', 'mailfilter', 'ftp', 'localhost']



def sendmail(fromad, toad, message):
	''' Send an email '''

	s = smtplib.SMTP('<alsosecret>', 587)
	s.login(emaillogin, emailpassword)
	s.sendmail(fromad, [toad], message.as_string())
	s.quit()

def validateip(s):
	''' Validate an IP address for regular IPv4 format '''

	a = s.split('.')
	if len(a) != 4:
		return False
	for x in a:
		if not x.isdigit():
			return False
		i = int(x)
		if i < 0 or i > 255:
			return False
	return True

def subdomainexists(name):
	''' Check if subdomain name exist yet '''

	conn = sqlite3.connect(dblocation)
	c = conn.cursor()

	if c.execute('SELECT id FROM accounts WHERE subdomain = ?', (name,)).fetchone() != None:
		conn.close()
		return True

	if c.execute('SELECT id FROM changequeue WHERE subdomain = ?', (name,)).fetchone() != None:
		conn.close()
		return True

	if c.execute('SELECT id FROM subdomains WHERE subdomain = ?', (name,)).fetchone() != None:
		conn.close()
		return True

	conn.close()
	return False

def generatesubdomain():
	''' Generate subdomain name '''

	global generatecharset

	sublength = 3

	while True:
		subdomain = "".join( [random.choice(generatecharset) for i in xrange(sublength)] )

		if subdomainexists(subdomain) or subdomain in illegalsubdomains:
			sublength += 1
		else:
			break

	return subdomain

def generatesecret():
	''' Generate secret token for security stuff '''

	return base64.b64encode(os.urandom(32)).replace('=','').replace('/','').replace('+','')




# print header
print "Content-Type: text/html;charset=utf-8"
print ""


#try:

# USER CHANGES DNS IP
if 'token' in arguments and 'ip' in arguments:

	msg = "Error"

	ip = str(arguments.getvalue('ip'))
	token = str(arguments.getvalue('token'))

	if validateip(ip) or ip == "this":
		if len(token) > 3 and len(token) < 1024:

			conn = sqlite3.connect(dblocation)
			c = conn.cursor()

			subdomain = c.execute('SELECT subdomain FROM accounts WHERE domaintoken=?', (token,)).fetchone()

			if subdomain != None:

				subdomain = subdomain[0]

				if len(subdomain) > 2:

					checkid = c.execute('SELECT id FROM changequeue WHERE subdomain=?', (subdomain,)).fetchone()

					if checkid != None:
						msg = "WaitForChange"

					else:
						if ip == "this":
							ip = cgi.escape(os.environ["REMOTE_ADDR"])

						c.execute("insert into changequeue (subdomain, ip) values (?, ?)", (subdomain, ip))
						conn.commit()

						if c.execute('SELECT id FROM subdomains WHERE subdomain=?', (subdomain,)).fetchone() == None:
							c.execute("INSERT into subdomains (subdomain, ip) values (?, ?)", (subdomain, ip))
							conn.commit()
						else:
							c.execute("UPDATE subdomains SET ip=? WHERE subdomain=?", (ip, subdomain))
							conn.commit()

						msg = "Success"

	print msg
	conn.close()
	exit(0)





# REGISTRATION
elif 'g-recaptcha-response' in arguments and 'email' in arguments:

	msg = "An error occurred when processing the form. This could be due to a captcha error, or you're email address already has an account."

	email = str(arguments.getvalue('email'))
	captcha = str(arguments.getvalue('g-recaptcha-response'))

	if len(email) > 3 and len(email) < 1024 and len(captcha) > 3 and len(captcha) < 1024:
		if re.match("^.+\\@(\\[?)[a-zA-Z0-9\\-\\.]+\\.([a-zA-Z]{2,3}|[0-9]{1,3})(\\]?)$", email) != None:

			conn = sqlite3.connect(dblocation)
			c = conn.cursor()

			if c.execute('SELECT id FROM registration WHERE email=?', (email,)).fetchone() == None:
				if c.execute('SELECT id FROM accounts WHERE email=?', (email,)).fetchone() == None:

					arguments = {}
					arguments["remoteip"] = cgi.escape(os.environ["REMOTE_ADDR"])
					arguments["secret"] = googlesecret
					arguments["response"] = captcha
					
					url = googleapiurl + urllib.urlencode(arguments)

					response = urllib.urlopen(url).read()
					responsejson = json.loads(response)

					if responsejson['success'] == True:

							token = generatesecret()

							c.execute("insert into registration (email, token, timestamp) values (?, ?, ?)", (email, token, str(time())))
							conn.commit()

							with open(registrationmailfile,'r') as fin:
								registrationemail = fin.read()

							arguments = {}
							arguments["token"] = token
							arguments["email"] = email

							registrationemail = registrationemail.replace("[LINK]", "https://www.crackert.com/?" + urllib.urlencode(arguments))
							emailmsg = MIMEText(registrationemail, 'html')

							emailmsg['Subject'] = 'Crackert email verification'
							emailmsg['From'] = 'registration@crackert.com'
							emailmsg['To'] = email

							sendmail('registration@crackert.com', email, emailmsg)

							msg = "Thank you for registering. Please follow the instructions in your mailbox."




# VALIDATE EMAIL
elif 'token' in arguments and 'email' in arguments:

	msg = "An error occurred. This could be caused by a wrong token. Please contact the website administrator."

	email = str(arguments.getvalue('email'))
	token = str(urllib.unquote(arguments.getvalue('token')))

	if len(email) > 3 and len(email) < 1024 and len(token) > 3 and len(token) < 1024:

			conn = sqlite3.connect(dblocation)
			c = conn.cursor()

			# check if it's an email reset
			

			# else it's a registration
			if c.execute('SELECT id FROM accounts WHERE email=?', (email,)).fetchone() == None:

				dbtoken = c.execute('SELECT token FROM registration WHERE email=?', (email,)).fetchone()

				if dbtoken != None:

					dbtoken = dbtoken[0]

					if len(dbtoken) > 3:

						if dbtoken == token:
							
							with open(newdomainmailfile,'r') as fin:
								newdomainemail = fin.read()

							subdomain = generatesubdomain()
							domaintoken = generatesecret()

							c.execute("insert into accounts (email, registertime, subdomain, domaintoken) values (?, ?, ?, ?)", (email, str(time()), subdomain, domaintoken))
							conn.commit()

							newdomainemail = newdomainemail.replace("[SUBDOMAIN]", subdomain)
							newdomainemail = newdomainemail.replace("[TOKEN]", domaintoken)

							emailmsg = MIMEText(newdomainemail, 'html')

							emailmsg['Subject'] = 'Crackert domain activated'
							emailmsg['From'] = 'registration@crackert.com'
							emailmsg['To'] = email

							sendmail('registration@crackert.com', email, emailmsg)

							c.execute("DELETE FROM registration WHERE email=?", (email, ))
							conn.commit()

							msg = "Thank you for registering! A subdomain has been created. Please follow the instructions in your mailbox."


#except:
#	msg = "An error occurred when processing forms. Please contact the website's administrator."



with open(mainpageview,'r') as fin:
	mainpage = fin.read()

if msg != "":
	with open(messageview,'r') as fin:
		message = fin.read()
	message = message.replace("[CONTENT]", msg)
	mainpage = mainpage.replace("[MESSAGE]", message)

else:
	mainpage = mainpage.replace("[MESSAGE]","")

print mainpage