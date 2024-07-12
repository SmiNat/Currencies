# Project

Script to convert the value of the selected currency to PLN according to the available
exchange rate.

Data sources for exchange rates:

1) local database (file: currency_rates.json)
2) NBP API (table A, http://api.nbp.pl/)

The script allows (PriceCurrencyConverterToPLN class):

- downloading currency rates from one of two sources (mentioned above)
- conversion of the amount in the selected currency into PLN and automatic saving
  data to the database in the database.json or database.sqlite file (depending on
  on selected environmental settings - see: config.py file)

The script operates on:

1) connector to local SQLite database (SQLiteDatabaseConnector class)
2) connector to local JSON database (JsonFileDatabaseConnector class)
- both classes enable basic database operations (CRUD) to record the value for
  the currency being converted
3) connector to the local database with currency rates (CurrencyRatesDatabaseConnector class)
- the class allows you to manage a database with daily currency rates


# Launch the project

To use the script you need to:

1) download the repository from GitHub
2) install the necessary libraries (requirements.txt file)
3) configure environment variables (see .env.example file)
4) initialize a class by creating an instance of it to use the methods of a given class


## Required
Python 3.10
