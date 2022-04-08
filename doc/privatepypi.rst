Set up a project private package index
======================================

Overview
--------

    This describes setting up a private package index as an
    alternative to the public PyPi index for sharing our package.

    Our software needs to be compatile with using the standard public
    python package index.  At this writing we are not yet ready to
    make it available to the general public. So to ensure we are
    staying compatible with PyPi, we need to run it through the
    process, but with a private packaging index.
    
    **devpi** to the rescue ('https://www.devpi.net/') . It is a
    conforming package index system we can use to serve our private
    package index.


Configure a virtual environment for devpi
-----------------------------------------

This howto is derived from the following tutorial:

<https://devpi.net/docs/devpi/devpi/stable/+doc/quickstart-releaseprocess.html>_


Start by setting up our desired python environment.  On ubuntu we need
to install **python3.8-venv** for the rest of these commands to work.
First remember to get out of whatever virtual environment you are in.


.. code-block:: bash
		
    deactivate                            # escape current virtual env
    cd ${HOME}
    sudo apt install python3.8-venv  # needed on ubuntu
    python3.8 -m venv devpi_venv    
    source devpi_venv/bin/activate
    python -m pip install --no-cache-dir -U pip
    pip install --no-cache-dir setuptools-rust
    pip install --upgrade pip                    # No sure if you need this
    pip install --no-cache-dir wheel
    pip install --no-cache-dir twine

.. raw:: pdf

    PageBreak oneColumn
    
		
Set up devpi server on our laptop
---------------------------------

Install devpi client and web server The non web server -
devpi-server - is installed as a consequence.

.. code-block:: bash
		
    pip install -U devpi-web devpi-client # devpi-server is installed implictly here
    devpi-init
    mkdir devpi-stuff  # 
    cd devpi-stuff     #
    devpi-gen-config   # generates a bunch of config files for different scenarios
    cd ..
    

We are using the 'supervisor' package to manage the startup/shutdown
of our servers. The above generates a configuration file which is
pretty close to what we want called "supervisor-devpi.conf".  But we
created one called "/etc/supervisor/conf.d/ubuntu_devpi_server.conf"
that suits our system configuration a bit better.  These are its
contents:

.. code-block:: bash
		
   ;;; privat package index server
   [program:ubuntu_devpi_server]
   directory=/home/ubuntu
   user = ubuntu
   command=/home/ubuntu/devpi_venv/bin/devpi-server
   autostart = false
   exitcodes=0
   autorestart=unexpected
   priority = 300
   startsecs = 5
   redirect_stderr = true

   
If you want to be open up to the internet rather than just localhost
you are going to want to change your command line above to this.

.. code-block:: bash
		
   command=/home/ubuntu/devpi_venv/bin/devpi-server --host=0.0.0.0 --port=3141
   

We need to get the running supervisor to reread its configurations and
update its in-memory view of configurations.  This will make the new
server known to supervisor.

.. code-block:: bash

   sudo supervisorctl reread
   sudo supervisorctl update

Since our configuration has autostart = false, we need to start it.
   
.. code-block:: bash

   sudo supevisorctl start ubuntu_devpi_server

If and when we want to stop it we can use this command.  But for now
we will leave it running.
   
.. code-block:: bash

   sudo supevisorctl stop ubuntu_devpi_server


Point the devpi client to our running devpi server

.. code-block:: bash

   devpi use http://localhost:3141		

Add our own user, and login as that user.

.. code-block:: bash

   devpi user -c pbernatchez password=somepassword
   devpi login pbernatchez --password=somepassword

Create a "dev" index that uses the root/pypi cache as base so that all pypy.org packages
will appear on that index, and finally we use the new index.

.. code-block:: bash

   devpi index -c dev bases=root/pypi
   devpi use pbernatchez/dev

Now we can make use of the private index.
We are using flit to publish to our index and it
relies on the file : ~/.pypirc.

So we make an entry there for our index.  I gave it the name 'latexhelperpypi'.
My .pypirc file looks like this:

::

    [distutils]
    index-servers =
       latexhelperpypi
       testpypi

    [latexhelperpypi]
    repository = http://localhost:3141/pbernatchez/dev
    username = pbernatchez

    [testpypi]
    repository = https://test.pypi.org/legacy/
    username = pbernatchez


From here on, using flit, we can refer it as 'latexhelperpypi'.

.. code-block:: bash

    deactivate
    cd /home/ubuntu/collab/latexhelper
    source /home/ubuntu/latexhelper_venv/bin/activate
    flit build
    flit publish --repository latexhelperpypi
    pip uninstall  latexhelper
    pip install -i http://localhost:3141/pbernatchez/dev  latexhelper


