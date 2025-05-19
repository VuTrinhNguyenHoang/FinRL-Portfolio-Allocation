async function fetchData() {
    const res = await fetch('/api/data');
    return await res.json();
}

function drawWeights(data) {
    const dates = data.map(r => r.Date);
    const assetKeys = Object.keys(data[0]).filter(k => k !== 'Date');
    const traces = assetKeys.map(key => ({ x: dates, y: data.map(r => r[key]), name: key, type: 'scatter' }));
    Plotly.newPlot('chart-weights', traces, {
        margin: { t: 30 },
        xaxis: { title: 'Date' }, yaxis: { title: 'Weight' }
    });
}

function drawPortfolio(data) {
    const dates = data.map(r => r.Date);
    const traceKeys = ['PPO Value', 'BTC Value', 'Equal-Weighted Value'];
    const traces = traceKeys.map(key => ({ x: dates, y: data.map(r => r[key]), name: key, type: 'scatter' }));
    Plotly.newPlot('chart-portfolio', traces, {
        margin: { t: 30 },
        xaxis: { title: 'Date' }, yaxis: { title: 'Value' }
    });
}

function fillMetricsTable(data) {
    const thead = document.getElementById('metrics-header');
    const tbody = document.getElementById('metrics-body');
    
    thead.innerHTML = '';
    tbody.innerHTML = '';
    
    const headerRow = document.createElement('tr');
    headerRow.appendChild(document.createElement('th'));
    
    const strategies = data.map(item => item.strategy);
    
    strategies.forEach(strategy => {
        const th = document.createElement('th');
        th.textContent = strategy;
        headerRow.appendChild(th);
    });
    
    thead.appendChild(headerRow);
    
    const metrics = [
        { key: 'start_period', label: 'Start Period' },
        { key: 'end_period', label: 'End Period' },
        { key: 'cumulative_return', label: 'Cumulative Return' },
        { key: 'annual_return', label: 'Annual Return' },
        { key: 'sharpe_ratio', label: 'Sharpe Ratio' },
        { key: 'max_drawdown', label: 'Max Drawdown' },
        { key: 'volatility', label: 'Volatility' }
    ];
    
    metrics.forEach(metric => {
        const row = document.createElement('tr');
        
        const labelCell = document.createElement('th');
        labelCell.textContent = metric.label;
        row.appendChild(labelCell);
        
        data.forEach(strategy => {
            const cell = document.createElement('td');
            cell.textContent = strategy[metric.key];
            row.appendChild(cell);
        });
        
        tbody.appendChild(row);
    });
}

(async () => {
    const { weights, portfolio, metrics } = await fetchData();
    drawWeights(weights);
    drawPortfolio(portfolio);
    fillMetricsTable(metrics);
})();