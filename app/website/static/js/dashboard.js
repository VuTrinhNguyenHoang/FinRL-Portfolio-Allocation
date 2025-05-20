async function fetchData() {
    const res = await fetch('/api/data');
    return await res.json();
}

function drawWeights(data) {
    const assetKeys = Object.keys(data[0]).filter(k => k !== 'Date');
    const traces = [];
    
    const colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd', '#8c564b', '#e377c2'];
    
    assetKeys.forEach((key, index) => {
        const values = data.map(r => r[key]);
        
        traces.push({ 
            x: values, 
            type: 'histogram',
            name: key,
            opacity: 0.6,
            legendgroup: key,
            marker: {
                color: colors[index % colors.length],
            },
            xbins: {
                size: 0.05
            },
            histnorm: 'probability density',
            showlegend: true
        });
        
        const min = Math.min(...values);
        const max = Math.max(...values);
        const step = (max - min) / 100;
        const kdeX = Array.from({length: 101}, (_, i) => min + i * step);
        
        const bandwidth = 0.05;
        const kdeY = kdeX.map(x => {
            return values.reduce((acc, val) => {
                return acc + Math.exp(-0.5 * Math.pow((x - val) / bandwidth, 2)) / (bandwidth * Math.sqrt(2 * Math.PI));
            }, 0) / values.length;
        });
        
        traces.push({
            x: kdeX,
            y: kdeY,
            type: 'scatter',
            mode: 'lines',
            name: key + ' KDE',
            line: {
                color: colors[index % colors.length],
                width: 2
            },
            legendgroup: key,
            showlegend: false
        });
    });
    
    Plotly.newPlot('chart-weights', traces, {
        margin: { t: 30 },
        xaxis: { title: 'Weight Value' }, 
        yaxis: { title: 'Density' },
        barmode: 'overlay',
        bargap: 0.05,
        legend: { orientation: 'h', y: -0.2 }
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