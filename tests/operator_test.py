import unittest
from smtm import Operator
from unittest.mock import *
import requests
import threading


class OperatorTests(unittest.TestCase):
    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_initialize_keep_object_correctly(self):
        operator = Operator()
        operator.initialize("apple", "kiwi", "mango", "banana", "orange", "grape")
        self.assertEqual(operator.http, "apple")
        self.assertEqual(operator.threading, "kiwi")
        self.assertEqual(operator.data_provider, "mango")
        self.assertEqual(operator.strategy, "banana")
        self.assertEqual(operator.trader, "orange")
        self.assertEqual(operator.analyzer, "grape")

    def test_setup_set_interval_correctly(self):
        operator = Operator()
        operator.setup(10)

        self.assertEqual(operator.interval, 10)

        operator.setup(39)
        self.assertEqual(operator.interval, 39)

    def test_start_return_false_without_initialization(self):
        operator = Operator()
        self.assertEqual(operator.start(), False)

    def test_start_should_call_worker_start_and_post_task(self):
        operator = Operator()
        operator.initialize("apple", "kiwi", "mango", "banana", "orange", "grape")
        operator.worker = MagicMock()
        operator.start()
        operator.worker.start.assert_called_once()
        operator.worker.post_task.assert_called_once_with(ANY)
        called_task = operator.worker.post_task.call_args[0][0]
        self.assertEqual(called_task["runnable"], operator._excute_trading)

    def test_excute_trading_should_call_get_info_and_set_timer(self):
        timer_mock = Mock()
        threading_mock = Mock()
        threading_mock.Timer = MagicMock(return_value=timer_mock)

        operator = Operator()
        dp_mock = Mock()
        dp_mock.initialize = MagicMock(return_value="")
        dp_mock.get_info = MagicMock(return_value="mango")

        dummy_request = {"id": "mango", "type": "orange", "price": 500, "amount": 10}
        strategy_mock = Mock()
        strategy_mock.update_trading_info = MagicMock(return_value="orange")
        strategy_mock.get_request = MagicMock(return_value=dummy_request)
        analyzer_mock = Mock()
        analyzer_mock.put_trading_info = MagicMock()
        trader_mock = Mock()
        trader_mock.send_request = MagicMock()
        operator.initialize(
            "apple", threading_mock, dp_mock, strategy_mock, trader_mock, analyzer_mock
        )
        operator.setup(27)
        operator._excute_trading(None)

        threading_mock.Timer.assert_called_once_with(27, ANY)
        timer_mock.start.assert_called_once()
        dp_mock.get_info.assert_called_once()
        analyzer_mock.put_trading_info.assert_called_once_with("mango")

    def test_excute_trading_should_call_trader_send_request_and_strategy_update_result(self):
        timer_mock = Mock()
        threading_mock = Mock()
        threading_mock.Timer = MagicMock(return_value=timer_mock)
        analyzer_mock = Mock()
        analyzer_mock.put_request = MagicMock()
        analyzer_mock.put_result = MagicMock()
        operator = Operator()
        dp_mock = Mock()
        dp_mock.initialize = MagicMock(return_value="")
        dp_mock.get_info = MagicMock(return_value="mango")

        dummy_request = {"id": "mango", "type": "orange", "price": 500, "amount": 10}
        strategy_mock = Mock()
        strategy_mock.update_trading_info = MagicMock(return_value="orange")
        strategy_mock.update_result = MagicMock()
        strategy_mock.get_request = MagicMock(return_value=dummy_request)
        trader_mock = Mock()
        trader_mock.send_request = MagicMock()
        operator.initialize(
            "apple", threading_mock, dp_mock, strategy_mock, trader_mock, analyzer_mock
        )
        operator.setup(27)
        operator._excute_trading(None)
        analyzer_mock.put_request.assert_called_once_with(dummy_request)
        strategy_mock.update_trading_info.assert_called_once_with(ANY)
        trader_mock.send_request.assert_called_once_with(ANY, ANY)
        trader_mock.send_request.call_args[0][1]("mango")
        strategy_mock.update_result.assert_called_once_with("mango")
        analyzer_mock.put_result.assert_called_once_with("mango")

    def test_excute_trading_should_NOT_call_trader_send_request_when_request_is_invalid(self):
        timer_mock = Mock()
        threading_mock = Mock()
        threading_mock.Timer = MagicMock(return_value=timer_mock)
        analyzer_mock = Mock()
        analyzer_mock.put_request = MagicMock()
        analyzer_mock.put_result = MagicMock()
        operator = Operator()
        dp_mock = Mock()
        dp_mock.initialize = MagicMock(return_value="")
        dp_mock.get_info = MagicMock(return_value="mango")

        dummy_request = {"id": "mango", "type": "orange", "price": 0, "amount": 10}
        strategy_mock = Mock()
        strategy_mock.update_trading_info = MagicMock(return_value="orange")
        strategy_mock.get_request = MagicMock(return_value=dummy_request)
        trader_mock = Mock()
        trader_mock.send_request = MagicMock()
        operator.initialize(
            "apple", threading_mock, dp_mock, strategy_mock, trader_mock, analyzer_mock
        )
        operator.setup(27)
        operator._excute_trading(None)

        analyzer_mock.put_request.assert_not_called()
        trader_mock.send_request.assert_not_called()
        analyzer_mock.put_result.assert_not_called()

    def test_excute_trading_should_NOT_call_trader_send_request_when_request_is_None(self):
        timer_mock = Mock()
        threading_mock = Mock()
        threading_mock.Timer = MagicMock(return_value=timer_mock)
        analyzer_mock = Mock()
        analyzer_mock.put_request = MagicMock()
        analyzer_mock.put_result = MagicMock()
        operator = Operator()
        dp_mock = Mock()
        dp_mock.initialize = MagicMock(return_value="")
        dp_mock.get_info = MagicMock(return_value="mango")
        strategy_mock = Mock()
        strategy_mock.update_trading_info = MagicMock(return_value="orange")
        strategy_mock.get_request = MagicMock(return_value=None)
        trader_mock = Mock()
        trader_mock.send_request = MagicMock()
        operator.initialize(
            "apple", threading_mock, dp_mock, strategy_mock, trader_mock, analyzer_mock
        )
        operator.setup(27)
        operator._excute_trading(None)

        analyzer_mock.put_request.assert_not_called()
        trader_mock.send_request.assert_not_called()
        analyzer_mock.put_result.assert_not_called()

    def test_stop_should_cancel_timer_and_set_false_is_timer_running(self):
        operator = Operator()
        operator.timer = MagicMock()
        operator.is_timer_running = True
        operator.stop()
        self.assertFalse(operator.is_timer_running)
        operator.timer.cancel.assert_called_once()

    def test_stop_should_set_is_terminating_True_and_is_timer_running_False(self):
        operator = Operator()
        operator.is_timer_running = True
        operator.stop()
        self.assertFalse(operator.is_timer_running)
        self.assertTrue(operator.is_terminating)

    def test_stop_should_call_worker_stop(self):
        operator = Operator()
        operator.timer = MagicMock()
        operator.worker = MagicMock()
        operator.stop()
        operator.worker.stop.assert_called_once()

    def test_start_timer_should_call_Timer_and_start(self):
        timer_mock = Mock()
        threading_mock = Mock()
        threading_mock.Timer = MagicMock(return_value=timer_mock)

        operator = Operator()
        operator.initialize("apple", threading_mock, "banana", "kiwi", "orange", "mango")

        operator.setup(27)
        operator._start_timer()

        threading_mock.Timer.assert_called_once_with(27, ANY)
        timer_mock.start.assert_called_once()
        timer_callback = threading_mock.Timer.call_args[0][1]
        operator.worker = MagicMock()
        timer_callback()
        operator.worker.post_task.assert_called_once_with(ANY)
        self.assertEqual(
            operator.worker.post_task.call_args[0][0]["runnable"], operator._excute_trading
        )

    def test_start_timer_should_NOT_call_Timer_and_start_when_is_terminating_True(self):
        timer_mock = Mock()
        threading_mock = Mock()
        threading_mock.Timer = MagicMock(return_value=timer_mock)

        operator = Operator()
        operator.initialize("apple", threading_mock, "banana", "kiwi", "orange", "mango")
        operator.is_terminating = True
        operator.setup(27)
        operator._start_timer()

        threading_mock.Timer.assert_not_called()
        timer_mock.start.assert_not_called()

    def test_start_timer_should_set_is_timer_running_true(self):
        timer_mock = Mock()
        threading_mock = Mock()
        threading_mock.Timer = MagicMock(return_value=timer_mock)

        operator = Operator()
        operator.initialize("apple", threading_mock, "banana", "kiwi", "orange", "mango")
        operator._start_timer()
        self.assertEqual(operator.is_timer_running, True)

    def test_get_score_should_call_work_post_task_with_correct_task(self):
        timer_mock = Mock()
        threading_mock = Mock()
        threading_mock.Timer = MagicMock(return_value=timer_mock)

        operator = Operator()
        operator.initialize("apple", threading_mock, "banana", "kiwi", "orange", "mango")
        operator.worker = MagicMock()
        operator.get_score("dummy")
        operator.worker.post_task.assert_called_once_with(ANY)

        operator.analyzer = MagicMock()
        operator.analyzer.get_return_report.return_value = "grape"
        task = {"runnable": MagicMock(), "callback": MagicMock()}
        runnable = operator.worker.post_task.call_args[0][0]["runnable"]
        runnable(task)
        operator.analyzer.get_return_report.assert_called_once()
        task["callback"].assert_called_once_with("grape")
