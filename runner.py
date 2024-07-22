from dataclasses import dataclass
from typing import List, Dict, Tuple
from copy import deepcopy

# constraints are global but could be added at the account level

@dataclass
class Account:
	id: str
	positions: Dict[str, float]
	cash: Dict[str, float]
	metrics: Dict[str, float]
	prices: Dict[str, float] # added to record last trade price


@dataclass
class Trade:
	side: str
	security_name: str
	security_type: str
	currency: str
	quantity: float
	price: float
	accrued_interest: float


def model_trade(account: Account, trade: Trade):
	account.positions[trade.security_name] = account.positions.get(trade.security_name, 0) + trade.quantity
	trade_value = trade.quantity * trade.price + trade.accrued_interest

	if trade.side == 'buy':
		account.cash[trade.currency] = account.cash.get(trade.currency, 0) - trade_value
	else:
		account.cash[trade.currency] = account.cash.get(trade.currency, 0) + trade_value

	# have to expand to record latest price in order to calc total value
	account.prices[trade.security_name] = trade.price


def metric_summ(account: Account, metrics: str) -> float:
	return sum(calc_metric(account, metric) * weight for metric, weight in account.metrics.items())


def calc_metric(account: Account, metric_name: str) -> float:
	if metric_name == 'total_value':
		return sum(pos * 100 for pos in account.positions.values()) + sum(account.cash.values())

	elif metric_name == 'position_count':
		return len(account.positions)

	elif metric_name == 'cash_percentage':
		total_value = sum(pos * 100 for pos in account.positions.values()) + sum(account.cash.values())
		return (sum(account.cash.values()) / total_value) * 100 if total_value else 0

	return 0


def prime_allocator(trades: List[Trade],
	accounts: Dict[str, Account], constraints: Dict[str, float]):
	_accounts = []
	list.sort(trades, key=lambda t: abs(t.quantity * t.price), reverse=True)
	for trade in trades:
		print('for trade: ', trade)
		for account_id, account in accounts.items():
			_account = deepcopy(account)
			model_trade(_account, trade)
			print(metric_summ(_account, account.metrics))


		
trades = [
	Trade('buy', 'AAPL', 'corporate', 'USD', 100, 150, 0),
	Trade('sell', 'GOOGL', 'corporate', 'USD', 50, 2000, 0)
]


accounts = {
	'Account1': Account(
		'Account1',
		{'AAPL': 1000},
		{'USD': 1000000},
		{'total_value': 1, 'position_count': -0.1, 'cash_percentage': -0.05},
		{'AAPL': 150}
	),
	'Account2': Account(
		'Account2',
		{'GOOGL': 500},
		{'USD': 2000000},
		{'total_value': 1, 'position_count': -0.1, 'cash_percentage': -0.05},
		{'GOOGL': 150}
	)
}

constraints = {
	'total_value': (500000, 'greater_than_or_equal'), 
	'cash_percentage': (10, 'greater_than_or_equal')
}

prime_allocator(trades, accounts, constraints)

	
