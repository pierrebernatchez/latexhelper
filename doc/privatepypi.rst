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
    sudo apt-get install python3.8-venv  # needed on ubuntu
    python3.8 -m venv devpi_venv    
    source devpi_venv/bin/activate    
    python -m pip install -U pip
    pip install wheel
    pip install setuptools
    pip install twine

Note:

   These lines may help  if you run into trouble with 'setuptools_rust'
   when installing twine.
   
.. code-block:: bash

    pip3.8 install setuptools-rust
    pip install --upgrade pip
    

		
Set up devpi server on our laptop
---------------------------------

Install devpi client and web server
The non web server - devpi-server - is  installed as a consequence.

newblock

.. code-block:: bash
		
    pip install -q -U devpi-server
    devpi-server --version
    devpi-init
    mkdir devpi-stuff
    cd devpi-stuff
    devpi-gen-config # generates a bunch of config files for different scenarios
    
    

		


.. code-block:: bash
		
    pip install -U devpi-web devpi-client

Initialize an empty index (at /var/devpi-server by default)
Note I had a permissions problem with the init one.
So first I manually do this:

.. code-block:: bash

   sudo mkdir  /var/devpi-server
   sudo chown ubuntu:ubuntu /var/devpi-server

.. code-block:: bash

    devpi-init

We want a config file for supervisor daemon to use.
This will generate a bunch of config files under the current
directory, the one we want included.

.. code-block:: bash

    cd ${HOME}/devpi_setup
    devpi-gen-config

This gives us the file gen-config/supervisor-devpi.conf
to copy to /etc/supervisor/conf so that we can start
up the server.  I started by editing it to say
start=False so that it would need to be started
up manually.  Then I copied it to the right place for it.

.. code-block:: bash

    sudo cp gen-config/supervisor-devpi.conf /etc/supervisor/conf.d/devpi-server.conf
    sudo supervisorctl update
    sudo supervisorctl start devpi-server

Create a user, login as him and create the 'dev' index

.. code-block:: bash

    devpi user -c pbernatchez password=foobar
    devpi login pbernatchez --password=foobar
    devpi index -c dev bases=root/pypi

Use our dev index
    
.. code-block:: bash

    devpi use testuser/dev

Now we can make use of the private index.

We are using flit to publish to our index and it
relies on the file : ~/.pypirc.

So we make an entry there for our index.  I gave it the name 'mypypi':

::
   
    [distutils]
    index-servers =
       mypypi
       testpypi

    [mypypi]
    repository = http://localhost:3141/pbernatchez/dev
    username = pbernatchez

    [testpypi]
    repository = https://test.pypi.org/legacy/
    username = pbernatchez

From here on, using flit, we can refer it as 'mypypi'.

.. code-block:: bash

    deactivate
    cd /home/ubuntu/repos/animbboard
    source venv/bin/activate
    flit build
    flit publish --repository mypypi
    pip uninstall  animbboard
    pip install -i http://localhost:3141/pbernatchez/dev  animbboard


