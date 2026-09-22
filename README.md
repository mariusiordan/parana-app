# Parana Online Shopping Application

A command line application for the Parana Electronics Store, written for
Introduction to Databases (Assessment AE2).

## Requirements

- Python 3.11 or later (developed and tested on Python 3.14.7)
- No external libraries are needed. The application uses only the standard
  library modules `sqlite3` and `os`.

## Files

 File - Description 

 `main.py`  The application 
 `parana.db`  The SQLite database, including the two review tables added in Part 1 

## Running the application

From the folder containing both files:
python3 main.py


The application prompts for a shopper id, use an id that exists in the
`shoppers` table, for example `10010`, which has several previous orders, and
if the id is not found, an error message is displayed and the program exits.