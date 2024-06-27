#### Autor: Natalia Śmieja

# Projekt
Skrypt do przeliczania wartości wybranej waluty do PLN według aktualnego kursu walut.

Źródła danych dla kursu walut:
1) lokalna baza danych (plik: currency_rates.json)
2) API NBP (tabela A, http://api.nbp.pl/)

Skrypt umożliwia (klasa PriceCurrencyConverterToPLN):
- pobranie kursów walut z jednego z dwóch źródeł
- przeliczenie kwoty w wybranej walucie na wartość w PLN i automatyczne zapisanie
  danych do bazy danych w pliku database.json lub database.sqlite (w zależności
  od wybranych ustawień środowiskowych)

Skrypt posiada:
1) łącznik do lokalnej bazy danych SQLite (klasa SQLiteDatabaseConnector)
2) łącznik do lokalnej bazy danych JSON (klasa JsonFileDatabaseConnector)
- obie klasy umożliwiają wykonywanie podstawowych operacji na bazach danych (CRUD)
  celem rejestracji wartości dla przeliczanej waluty
3) łącznik do lokalnej bazy z kursami walut (klasa CurrencyRatesDatabaseConnector)
- klasa umożliwia zarządzanie bazą danych z dziennymi kursami walut


# Uruchomienie projektu
By korzystać ze skryptu należy:
1) pobrać repozytorium z GitHub
2) zainstalować niezbędne biblioteki (plik requirements.txt)
3) skonfigurować zmienne środowiskowe (patrz: plik .env.example)
4) zainicjować klasę poprzez stworzenie jej instancji celem wykorzystania metod danej klasy


## Wymagane
Python 3.10

## Dalsze możliwe ulepszanie kodu

- do zasatnowiania, czy podczas zapisywania nowego rekordu do bazy danych nie dać możliwości zapisania danych w postaci odpowiedniego słownika (obecnie przyjmowane są jedynie dane w postaci instancji klasy ConvertedPricePLN) - mowa o metodach save() w json.py, sqlite.py

- do zastanowienia, ujednolicenie by klasa ConvertedPricePLN (z atrybutami: "currency", "currency_rate", "currency_rate_fetch_date", "price_in_pln", "price_in_source_currency") miała takie same nazwy atrybutów jak dane zapisywane w bazie danych ["currency", "rate", "price_in_pln", "date"] - wówczas rozpaowanie klasy ConvertedPricePLN do bazy danych z modelem CurrencyData byłoby znacznie łatwiejsze

- krok do wdrożenia: zamienić metody operujące na bazach danych na funkcje asynchroniczne (doczytać jak to działa na plikach bazodanowych i jak działa biblioteka asyncio), przjeść na asynchroniczne pobieranie danych z API NBP

- klasa ConvertedPricePLN w pliku currency_converter.py - do rozważenia czy nie zmianić
  atrybutu price_in_pln: float na metodę obliczającą ten atrybut na podstawie pozostałych danych,
  albo dodać walidację:
  def _validate_price_in_pln(self):
        if not self.price_in_pln == round(self.price_in_source_currency * self.currency_rate, 2):
            raise ValueError("Computed price_in_pln does not match expected value.")