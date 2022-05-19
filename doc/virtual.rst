python virtual environment setup
================================

To have a good control over pre-requisite library modules
for our software, we run in a python virtual environment.

That means that whenever you want to use or maintain the software
you must first invoke that virtual environment like this:

::
   
    source ${HOME}/projectname_venv/bin/activate

Below we describe how to set up a project virtual environment.

Replace '**projectname**' with the name of your project below.

First we create a virtual  environment and make it our current one..


Install non pip packages we are going to rely on.

.. code-block:: bash
		
    snap install rst2pdf
    sudo apt install python3.8-venv          # on ubuntu need this for "python3.8 -m venv projectname_venv " to work


.. code-block:: bash
    
    cd ${HOME}
    python3.8 -m venv projectname_venv
    source ${HOME}/projectname_venv/bin/activate

If we already have a correct requirements file for the project.
We can just use that to get everything.

.. code-block:: bash

    pip install -r ${HOME}/repos/projectname/requirements.txt

But the first time we need to install all the parts we need.

We install the bare essentials.

.. code-block:: bash
    
    python -m pip install -U pip
    pip install wheel
    pip install setuptools
    pip install twine
    pip install flit


Our revision control tool of choice is git.

Flit works nicely with it, but it is strict about files being properly
committed.  We need to ignore all any extraeneous files.  I find this
a good starting point for ignoring files:

.gitignore contents:

::

   *~
   requirements-*.txt
   dist/*
   pdf_docs/*.pdf
   
