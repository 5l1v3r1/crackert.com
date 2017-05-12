import sqlite3
from subprocess import call
import time


serialnumber = time.strftime("%Y%m%d%H")

forwardfileNew = '''$ORIGIN crackert.com.
$TTL 86400           ; default time to live

@ IN SOA ns1.crackert.com. admin.crackert.com. (
           '''+serialnumber+'''  ; serial number
           3600       ; Refresh
           3600        ; Retry
           864000      ; Expire
           86400       ; Min TTL
           )

	NS	ns1.crackert.com.
	NS	ns2.crackert.com.
	MX	10	mailfilter.hostnet.nl.
mail	IN	A	91.184.0.100
www	IN	A	37.128.146.107
ns1     IN      A       37.128.146.107
ns2     IN      A       37.128.149.90
crackert.com. IN  A 37.128.146.107

'''

conn = sqlite3.connect('/var/www/crackert.com/database/crackert.db')
c = conn.cursor()

currentconfig = c.execute('SELECT subdomain,ip FROM subdomains').fetchall()

for subdomain in currentconfig:
  forwardfileNew += "%s	IN	A	%s\n" % (subdomain[0], subdomain[1])

forwardfileNew += "*.crackert.com.	IN	A	37.128.146.107\n"

with open("/etc/nsd3/www.crackert.com.forward","w") as fout:
	fout.write(forwardfileNew)

call(["/usr/sbin/nsdc", "rebuild"])
call(["/usr/sbin/nsdc", "reload"])
call(["/usr/sbin/nsdc", "notify"])

c.execute("delete from changequeue")
conn.commit()
