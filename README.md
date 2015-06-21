Full Stack Nanodegree Project 3
===============================

To run:
- clone this repository to your machine
- start up vagrant using `vagrant up`
- connect to the vagrant vm using `vagrant ssh`
- go to the catalog directory using `cd /vagrant/catalog`
- setup database using `python database_setup.py`
- prepopulate database using `python prepopulate.py`
- run the project using `python project.py`
- go to `localhost:5000/genres` in your browser

Available API endpoints:
- `/genres/json` to get all the movies for all genres
- `/genres/<genre_id>/json` to get all the movies for a given genre_id
