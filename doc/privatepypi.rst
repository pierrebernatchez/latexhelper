Set up a project private package index
======================================

Overview
--------

    At this writing we are only working with the single package
    **animbboard** and there is only one person maintaining it.
    Because of that our current practise is to generate versioned
    tarballs and to 'pip install' from those.

    This describes setting up a private package index as a more
    convenient alternative to using tarballs directly.  We will want
    to do this if/when we have several maintainers or we are
    maintaining several packages.

    Nevertheless, this python software of ours needs to be compatile
    with using the standard python package index, and at this writing
    we are not ready to make it available to the general public.

    So to ensure we are staying compatible with pypi, we need to run
    it through the process, but with a private packaging index.
    **devpi** to the rescue ('https://www.devpi.net/') . It is a
    conforming package index system we can use to serve our private
    package index.


Configuring the SW for  devpi
-----------------------------

This howto is derived from the following tutorial:

<https://devpi.net/docs/devpi/devpi/stable/+doc/quickstart-releaseprocess.html>_

We are working with python3. We want to setup up a virtual environment
that conforms to our assumptions, and then install within that.  We
call the environment devpi_venv.

We create a directory for our setup first.

.. code-block:: bash

    mkdir ${HOME}/devpi_setup
    cd ${HOME}/devpi_setup

We install the bare essentials.

.. code-block:: bash
    
    python3 -m venv devpi_venv
    source devpi_venv/bin/activate
    python -m pip install -U pip
    pip install wheel
    pip install setuptools
    pip install twine

A Restructured Text format viewer I find usefull.

.. code-block:: bash
		
    pip install restview

You invoke it and it keeps re-rendering your file as you modify
it. Like this:

.. code-block:: bash

    restview README.rst


I also find rst2pdf convenient for generating pdf copies of .rst documuents.

.. code-block:: bash
		
    snap install rst2pdf
    rst2pdf doc/privatepypi.rst -o reformatted_docs/privatepypi.pdf
		
Set up devpi server on our laptop
---------------------------------

Install devpi client and web server
The non web server - devpi-server - is  installed as a consequence.

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


