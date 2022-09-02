"""바이낸스 거래소의 실시간 거래 데이터를 제공하는 DataProvider 클래스"""

import requests
from datetime import datetime
from .data_provider import DataProvider
from .log_manager import LogManager
"""바이낸스 거래소의 실시간 거래 데이터를 제공하는 DataProvider 클래스"""

class BinanceDataProvider(DataProvider):
    """
    바이낸스 거래소의 실시간 거래 데이터를 제공하는 클래스

    바이낸스의 open api를 사용. 별도의 가입, 인증, token 없이 사용 가능
    https://docs.upbit.com/reference#%EC%8B%9C%EC%84%B8-%EC%BA%94%EB%93%A4-%EC%A1%B0%ED%9A%8C
    """

    URL = "https://api.binance.com/api/v3/klines"
    AVAILABLE_CURRENCY = {"BTCUSDT": "BTCUSDT", "ETHUSDT": "ETHUSDT", "DOGE": "DOGEUSDT", "XRPUSDT": "XRPUSDT"}

    def __init__(self, currency="BTCUSDT"):
        if currency not in self.AVAILABLE_CURRENCY:
            raise UserWarning(f"not supported currency: {currency}")

        self.logger = LogManager.get_logger(__class__.__name__)
        self.query_string = {"symbol": self.AVAILABLE_CURRENCY[currency], "interval": "1m", "limit": 1}
        self.market = currency

    def get_info(self):
        """실시간 거래 정보 전달한다

        Returns: 거래 정보 딕셔너리
        {
            "market": 거래 시장 종류 BTC
            "date_time": 정보의 기준 시간
            "opening_price": 시작 거래 가격
            "high_price": 최고 거래 가격
            "low_price": 최저 거래 가격
            "closing_price": 마지막 거래 가격
            "acc_price": 단위 시간내 누적 거래 금액
            "acc_volume": 단위 시간내 누적 거래 양
        }
        """
        data = self.__get_data_from_server()
        return self.__create_candle_info(data[0])

    def __create_candle_info(self, data):
        try:
            return {
                "market": self.market,
                "date_time": datetime.fromtimestamp(int(data[0]/1000)).isoformat(),
                "opening_price": float(data[1]),
                "high_price": float(data[2]),
                "low_price": float(data[3]),
                "closing_price": float(data[4]),
                "acc_price": float(0.0),
                "acc_volume": float(data[5]),
            }
        except KeyError as err:
            self.logger.warning(f"invalid data for candle info: {err}")
            return None

    def __get_data_from_server(self):
        try:
            response = requests.get(self.URL, params=self.query_string)
            response.raise_for_status()
            return response.json()
        except ValueError as error:
            self.logger.error(f"Invalid data from server: {error}")
            raise UserWarning("Fail get data from sever") from error
        except requests.exceptions.HTTPError as error:
            self.logger.error(error)
            raise UserWarning("Fail get data from sever") from error
        except requests.exceptions.RequestException as error:
            self.logger.error(error)
            raise UserWarning("Fail get data from sever") from error
