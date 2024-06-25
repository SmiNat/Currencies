import logging

from .currency_converter import PriceCurrencyConverterToPLN

logger = logging.getLogger("currencies")


try:
    converter = PriceCurrencyConverterToPLN()

    # Example usage: Convert EUR 100 to PLN using NBP API
    data = converter.convert_to_pln("chf", 400, "api nbp")
    logger.info(f"Converted data: {data}")

    # Example usage: Fetching currency data from local database
    data = converter.fetch_single_currency_from_local_database("gbpd")
    logger.info(f"Data: {data}")

    # Example usage: Fetching currency data from the NBP API
    data = converter.fetch_single_currency_from_nbp("eur")
    logger.info(f"Data: {data}")

    logger.debug("Job done!")

except Exception as err:
    logger.error(f"An error occurred: {err}")
