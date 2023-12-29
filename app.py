from flask import Flask, request, jsonify, render_template
from algorithms import Tahoe, Reno, Cubic, BICTCP

app = Flask(__name__, static_url_path='/static')

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/simulate', methods=['POST'])
def simulate():
    data = request.get_json()
    algorithm_type = data.pop('algorithm', None)
    algorithms = {'Tahoe': Tahoe, 'Reno': Reno, 'Cubic': Cubic, 'BICTCP': BICTCP}
    
    algorithm_class = algorithms.get(algorithm_type)
    if not algorithm_class:
        return jsonify({'error': 'Invalid algorithm type'}), 400

    algorithm = algorithm_class(**data)
    results = algorithm.perform_algorithm()

    return jsonify({
        'simulationResults': results[0],
        'packetLossEvents': results[1],
        'rttVariations': results[2],
        'stateTransitions': results[3],
        'queueLengths': results[4],  # Include queue lengths
        'acks': results[5]  # Include acknowledgments
    })

if __name__ == '__main__':
    app.run(debug=True)
