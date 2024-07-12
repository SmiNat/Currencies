import datetime

import pytest
from sqlalchemy.orm import Session

from currencies.database_config import CurrencyData


def test_validate_date_with_valid_currency_date(db_session: Session):
    db = db_session

    new_record = CurrencyData(
        amount=100,
        currency="JPY",
        currency_rate=0.024,
        currency_date="2022-12-12",
        price_in_pln=2.4,
    )
    db.add(new_record)
    db.commit()

    assert (
        db.query(CurrencyData).filter_by(currency="JPY", currency_rate=0.024).first()
    ) is not None


@pytest.mark.parametrize(
    "date, error_type, error_msg",
    [
        (
            datetime.date(2022, 12, 12),
            TypeError,
            "Invalid data type for date attribute. Required type: string",
        ),
        (
            "12-12-2022",
            ValueError,
            "Invalid date format. Required format: 'YYYY-MM-DD' (e.g. 2020-12-30)",
        ),
    ],
)
def test_validate_date_with_invalid_currency_date(
    db_session: Session,
    date: datetime.date | str,
    error_type: Exception,
    error_msg: str,
):
    db = db_session
    with pytest.raises(error_type) as exc_info:
        new_record = CurrencyData(
            amount=10,
            currency="EUR",
            currency_rate=4.20,
            currency_date=date,
            price_in_pln=42,
        )
        db.add(new_record)
        db.commit()
    assert error_msg in str(exc_info.value)
