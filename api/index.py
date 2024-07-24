# from test of formula
from api.helper import Account, Trade
from api.helper import model_trade, metric_summ, calc_metric, calc_all_metrics, constraints_satisfied, prime_allocator

from flask import Flask, request, jsonify
from dataclasses import dataclass, asdict
from typing import List, Dict, Tuple
from copy import deepcopy

app = Flask(__name__)

@app.get("/")
def healthcheck():
	return {"msg": "hello world"}, 200

@app.route('/allocate_trades', methods=['POST'])
def allocate_trades():
	data = request.json
    
	try:
		trades = [Trade(**trade) for trade in data['trades']]
		accounts = {acc_id: Account(**acc) for acc_id, acc in data['accounts'].items()}
		constraints = data['constraints']
		
		allocations, updated_accounts, final_metrics = prime_allocator(trades, accounts, constraints)
		
		# Convert dataclasses to dictionaries for JSON serialization
		allocations_json = [(asdict(trade), account_id) for trade, account_id in allocations]
		updated_accounts_json = {acc_id: asdict(account) for acc_id, account in updated_accounts.items()}

		return jsonify({
			'allocations': allocations_json,
			'final_account_states': updated_accounts_json,
			'final_metrics': final_metrics
		})
	
	except Exception as e:
		return jsonify({'error': str(e)}), 400


if __name__ == '__main__':
	app.run(port=1337, debug=True)


# minimum
	# post route for trades, accounts, constraints in prime allocator
	# some kind of sqlite for in memory
		# can initalize the first testset then add new trades

#extra
	# route for adding trades via json
	# route for adding trades via csv
	# test suite

# need testset


