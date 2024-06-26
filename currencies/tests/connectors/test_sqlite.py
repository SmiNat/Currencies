from currencies.connectors.database.sqlite import SQLiteDatabaseConnector
from currencies.currency_converter import ConvertedPricePLN


def test_init(db_session):
    session = SQLiteDatabaseConnector(db_session)
    assert isinstance(session, SQLiteDatabaseConnector)


def test_get_all_empty_db(db_session):
    session = SQLiteDatabaseConnector(db_session)

    exp_result = []

    result = session.get_all()
    assert result == exp_result


def test_get_all_not_empty_db(db_session):
    session = SQLiteDatabaseConnector(db_session)

    cp1 = ConvertedPricePLN(10, "USD", 4.3, "2024-06-01", 43)
    cp2 = ConvertedPricePLN(10, "EUR", 4.55, "2022-10-10", 45.5)

    session.save(cp1)
    session.save(cp2)

    exp_result = []

    result = session.get_all()
    assert result == exp_result


# import pytest
# from sqlalchemy.exc import SQLAlchemyError
# from currencies.connectors.database.sqlite import SQLiteDatabaseConnector
# from currencies.currency_converter import ConvertedPricePLN


# def test_save_new_currency(db_session):
#     connector = SQLiteDatabaseConnector(session=lambda: db_session)
#     entity = ConvertedPricePLN("USD", 4.2, 25.0, "2024-06-30")

#     entity_id = connector.save(entity)

#     assert entity_id > 0
#     saved_entity = db_session.query(CurrencyData).filter_by(id=entity_id).first()
#     assert saved_entity is not None
#     assert saved_entity.currency == "USD"
#     assert saved_entity.rate == 4.2
#     assert saved_entity.price_in_pln == 25.0
#     assert saved_entity.date.strftime("%Y-%m-%d") == "2024-06-30"


# def test_get_all_currencies(db_session):
#     connector = SQLiteDatabaseConnector(session=lambda: db_session)
#     entity1 = ConvertedPricePLN("USD", 4.2, 25.0, "2024-06-30")
#     entity2 = ConvertedPricePLN("EUR", 4.5, 100.0, "2024-07-01")
#     connector.save(entity1)
#     connector.save(entity2)

#     all_currencies = connector.get_all()

#     assert len(all_currencies) == 2


# def test_get_currency_by_id(db_session):
#     connector = SQLiteDatabaseConnector(session=lambda: db_session)
#     entity = ConvertedPricePLN("USD", 4.2, 25.0, "2024-06-30")

#     entity_id = connector.save(entity)

#     currency_data = connector.get_by_id(entity_id)

#     assert currency_data is not None
#     assert currency_data["currency"] == "USD"


# def test_update_currency(db_session):
#     connector = SQLiteDatabaseConnector(session=lambda: db_session)
#     entity = ConvertedPricePLN("USD", 4.2, 25.0, "2024-06-30")

#     entity_id = connector.save(entity)
#     update_msg = connector.update(entity_id, rate=4.5)

#     assert update_msg == f"Currency with id '{entity_id}' was successfully updated."
#     updated_entity = db_session.query(CurrencyData).filter_by(id=entity_id).first()
#     assert updated_entity.rate == 4.5


# def test_delete_currency(db_session):
#     connector = SQLiteDatabaseConnector(session=lambda: db_session)
#     entity = ConvertedPricePLN("USD", 4.2, 25.0, "2024-06-30")

#     entity_id = connector.save(entity)
#     delete_msg = connector.delete(entity_id)

#     assert delete_msg == f"Currency with id '{entity_id}' deleted from the database."
#     deleted_entity = db_session.query(CurrencyData).filter_by(id=entity_id).first()
#     assert deleted_entity is None


# def test_delete_currency_with_exception(db_session, caplog):
#     connector = SQLiteDatabaseConnector(session=lambda: db_session)
#     entity = ConvertedPricePLN("USD", 4.2, 25.0, "2024-06-30")
#     entity_id = connector.save(entity)

#     with pytest.raises(SQLAlchemyError):
#         with patch.object(db_session, "query", side_effect=SQLAlchemyError("Simulated error")):
#             connector.delete(entity_id)

#     assert any("Error while deleting data from the database" in record.message for record in caplog.records)


# # Additional tests can be added to cover more edge cases, validations, and scenarios
