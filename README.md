# Item Catalog Project
This is my a simple Item Catalog Application in which a list of items within a variety of categories as well a user registration and authentication system are provided. Registered users have the ability to post, edit and delete their own items.

## Outside Dependencies
- This RESTful web application uses the Python Flask framework.
- I implemented [Google's](https://classroom.udacity.com/nanodegrees/nd004/parts/4dcefa2a-fb54-4909-9708-9ef2839e5340/modules/5dbcf44d-760d-49d4-9055-b6a0a48e5454/lessons/3967218625/concepts/39518891870923) and [Facebook's](https://classroom.udacity.com/nanodegrees/nd004/parts/4dcefa2a-fb54-4909-9708-9ef2839e5340/modules/5dbcf44d-760d-49d4-9055-b6a0a48e5454/lessons/3951228603/concepts/39497787730923) OAuth APIs that were taught in class using the notes that I've kept.
- I used the SQLAlchemy ORM (Object Relational Mapper) to send off requests written in Python (the code is transformed by the ORM into SQL) to the database, and then get the results from the SQL statements and use them as objects from within my Python code.
- I also used the jQuery library to make ajax request to the third party servers.
- Favicon is from [iconfinder](https://www.iconfinder.com/icons/1519787/catalog_color_guide_colorful_office_school_icon).


## Run the program
1. You need to have installed:
  - A version of Python (at least 2.7 and above).
  - The [Vagrant](https://www.vagrantup.com/) tool for building and managing virtual machine environments.
  - Linux on the [VirtualBox](https://www.virtualbox.org/) Virtual Machine.
  - Download and place this [Vagrantfile](https://github.com/udacity/fullstack-nanodegree-vm/tree/master/vagrant) in your vagrant directory.
2. Run the Virtual Machine:
  - Launch the Vagrant Virtual Machine inside your shared Vagrant sub-directory by running: `$ vagrant up`
  - Then ssh using this command: `$ vagrant ssh`.
3. Download and place the project files into a folder in your shared Vagrant sub-directory and navigate to that folder.
4. Use the PostgreSQL command line program to create a database named itemcatalog. First run `$ psql` to open up the command line program and then `$ CREATE DATABASE itemcatalog;` to create the database that the application will connect to. After that exit psql by running `\q`.
5. Setup the app's database by running `$ python database_setup.py` from your vagrant sub-directory using Python.
6. Run the app's script from your vagrant sub-directory using Python: `$ python main.py`.
7. Open up your browser, navigate to _http://localhost:5000/_ and *create a user* using the app's login methods.
8. After creating a user fill the database with the necessary data(categories and category items) by closing the running application in your terminal and then running `$ python fill_database.py`.
9. Restart the application with `$ python main.py`. Everything is set.

## API Endpoint instructions
- To get all user data use the URL: `/users/JSON`
- To get specific user data (If the username contains spaces use the URL encoding for space, which is %20) use the URL: `/users/<user_name>/JSON`.
- To get all category data use the URL: `/categories/JSON`.
- To get a specific category use the URL: `/categories/<category_name>/JSON`.
- To get all item data use the URL: `/items/JSON`
- To get specific item data use the URL: `/items/<item_name>/<item_id>/JSON`.
