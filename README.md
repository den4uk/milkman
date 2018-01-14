# milkman

## What is this?
This is a simple web app, its intention is to run an office milk purchasing club.
If someone purchases milk once a week (or at other intervals), an email is sent to the 'Milkman'.
Features include:
* Adding/removing/pausing/resuming participants
* Changing the intervals how often milk is purchased
* E-mailing a reminder to the 'Milkman'
* Customising an e-mail template

## Setup
1. Have a Python3.x environment (virtual or native) on your computer/server (how about a Raspberry Pi?!)
2. Get the source code:
```$ git clone https://github.com/den4uk/milkman.git```
3. Enter directory:
```$ cd milkman/```
4. Install your dependables:
```$ pip install -r requirements.txt```
5. Initialise the database for the app:
```
$ python
>>> from milk import *
>>> init_db()
>>> exit()
```
6. Configure the ```config.py``` file with your SMTP settings. Here is an example:
```
MAIL_SERVER = 'smtp.example.com'
MAIL_PORT = 587
MAIL_USE_TLS = True
MAIL_USERNAME ='someone@example.com'
MAIL_PASSWORD = 'pa$$w@rd'
```
7. Run the app in a development mode:
```$ python milk.py```

Default login details:

User: ```admin```

Password: ```admin```

Change the password once logged in!

## Example
Current example of the app in action: https://milk.saz.lt

## Bonus: Deployment Suggestion
(Global configurations are provided, however, virtualenv is recommended)

* Suggested server: Ubuntu server (or a Raspberry Pi)
* Setup a domain/ddns/dyndns; assumed domain: ```milkman.dnsexample.com```
* Assumed location for the source code: ```/opt/milkman/```
* Install ```gunicorn``` (WSGI server) using pip:
```$ sudo pip install gunicorn```

* Setup ```systemctl``` service (so gunicorn runs on system reboots):
```
$ sudo nano /etc/systemd/system/milkapp.service
```

```
[Unit]
Description=gunicorn daemon
After=network.target

[Service]
User=root
Group=www-data
WorkingDirectory=/opt/milkman
ExecStart=`which gunicorn` --workers 1 --reload --preload --access-logfile - --bind 0.0.0.0:8001 milk:app

[Install]
WantedBy=multi-user.target
```

* Now activate the new service:
```
$ sudo systemctl daemon-reload
$ sudo systemctl start milkapp
```

* Install ```nginx``` for use as web proxy:
```$ sudo apt-get install nginx-full```

* Create a site in nginx (entry for your site):
```
$ sudo nano /etc/nginx/sites-available/milkapp
```

```
server {
        listen 80;
        server_name milkman.dnsexample.com;

        location /static/ {
                autoindex off;
                alias /opt/milkman/static/;
        }

        location / {
                include proxy_params;
                proxy_pass http://0.0.0.0:8001;
        }
}

```

* Activate the site (creates a symbolic link):
```
$ sudo ln -s /etc/nginx/sites-available/milkapp /etc/nginx/sites-enabled/milkapp
```

* Reload nginx:
```
$ sudo service nginx reload
```

* Congratulations! Your site should now be serving the world!
