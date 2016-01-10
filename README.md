# Library App
You need [Virtualbox](https://www.virtualbox.org/wiki/Downloads) and [Vagrant](https://www.vagrantup.com/downloads) to run the project!

## Run the virtual machine!

Using the terminal, change directory to library, then type **vagrant up** to launch your virtual machine.

## Running the Library App
Once it is up and running, type **vagrant ssh**. This will log your terminal into the virtual machine, and you'll get a Linux shell prompt. When you want to log out, type **exit** at the shell prompt.  To turn the virtual machine off (without deleting anything), type **vagrant halt**. If you do this, you'll need to run **vagrant up** again before you can log into it.


Now that you have Vagrant up and running type **vagrant ssh** to log into your VM.  change to the /vagrant directory by typing **cd /vagrant**. This will take you to the shared folder between your virtual machine and host machine.

Now type **python database_setup.py** to initialize the database.

Type **python project.py** to run the Flask web server. In your browser visit **http://localhost:5000** to view the library app.
