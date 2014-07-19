SVN helper: tool to help with SVN routain
=========================================


Installation
------------

* Use pip and `vurtualev/virtualenvwrapper <http://docs.python-guide.org/en/latest/dev/virtualenvs/>`_
* install requirements.txt
* just run helper.py

Example
-------

.. code-block:: bash

    echo 'Checkout revision from server'
    $ ./helper.py --cfg=helper.cfg co
    Working copy path: mytestproj


    echo 'Clean extra files, rever changes switch to revision'
    $ touch mytestproj/extra-file
    $ mkdir mytestproj/extra-folder
    $ echo 'foo' >> mytestproj/README

    $ ./helper.py clean
    Working copy path: mytestproj
    The following untracked working tree files would be removed:
        * mytestproj/extra-file
        * mytestproj/extra-folder
    The following untracked working tree files would be rolled back:
        * mytestproj/README
    
    Continue (y/n)y

 
Requirements
------------

* CentOS release 5.10 (Final)
* svn, version 1.6.11 (r934486)
* Python 2.6.8
