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

@dataclass
class Trade:
	side: str
	security_name: str
	security_type: str
	currency: str
	quantity: float
	price: float
	accrued_interest: float

def prime_allocator(trades: List[Trade],
	accounts: Dict[str, Account], metrics: Dict[str, float], constraints: Dict[str, float]):
	list.sort(trades, key=lambda t: abs(t.quantity * t.price), reverse=True)
	for trade in trades:
		print(trade)

trades = [
    Trade('buy', 'AAPL', 'corporate', 'USD', 100, 150, 0),
    Trade('sell', 'GOOGL', 'corporate', 'USD', 50, 2000, 0)
]

accounts = {
    'Account1': Account('Account1', {'AAPL': 1000}, {'USD': 1000000}, {'total_value': 1, 'position_count': -0.1, 'cash_percentage': -0.05}),
    'Account2': Account('Account2', {'GOOGL': 500}, {'USD': 2000000}, {'total_value': 1, 'position_count': -0.1, 'cash_percentage': -0.05})
}

metrics = {'total_value': 1, 'position_count': -0.1, 'cash_percentage': -0.05}

constraints = {
	'total_value': (500000, 'greater_than_or_equal'), 
	'cash_percentage': (10, 'greater_than_or_equal')
}

prime_allocator(trades, accounts, metrics, constraints)
	
