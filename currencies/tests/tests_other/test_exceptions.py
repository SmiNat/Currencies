from currencies.exceptions import (
    CurrencyDataIntegrityError,
    CurrencyNotFoundError,
    DatabaseError,
)


def test_CurrencyDataIntegrityError():
    exp_message = (
        "IntegrityError: UNIQUE constraint failed: a record with the "
        "same parameters already exists in the database."
    )

    try:
        raise CurrencyDataIntegrityError()
    except CurrencyDataIntegrityError as exc:
        assert str(exc) == exp_message
        assert isinstance(exc, Exception)


def test_CurrencyNotFoundError_empty():
    exp_message = "Currency not found"

    try:
        raise CurrencyNotFoundError()
    except CurrencyNotFoundError as exc:
        assert exp_message in str(exc)
        assert isinstance(exc, Exception)


def test_CurrencyNotFoundError_with_message():
    exp_message = "Some special message"

    try:
        raise CurrencyNotFoundError(exp_message)
    except CurrencyNotFoundError as exc:
        assert exp_message in str(exc)
        assert isinstance(exc, Exception)


def test_CurrencyNotFoundError_with_currency():
    currency = "pln"
    exp_message = "'PLN' currency not found"

    try:
        raise CurrencyNotFoundError(currency=currency)
    except CurrencyNotFoundError as exc:
        assert exp_message in str(exc)
        assert isinstance(exc, Exception)


def test_CurrencyNotFoundError_with_available_currencies():
    currency = "pln"
    available_currencies = ["USD", "EUR"]
    exp_message = "'PLN' currency not found. Available currencies: ['USD', 'EUR']"

    try:
        raise CurrencyNotFoundError(
            currency=currency, available_currencies=available_currencies
        )
    except CurrencyNotFoundError as exc:
        assert exp_message in str(exc)
        assert isinstance(exc, Exception)


def test_DatabaseError():
    exp_message = (
        "Unable to set proper connector to the database. "
        "Check the environment settings."
    )

    try:
        raise DatabaseError()
    except DatabaseError as exc:
        assert str(exc) == exp_message
        assert isinstance(exc, Exception)
