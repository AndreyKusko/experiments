Supervisord

 apt-get install supervisor service --status-all | grep super [ + ] supervisor

supervisorctl update asphere: added process group supervisorctl status
asphere RUNNING pid 8892, uptime 0:00:31



Example

sudo nano /etc/supervisor/conf.d/asphere.conf

[program:asphere]
command=/root/asphere/asphereenv/bin/gunicorn --bind 0.0.0.0:8000 main_files.wsgi:application
directory=/root/asphere