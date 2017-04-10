from fabric.api import *
from fabric.operations import *
from fabric.contrib import django
from fabric.contrib.project import rsync_project
from fabric.contrib.console import confirm
from fabric.contrib.files import exists
from fabric.colors import yellow, green, blue, red
from fabric.operations import _prefix_commands, _prefix_env_vars
from contextlib import contextmanager as _contextmanager

import sys, os

abspath = lambda filename: os.path.join(
    os.path.abspath(os.path.dirname(__file__)),
    filename
)

# --------------------------------------------
# Finwallet platform cofiguration
# --------------------------------------------

class FabricException(Exception):
    pass

def dev():
    print "Connecting to AWS Server"

    env.setup = True
    env.user = 'ubuntu'     #server username
    env.ubuntu_version = '16.04'

    env.use_ssh_config = True
    env.shell = "/bin/bash -l -i -c"
    env.password = 'your machines password'
    #env.key_filename = abspath('your aws instance credentials .pem')
    env.abort_exception = FabricException

    env.hosts = [
        'ip_address_of_server'
    ]

    env.graceful = True
    env.is_grunt = True
    env.home = '/home/%s' %(env.user)
    env.project = 'your_app_name'

    #local config file path
    env.nginx_config = abspath('devops/myproject')
    env.gcorn_config = abspath('devops/gunicorn.service')
    env.nginx_path = '/etc/nginx/sites-available'
    env.app_sock = '0.0.0.0:8000'
    env.app_path = '%s/%s' %(env.home,env.project)
    env.virtualenvpath = '%s/virtual-env/%s' %(env.home,env.project)
    env.activate = '%s/bin/activate' %(env.virtualenvpath)

    env.rsync_exclude = [
        '/devops',
        'fab*',
        '*.pem',
        '*.pyc',
        '.gitignore',
    ]

    return


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

def update():
    print 'Start updating the system'
    sudo('apt-get update')
    return

def sync_code_base():
    print 'Syncing Django Project code base'
    rsync_project(env.app_path, abspath('') + '*', exclude=env.rsync_exclude, delete=True, default_opts='-rvz')
    sudo('chown -R %s:%s %s' % (env.user, env.user, env.app_path))

def install_python_dependency():
    """
    install python dependency packages
    """
    print "Installing python dependency packages"
    
    sudo(
        'apt-get -y install '
        'python-setuptools libmysqlclient-dev '
        'python-mysqldb libmysqlclient-dev '
        'python-dev make automake gcc '
        'libxml2 libxml2-dev libxslt-dev '
        'python-dev libtidy-dev python-lxml '
        'htop iftop'
    )

    sudo(
        'apt-get install -y '
        'libjpeg62 zlib1g-dev libjpeg8-dev '
        'libjpeg-dev libfreetype6-dev '
        'libpng-dev libgif-dev'
    )
    sudo('apt-get -y install libcurl4-gnutls-dev librtmp-dev')
    sudo('apt-get install -y libjpeg-turbo8-dev')
    sudo('apt-get install -y libjpeg62-dev')
    

def install_pip():
    update()
    print "Installing python pip in the system"
    sudo('apt-get install python-pip -y')
    return


def install_virtualenv():
    print "Installing python virtualenv"
    sudo('pip install virtualenv')
    run('mkdir -p %s/virtual-env' % env.home)
    sudo('chown -R %s:%s /home/ubuntu/virtual-env' % (env.user, env.user))
    print "Creating virtualenv for django"
    sudo('virtualenv %s' % env.virtualenvpath)
    sudo('chmod +x %s' % env.activate)
    print "Virtualenv installed"
    sudo('apt-get -y install build-essential libssl-dev  libffi-dev python-dev')
    return

def pip_requirements():
    sudo('source %s/bin/activate; cd %s; pip install -r requirements.txt' % (env.virtualenvpath, env.app_path))

def config_gunicorn():
    print 'Configuring gUnicorn'
    default_config='/etc/systemd/system/gunicorn.service'
    if exists(default_config):
        sudo('rm /etc/systemd/system/gunicorn.service')
        print 'Deleted gunicorn systemd file'

    print 'Install gUnicorn config'
    put('%s' % (env.gcorn_config), '/etc/systemd/system/', use_sudo=True)
    print 'Restarting gUnicorn'
    sudo("systemctl enable gunicorn")
    sudo("systemctl start gunicorn")

def install_nginx():
    print 'Installing NGINX'
    sudo("apt-get install -y nginx")
    sudo('systemctl enable nginx')
    sudo('systemctl start nginx')
    return

def nginx_config():
    print 'Install NGINX config'
    put('%s' % (env.nginx_config), '/etc/nginx/sites-available', use_sudo=True)
    sudo('ln -s %s/myproject /etc/nginx/sites-enabled' % (env.nginx_path))

    print 'Restarting NGINX and gunicorn'
    sudo("systemctl restart nginx")
    sudo("systemctl restart gunicorn.service")
    return

def deploy():
    with cd('%s' % env.app_path):
        run('mkdir static')
        run('source %s; ./manage.py collectstatic' % env.activate)
        run('source %s; ./manage.py makemigrations' % env.activate)
        run('source %s; ./manage.py migrate' % env.activate)
        #run('source %s; gunicorn --bind %s %s.wsgi:application' % (env.activate, env.app_sock, env.project))
    sudo("systemctl restart gunicorn.service")
    
########################################################################
#--------------------------End of fabric file--------------------------#
########################################################################
