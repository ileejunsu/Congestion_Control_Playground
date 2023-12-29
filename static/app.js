const chartColors = ['rgb(75, 192, 192)', 'rgb(255, 99, 132)', 'rgb(54, 162, 235)'];

document.addEventListener('DOMContentLoaded', function() {
    initializeRangeInputs();
    initializeCharts();

    const form = document.getElementById('parameters-form');
    form.addEventListener('submit', function(event) {
        event.preventDefault();
        const formData = new FormData(form);
        const params = collectFormData(formData);
        submitFormData(params)
            .then(data => {
                if (data && data.simulationResults) {
                    updateCharts(data);
                } else {
                    console.error('Invalid data format:', data);
                }
            })
            .catch(handleError);
    });
});

function initializeRangeInputs() {
    const rangeInputs = document.querySelectorAll('input[type="range"]');
    rangeInputs.forEach(input => {
        const valueDisplay = document.getElementById(input.id + '-value');
        valueDisplay.textContent = input.value;
        input.addEventListener('input', () => {
            valueDisplay.textContent = input.value;
        });
    });
}

function collectFormData(formData) {
    return {
        algorithm: formData.get('algorithm'),
        cwnd: parseInt(formData.get('cwnd'), 10),
        ssthresh: parseInt(formData.get('ssthresh'), 10),
        rtt: parseFloat(formData.get('rtt')),
        mss: parseInt(formData.get('mss'), 10),
        rto: parseFloat(formData.get('rto')),
        duplicate_acks: parseInt(formData.get('duplicate_acks'), 10),
        loss_rate: parseFloat(formData.get('loss_rate')),
        bandwidth: parseFloat(formData.get('bandwidth')),
        queue_size: parseInt(formData.get('queue_size'), 10)
    };
}

function submitFormData(params) {
    return fetch('/simulate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(params)
    }).then(response => response.json());
}

function handleError(error) {
    console.error('Error:', error);
}

let stateTransitionChart, packetLossChart, rttVariationChart, bandwidthUtilChart, queueLengthChart, ackChart;

function initializeCharts() {
    packetLossChart = initializeChart('packetLossChart', 'Packet Loss Events', [], 'bar');
    rttVariationChart = initializeChart('rttVariationChart', 'RTT Variations', [], 'line');
    bandwidthUtilChart = initializeChart('bandwidthUtilChart', 'Bandwidth Utilization', [], 'line');
    queueLengthChart = initializeChart('queueLengthChart', 'Queue Length', [], 'line');
    ackChart = initializeChart('ackChart', 'Acknowledgments', [], 'line');
    stateTransitionChart = initializeChart('stateTransitionChart', 'State Transitions', [], 'line'); // Make sure 'stateTransitionChart' matches the canvas ID in your HTML
}

function initializeChart(chartId, label, initialData, type) {
    const canvasElement = document.getElementById(chartId);
    if (!canvasElement) {
        console.error(`Canvas element with id '${chartId}' not found.`);
        return null;
    }
    const ctx = canvasElement.getContext('2d');
    return new Chart(ctx, {
        type: type,
        data: {
            labels: initialData.map(d => d.x),
            datasets: [{
                label: label,
                data: initialData.map(d => d.y),
                borderColor: chartColors[0],
                backgroundColor: type === 'bar' ? chartColors[0] : 'transparent',
                tension: type === 'line' ? 0.4 : 0
            }]
        },
        options: chartOptions
    });
}

const chartOptions = {
    responsive: true,
    scales: {
        y: {
            beginAtZero: true
        },
        x: {
            type: 'linear',
            position: 'bottom'
        }
    },
    plugins: {
        tooltip: {
            enabled: true,
            mode: 'index',
            intersect: false
        }
    }
};

function updateCharts(data) {
    // Update Packet Loss Chart
    if (packetLossChart && data.packetLossEvents) {
        const packetLossData = data.packetLossEvents.map(event => ({
            x: event.time,
            y: event.event === 'Packet Loss' ? 1 : NaN // Use NaN for non-events for scatter plot
        }));
        updateChart(packetLossChart, data.packetLossEvents.map(event => event.time), packetLossData, 'scatter');
    }
    
    // Update RTT Variation Chart
    if (rttVariationChart) {
        const rttData = processDataForChart(data.rttVariations, 'rtt');
        updateChart(rttVariationChart, data.rttVariations.map(variation => variation.time), rttData);
    } else {
        console.error('rttVariationChart not initialized');
    }

    // Update Bandwidth Utilization Chart
    if (bandwidthUtilChart) {
        const bandwidthData = processDataForChart(data.simulationResults, 'throughput');
        updateChart(bandwidthUtilChart, data.simulationResults.map(result => result.time), bandwidthData);
    } else {
        console.error('bandwidthUtilChart not initialized');
    }

    // Update Queue Length Chart
    if (queueLengthChart) {
        const queueLengthData = data.queueLengths.map((ql, index) => ({ x: index, y: ql }));
        updateChart(queueLengthChart, queueLengthData.map(d => d.x), queueLengthData);
    }

    // Update Acknowledgments Chart
    if (ackChart) {
        const ackData = data.acks.map((ack, index) => ({ x: index, y: ack }));
        updateChart(ackChart, ackData.map(d => d.x), ackData);
    }

    // Update State Transition Chart
    if (stateTransitionChart && data.stateTransitions) {
        const stateTransitionData = data.stateTransitions.map(transition => ({
            x: transition.time,
            y: mapStateToNumericValue(transition.state) // Convert state string to numeric value
        }));
        const labels = data.stateTransitions.map(transition => transition.time);
        updateChart(stateTransitionChart, labels, stateTransitionData, 'line');
    }
}

// Function to map state strings to numeric values for visualization
function mapStateToNumericValue(state) {
    const stateMapping = {
        'Slow Start': 1,
        'Congestion Avoidance': 2,
        'Fast Recovery': 3,
        // Add more states as needed
    };
    return stateMapping[state] || 0;
}

function processDataForChart(data, key) {
    return data.map(item => ({
        x: item.time,
        y: item[key] || 0
    }));
}

// Adjust the updateChart function to accommodate 'scatter' and 'line' types
function updateChart(chart, labels, newData, type = 'line') {
    chart.config.type = type; // Set the chart type dynamically
    chart.data.labels = labels;
    chart.data.datasets.forEach((dataset, index) => {
        dataset.data = newData;
        if (type === 'scatter') {
            dataset.pointRadius = newData.map(d => d.y ? 5 : 0); // Larger points for events
            dataset.pointBackgroundColor = newData.map(d => d.y ? 'red' : 'transparent');
        } else if (type === 'line') {
            dataset.steppedLine = 'middle'; // Use a stepped line for state transitions
            dataset.borderColor = chartColors[index % chartColors.length];
            dataset.backgroundColor = 'transparent';
            dataset.fill = false;
        }
    });
    chart.update();
}