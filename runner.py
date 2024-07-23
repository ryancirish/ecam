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

	elif metric_name == 'gov_bond_percentage':
		gov_bond_value = sum(quantity * account.prices[pos] for pos, quantity in account.positions.items() if 'GOV' in pos)
		total_value = calc_metric(account, 'total_value')
		return (gov_bond_value / total_value) * 100 if total_value else 0

	elif metric_name == 'currency_exposure':
		# percent of non usd
		usd_value = account.cash.get('USD', 0) + sum(quantity * account.prices[pos] for pos, quantity in account.positions.items() if not pos.endswith('CAD'))
		total_value = calc_metric(account, 'total_value')
		return ((total_value - usd_value) / total_value) * 100 if total_value else 0

	return 0


def calc_all_metrics(account: Account) -> Dict[str, float]:
	return {
		'total_value': calc_metric(account, 'total_value'),
		'position_count': calc_metric(account, 'position_count'),
		'cash_percentage': calc_metric(account, 'cash_percentage'),
		'leverage': calc_metric(account, 'leverage'),
		'financing_cost': calc_metric(account, 'financing_cost'),
		'gov_bond_percentage': calc_metric(account, 'gov_bond_percentage'),
		'currency_exposure': calc_metric(account, 'currency_exposure')
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
	Trade('sell', 'GOOG', 'corporate', 'USD', 50, 2000, 0),
	Trade('buy', 'US_GOV_10Y', 'government', 'USD', 100000, 98.5, 500),
	Trade('sell', 'RY.TO', 'corporate', 'CAD', 1000, 100, 0),
	Trade('buy', 'CA_GOV_5Y', 'government', 'CAD', 150000, 99, 300)
]


accounts = {
	'Account1': Account(
		'Account1',
		{'AAPL': 1000, 'US_GOV_5Y': 100000, 'RY.TO': 2000},
		{'USD': 2000000, 'CAD': 15000000},
		{
			'total_value': 1.0,
			'position_count': -0.1,
			'cash_percentage': 0.5,
			'leverage': -0.5,
			'financing_cost': -1.0,
			'gov_bond_percentage': 0.3,
			'currency_exposure': -0.2
		},
		{'AAPL': 150, 'US_GOV_5Y': 97.5, 'RY.TO': 95, 'US_GOV_10Y': 98.5},
		0.056
	),
	'Account2': Account(
		'Account2',
		{'GOOG': 500, 'CA_GOV_10Y': 200000, 'TD.TO': 1500},
		{'USD': 2000000, 'CAD': 16000000},
		{
			'total_value': 1.0,
			'position_count': -0.1,
			'cash_percentage': 0.5,
			'leverage': -0.5,
			'financing_cost': -1.0,
			'gov_bond_percentage': 0.3,
			'currency_exposure': 0.2
		},
		{'GOOG': 2000, 'CA_GOV_10Y': 98, 'TD.TO': 80, 'CA_GOV_5Y': 99},
		0.032
	)
}

constraints = {
	'total_value': (100000, 'greater_than_or_equal'),
	'leverage': (3, 'less_than_or_equal'),
	'cash_percentage': (5, 'greater_than_or_equal'),
	'gov_bond_percentage': (15, 'greater_than_or_equal'),
	'currency_exposure': (60, 'less_than_or_equal')
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

	
