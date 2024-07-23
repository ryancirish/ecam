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
	financing_rate: float # added for interest optimization.

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
		return sum(account.positions[pos] * account.prices[pos] for pos in account.positions) + sum(account.cash.values())

	elif metric_name == 'position_count':
		return len(account.positions)

	elif metric_name == 'cash_percentage':
		total_value = calc_metric(account, 'total_value')
		return (sum(account.cash.values()) / total_value) * 100 if total_value else 0

	elif metric_name == 'leverage':
		total_asset_value = calc_metric(account, 'total_value')
		total_liabilities = sum(
			max(0, -quantity * account.prices[pos] * account.financing_rate)
			for pos, quantity in account.positions.items())
		return total_liabilities / total_asset_value if total_asset_value else 0

	elif metric_name == 'financing_cost':
		return sum(
			max(0, quantity) * account.prices[pos] * account.financing_rate
			for pos, quantity in account.positions.items())

	return 0


def calc_all_metrics(account: Account) -> Dict[str, float]:
	return {
		'total_value': calc_metric(account, 'total_value'),
		'position_count': calc_metric(account, 'position_count'),
		'cash_percentage': calc_metric(account, 'cash_percentage'),
		'leverage': calc_metric(account, 'leverage'),
		'financing_cost': calc_metric(account, 'financing_cost')
	} 

def constraints_satisfied(account: Account, constraints: Dict[str, Tuple[float, str]]) -> bool:
	for metric_name, (limit, gator) in constraints.items():
		M = calc_metric(account, metric_name)
		if gator == 'less_than_or_equal' and M > limit:
			return False
		if gator == 'greater_than_or_equal' and M < limit:
			return False

	return True


def prime_allocator(
	trades: List[Trade],
	accounts: Dict[str, Account], 
	constraints: Dict[str, float]):
	
	allocation_log = []
	list.sort(trades, key=lambda t: abs(t.quantity * t.price), reverse=True)

	for trade in trades:
		# print('for trade: ', trade)
		alloc_id, _M = None, float('-inf')

		for account_id, account in accounts.items():
			_account = deepcopy(account)
			model_trade(_account, trade)

			# ensure that constraints are met before bothering with downstream calc
			# contract must be fufilled
			if constraints_satisfied(_account, constraints):
				M = metric_summ(_account, account.metrics)
				# print('Σ: ', M) # optimize for larger score currently, need to expand scenario
				if M > _M:
					_M = M
					alloc_id = account_id
		# post termination clause
			# allocate the modeled trade scenarios to the greedy-optimal account
		if alloc_id is not None:
			model_trade(accounts[alloc_id], trade)
			allocation_log.append((trade, alloc_id))
		else:
			raise ValueError(f"Unable to allocate: {trade}")

	final_metrics = {account_id: calc_all_metrics(account) for account_id, account in accounts.items()}
	return allocation_log, accounts, final_metrics

		
trades = [
	Trade('buy', 'AAPL', 'corporate', 'USD', 100, 150, 0),
	Trade('sell', 'GOOG', 'corporate', 'USD', 50, 2000, 0)
]


accounts = {
	'Account1': Account(
		'Account1',
		{'AAPL': 1000},
		{'USD': 1000000},
		{
			'total_value': 1.0,
			'position_count': -0.1,
			'cash_percentage': 0.5,
			'leverage': -0.5,
			'financing_cost': -1.0
		},
		{'AAPL': 150},
		0.056
	),
	'Account2': Account(
		'Account2',
		{'GOOG': 500},
		{'USD': 2000000},
		{
			'total_value': 1.0,
			'position_count': -0.1,
			'cash_percentage': 0.5,
			'leverage': -0.5,
			'financing_cost': -1.0
		},
		{'GOOG': 150},
		0.032
	)
}

constraints = {
	'total_value': (500000, 'greater_than_or_equal'),
	'leverage': (2, 'less_than_or_equal'),
	'cash_percentage': (10, 'greater_than_or_equal')
}

allocation_log, updated, metrics = prime_allocator(trades, accounts, constraints)


print("Trade Allocations:")
for trade, alloc_id in allocation_log:
    print(f"Allocated {trade.side} {trade.quantity} {trade.security_name} to {alloc_id}")

print("\nFinal Account States and Metrics:")
for account_id, account in updated.items():
    print(f"{account_id}:")
    print(f"  Positions: {account.positions}")
    print(f"  Cash: {account.cash}")
    print(f"  Metrics: {metrics[account_id]}")

	
