Installation
============


Virtual/Conda Environment using ``Pip``
***************************************

After downloading the model repo, navigate to the ``omics-utils`` folder and install the package with:
::

    pip install -e .



Docker Container 
****************

The repo contains a Docker configuration, which can be utilized to develop within. An exemplary setup:

    * Install ``VSCode``, including the ``Devcontainer`` extension, and ``Docker Desktop``
    * Clone the repo and open it in ``VSCode``
    * In the right-hand, lower corner, a message will appear: 

        .. image:: Bild_Devcontainer_Msg1.png
            :width: 400
            :alt: A Devcontainer message.

        Click 'Reopen in Container'.
    * Wait for the container building to finish. Progress can be surveilled in the ``VSCode`` "Terminal". 	
