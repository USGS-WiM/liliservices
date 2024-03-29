![USGS](USGS_ID_black.png) ![WIM](wimlogo.png)

# THIS REPO IS ARCHIVED
## Please visit https://code.usgs.gov/WiM/liliservices for the active repo of this project.

# LIDE Web Services

This is the web services codebase for the Laboratory for Infectious Disease and the Environment's Laboratory Information Management System (LIDE LIMS) (the web client application codebase can be found [here](https://github.com/USGS-WiM/lili)).

This project was built with Django, Django REST Framework, Psycopg2, Celery, and RabbitMQ.

#### Installation
*Prerequisite*: Please install Python 3 by following [these instructions](https://wiki.python.org/moin/BeginnersGuide/Download).

*Prerequisite*: Please install PostgreSQL by following [these instructions](https://www.postgresql.org/docs/devel/tutorial-install.html).

*Prerequisite*: Please install Celery and RabbitMQ by following [these instructions](https://docs.celeryproject.org/en/latest/getting-started/first-steps-with-celery.html).

```bash
git clone https://github.com/USGS-WiM/liliservices.git
cd liliservices

# install virtualenv
pip3 install virtualenv

# create a virtual environment
virtualenv env

# activate the virtual environment
source /env/bin/activate

# install the project's dependencies
pip3 install -r requirements.txt

# migrate the database
python3 manage.py migrate

# install the custom SQL Median aggregate function in the database
psql -U lideadmin -d lili -f create_aggregate_median.sql

# install RabbitMQ, the message broker used by Celery (which is itself was installed by the prior pip command)
sudo apt-get install rabbitmq-server

```

## Environments
Note that on Windows, the default arrangement of a settings.py file reading a settings.cfg file (to keep sensitive information out of code repositories) seems to  work fine, but in Linux this does not seem to work, and so all the `CONFIG.get()` calls should be replaced by simple values.

## Development server

Run `python3 manage.py runserver` for a dev server with live reload. Navigate to `http://localhost:8000/lideservices/`. The web services will automatically reload if you change any of the source files. This will use the development environment configuration.

To use Celery in development, run `celery -A liliservices worker -l info` (note that this no longer seems to work on Windows, and so the `--pool=solo` option should be appeneded to the preceding command).

## Production server

In a production environment (or really, any non-development environment) this Django project should be run through a dedicated web server, likely using the Web Server Gateway Interface [(WSGI)](https://modwsgi.readthedocs.io/en/latest/). This repository includes sample configuration files (*.conf in the root folder) for running this project in [Apache HTTP Server](https://docs.djangoproject.com/en/dev/howto/deployment/wsgi/modwsgi/).

Additionally, Celery must be set up as a service or daemon for Django to use it. On Linux (note that Celery is no longer supported on Windows) follow the instructions [here](https://docs.celeryproject.org/en/latest/userguide/daemonizing.html#daemonizing) (also read the docs about how Celery and Django connect [here](https://docs.celeryproject.org/en/latest/django/first-steps-with-django.html#django-first-steps)). For convenience, the necessary documents are in this repository:
* `default_celeryd` (sourced from the [official Celery documentation](https://docs.celeryproject.org/en/latest/userguide/daemonizing.html#example-configuration), note that this file should be saved on the server as `/etc/default/celeryd`)
* `init.d_celeryd` (sourced from the [official Celery repo](https://github.com/celery/celery/blob/master/extra/generic-init.d/celeryd), note that this file should be saved on the server as `/etc/init.d/celeryd`, and its file permissions should be set to 755 (which can be done with the command `sudo chmod 755 /etc/init.d/celeryd`); also register the script to run on boot with the command `sudo update-rc.d celeryd defaults`)

## Authors

* **[Aaron Stephenson](https://github.com/aaronstephenson)**  - *Lead Developer* - [USGS Web Informatics & Mapping](https://wim.usgs.gov/)

See also the list of [contributors](../../graphs/contributors) who participated in this project.

## License

This software is in the Public Domain. See the [LICENSE.md](LICENSE.md) file for details

## Suggested Citation
In the spirit of open source, please cite any re-use of the source code stored in this repository. Below is the suggested citation:

`This project contains code produced by the Web Informatics and Mapping (WIM) team at the United States Geological Survey (USGS). As a work of the United States Government, this project is in the public domain within the United States. https://wim.usgs.gov`


## About WIM
* This project authored by the [USGS WIM team](https://wim.usgs.gov)
* WIM is a team of developers and technologists who build and manage tools, software, web services, and databases to support USGS science and other federal government cooperators.
* WIM is a part of the [Upper Midwest Water Science Center](https://www.usgs.gov/centers/wisconsin-water-science-center).
