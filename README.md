Welcome to the Nginx-Gunicorn-Django-deployment-in-Ubuntu-16.04-Fabric

We are going to create a fabric file which will deploy the finwallet django application to the Internet. To do this, we should have to have an idea about fabric.

Fabric is a Python library and command-line tool for streamlining the use of SSH for application deployment or systems administration tasks. It provides a basic suite of operations for executing local or remote shell commands (normally or via sudo) and uploading/downloading files, as well as auxiliary functionality such as prompting the running user for input, or aborting execution.

Gunicorn ‘Green Unicorn’ is a Python WSGI HTTP Server for UNIX. It’s a pre-fork worker model ported from Ruby’s Unicorn project. The Gunicorn server is broadly compatible with various web frameworks, simply implemented, light on server resources, and fairly speedy.

Freatures:

     * Natively supports WSGI, Django, and Paster
     * Automatic worker process management
     * Simple Python configuration
     * Multiple worker configurations
     * Various server hooks for extensibility
     * Compatible with Python 2.x >= 2.6 or 3.x >= 3.2
Installing fabric via pip:

                      $ pip install fabric
Installing fabric via apt:

                      $ sudo apt-get install fabric
Fabric is installed in the system. Now user can create a python file named fabfile.py. In the fab file, firstly user have to import fabric modules which will help executing remote shell commands and functionality.

from fabric.api import *
from fabric.operations import *
from fabric.contrib import django
from fabric.contrib.project import rsync_project
from fabric.contrib.console import confirm
from fabric.contrib.files import exists
from fabric.colors import yellow, green, blue, red
from fabric.operations import _prefix_commands, _prefix_env_vars
from contextlib import contextmanager as _contextmanager
Now in the dev() function, user should be the username of the server e.g 'ubuntu', ubuntu_version should be the version number of the server e.g '16.04', password and hosts should be the user password and host's ip address of the server.

env.home = home directory path of the user, e.g "/home/ubuntu"

env.project = name of the project

In the #local config file path we use the files which will be put on the server...

env.nginx_config = is the absolute path where the nginx configuration file is stored

env.gcorn_config = is the absolute path where the gunicorn systemd service file is stored

env.nginx_path = is the absolute path where user will put the nginx config file

env.app_sock = consists of ip address of the server and the port number on which the server will be run

env.app_path = is the absolute path of the project/application

env.virtualenvpath = is the absolute path of the virtual environment which will be created later

env.activate = is the absolute path which will activate the virtual environment

Using the env.rsync_exclude variable we define a list of files which will not send to the server. In the install() function user should call the functions which will be implemented to the server.

def install():
    update()
    sync_code_base()
    install_python_dependency()
    install_pip()
    install_virtualenv()
    pip_requirements()
    config_gunicorn()
    install_nginx()
    nginx_config()   
    return
Now, the functionalities of the functions will be described below...

update() function updates the apt list and package dependencies.

sync_code_base() function will rsync the whole project files to the server that means project files will be copied to the server's home directory from the local machine. And also changed the permission to user:user

install_python_dependency() function will install all the python dependencies to the server.

In install_pip() function while installing pip using apt-get install python-pip -y the apt should be updated. For this reason the update() function is being used.

install_virtualenv() function virtual environment will be installed using pip and then a directory will be created in the home folder called virtual-env and change the permission to user:user. After this, a virtual environment will be created and make it executable. The below command will remove the virtual environment issues.

sudo('apt-get -y install build-essential libssl-dev libffi-dev python-dev')

In the pip_requirements() function the virtual environment will be activated and installed the django modules using pip in requirements.txt file.

Now user have to create and open a systemd service file for Gunicorn with sudo privileges in text editor:

sudo vim /etc/systemd/system/gunicorn.service

User should copy and paste the following:

    [Unit]
    Description=gunicorn daemon
    After=network.target
    
    
    [Service]
    User=ubuntu
    Group=www-data
    WorkingDirectory=/home/ubuntu/finwallet
    ExecStart=/home/ubuntu/virtual-env/finwallet/bin/gunicorn --workers 3 --bind unix:/home/ubuntu/finwallet/finwallet.sock finwallet.wsgi:application
    
    
    [Install]
    WantedBy=multi-user.target
    Start with the [Unit] section, which is used to specify metadata and dependencies. User'll put a description of the service here and tell the init system to only start this after the networking target has been reached.

In the [Service] section, specify the user and group that the user wants to process to run under. User should give regular user account ownership of the process since it owns all of the relevant files and should give group ownership to the www-data group so that Nginx can communicate easily with Gunicorn.

User'll then map out the working directory and specify the command to use to start the service. In this case, user'll have to specify the full path to the Gunicorn executable, which is installed within the virtual environment. User will bind it to a Unix socket within the project directory since Nginx is installed on the same computer. This is safer and faster than using a network port. There are 3 specified worker processes in this case.

In the [Install] section, this will tell systemd what to link this service to if user enables it to start at boot. Then the user can enable and start the gunicorn service so that it can starts at boot.

install_nginx() function will install the nginx to the server and make it enable and start so that it can starts at boot.

In the nginx_config() function put() command will put the nginx configuration called 'myproject' to the /etc/nginx/sites-available directory and link this file to the /etc/nginx/sites-enabled directory. Now restart the nginx service and gunicorn for applying changes.

Here is the nginx config file "myproject":

server {
    listen 80;
    server_name server_ip_address;

    location = /favicon.ico { access_log off; log_not_found off; }
    location /static/ {
        root /home/ubuntu/finwallet;
    }

    location / {
        include proxy_params;
        proxy_pass http://unix:/home/ubuntu/finwallet/finwallet.sock;
    }
  }


In the deploy() function, first go to the app directory and create a static folder and collect all the static files using ./manage.py collectstatic. Now using ./manage.py makemigrations and ./manage.py migrate command user can migrate and apply the database schema to the application. At last the gunicorn service should restart...
