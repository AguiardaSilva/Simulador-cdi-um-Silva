from flask import Flask, jsonify, request, render_template_string
import os

app = Flask(__name__)

DWELL_US = 3000
MAX_RPM = 11000

FUEL_MAPS = {
    "gasolina": {
        "name": "Gasolina", "icon": "⛽", "color": "#58a6ff",
        "rpm":  [800, 1500, 2000, 3000, 4000, 5000, 6000, 7000, 8000, 9000, 10000, 11000],
        "adv":  [12.0, 20.0, 24.0, 27.0, 28.0, 27.0, 25.0, 23.0, 21.0, 19.5, 18.0, 16.0]
    },
    "etanol": {
        "name": "Etanol", "icon": "🍃", "color": "#3fb950",
        "rpm":  [800, 1500, 2000, 3000, 4000, 5000, 6000, 7000, 8000, 9000, 10000, 11000],
        "adv":  [14.0, 22.5, 27.5, 30.5, 31.5, 30.5, 28.5, 26.5, 24.5, 23.0, 21.5, 19.5]
    },
    "podium": {
        "name": "Podium", "icon": "🏆", "color": "#f0883e",
        "rpm":  [800, 1500, 2000, 3000, 4000, 5000, 6000, 7000, 8000, 9000, 10000, 11000],
        "adv":  [13.0, 21.0, 25.5, 28.5, 29.5, 28.5, 26.5, 24.5, 22.5, 21.0, 19.5, 17.5]
    },
    "metanol": {
        "name": "Metanol", "icon": "🔥", "color": "#ff7b72",
        "rpm":  [800, 1500, 2000, 3000, 4000, 5000, 6000, 7000, 8000, 9000, 10000, 11000],
        "adv":  [16.0, 24.0, 29.0, 32.5, 33.5, 32.5, 30.5, 28.5, 26.5, 25.0, 23.5, 21.5]
    }
}

def get_advance_from_map(rpm, fuel="gasolina"):
    maps = FUEL_MAPS.get(fuel, FUEL_MAPS["gasolina"])
    rpmMap, advanceMap = maps["rpm"], maps["adv"]
    if rpm <= rpmMap[0]: return advanceMap[0]
    if rpm >= rpmMap[-1]: return advanceMap[-1]
    for i in range(len(rpmMap) - 1):
        if rpmMap[i] <= rpm <= rpmMap[i + 1]:
            ratio = (rpm - rpmMap[i]) / (rpmMap[i + 1] - rpmMap[i])
            return advanceMap[i] + ratio * (advanceMap[i + 1] - advanceMap[i])
    return advanceMap[0]

HTML_INTERFACE = """
<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Biel CDI Drag-Sim</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
<style>
* { box-sizing: border-box; margin: 0; padding: 0; font-family: 'Segoe UI', system-ui, sans-serif; }
html, body { height: 100%; overflow: hidden; }
body {
    background: linear-gradient(rgba(8,10,15,0.50), rgba(8,10,15,0.62)),
                url('https://images.unsplash.com/photo-1493238792000-8113da705763?auto=format&fit=crop&w=1920&q=80') no-repeat center center fixed;
    background-size: cover;
    color: #e6edf3;
    display: flex; justify-content: center; align-items: center;
    padding: 12px;
}
.container {
    width: 100%; max-width: 420px;
    display: flex; flex-direction: column; gap: 8px;
    max-height: 96vh;
}
.card {
    background: rgba(22,27,34,0.88);
    backdrop-filter: blur(12px);
    border: 1px solid rgba(48,54,61,0.7);
    border-radius: 12px;
    padding: 10px 12px;
    box-shadow: 0 4px 14px rgba(0,0,0,0.3);
}
h1 {
    font-size: 1.05rem; color: #58a6ff; text-align: center;
    letter-spacing: 0.8px; text-transform: uppercase; line-height: 1.2;
}
.subtitle { text-align: center; color: #8b949e; font-size: 0.68rem; margin-top: 1px; }
h2 {
    font-size: 0.72rem; color: #f0883e; margin-bottom: 6px;
    text-transform: uppercase; display: flex; align-items: center; gap: 5px;
}
h2::before { content: ''; width: 2.5px; height: 11px; background: #f0883e; border-radius: 2px; }

/* Combustível */
.fuel-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 6px; }
.fuel-btn {
    background: rgba(13,17,23,0.65); border: 1.5px solid #30363d; border-radius: 9px;
    padding: 6px 2px; cursor: pointer; text-align: center; transition: 0.15s; color: #8b949e;
}
.fuel-btn:hover { border-color: #58a6ff; }
.fuel-btn.active {
    border-color: var(--fuel-color); background: rgba(88,166,255,0.12);
    color: #e6edf3; box-shadow: 0 0 0 1px var(--fuel-color);
}
.fuel-icon { font-size: 1.15rem; display: block; line-height: 1.2; }
.fuel-name { font-size: 0.58rem; font-weight: 600; text-transform: uppercase; }

/* RPM */
.rpm-display {
    font-size: 1.9rem; font-weight: 700; color: #58a6ff; text-align: center;
    margin: 2px 0 6px; font-family: 'Courier New', monospace; letter-spacing: -0.5px;
}
input[type="range"] {
    width: 100%; height: 5px; border-radius: 3px; background: #21262d;
    outline: none; -webkit-appearance: none;
}
input[type="range"]::-webkit-slider-thumb {
    -webkit-appearance: none; width: 15px; height: 15px; border-radius: 50%;
    background: #58a6ff; cursor: pointer;
}

/* Puxada */
.auto-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 6px; margin-bottom: 7px; }
.input-field label {
    display: block; font-size: 0.62rem; color: #8b949e; margin-bottom: 2px; text-transform: uppercase;
}
.input-field input {
    width: 100%; background: #0d1117; border: 1px solid #30363d; border-radius: 6px;
    padding: 6px 3px; color: #e6edf3; text-align: center; font-size: 0.85rem; font-weight: 600;
}
.input-field input:focus { outline: none; border-color: #58a6ff; }

.btn {
    width: 100%; background: #238636; color: white; border: none; border-radius: 8px;
    padding: 8px; font-size: 0.82rem; font-weight: 700; cursor: pointer;
    text-transform: uppercase; transition: 0.15s;
}
.btn:hover { filter: brightness(1.1); }
.btn.stop { background: #da3633; }

/* Métricas - mais compactas */
.result-item {
    display: flex; justify-content: space-between; align-items: center;
    padding: 4px 0; border-bottom: 1px solid rgba(48,54,61,0.35); font-size: 0.78rem;
}
.result-item:last-child { border-bottom: none; }
.label { color: #8b949e; }
.value { font-weight: 700; color: #f0883e; font-family: monospace; font-size: 0.82rem; }
.status-badge {
    display: inline-block; padding: 2px 7px; border-radius: 4px;
    font-size: 0.62rem; font-weight: 700;
}
.status-running { background: #238636; color: white; }
.status-limit { background: #da3633; color: white; }
.status-auto { background: #8957e5; color: white; }

/* Gráfico flutuante */
.chart-panel {
    display: none; position: fixed; top: 60px; right: 16px;
    width: 340px; max-width: 90vw;
    background: rgba(22,27,34,0.94); backdrop-filter: blur(14px);
    border: 1px solid rgba(88,166,255,0.3); border-radius: 12px;
    z-index: 200; box-shadow: 0 10px 28px rgba(0,0,0,0.5); user-select: none;
}
.chart-panel.show { display: block; }
.chart-panel.pinned { border-color: #3fb950; }
.chart-header {
    display: flex; align-items: center; justify-content: space-between;
    padding: 7px 10px; cursor: move;
    background: rgba(88,166,255,0.07); border-radius: 12px 12px 0 0;
    border-bottom: 1px solid rgba(48,54,61,0.5);
}
.chart-header h3 { color: #58a6ff; font-size: 0.78rem; margin: 0; }
.chart-actions { display: flex; gap: 4px; align-items: center; }
.chart-actions button {
    background: rgba(13,17,23,0.8); border: 1px solid #30363d; color: #c9d1d9;
    border-radius: 5px; padding: 2px 6px; font-size: 0.65rem; cursor: pointer;
}
.chart-actions button:hover { border-color: #58a6ff; color: #58a6ff; }
.chart-actions button.active-pin { background: #238636; border-color: #238636; color: white; }
.chart-actions .close-btn { font-size: 1rem; padding: 0 5px; }
.chart-body { padding: 6px 10px 8px; }
#chartCanvas { max-height: 170px; width: 100% !important; }
.chart-legend { display: flex; flex-wrap: wrap; gap: 4px; margin-top: 4px; font-size: 0.62rem; }
.legend-item {
    display: flex; align-items: center; gap: 3px;
    background: rgba(13,17,23,0.55); padding: 1px 5px; border-radius: 3px;
}
.legend-color { width: 8px; height: 8px; border-radius: 2px; }
</style>
</head>
<body>
<div class="container">
    <div class="card" style="text-align:center; padding:8px 12px;">
        <h1>Biel CDI Drag-Sim</h1>
        <div class="subtitle">Avanço • 2T Arrancada</div>
    </div>

    <div class="card">
        <h2>Combustível</h2>
        <div class="fuel-grid">
            <div class="fuel-btn active" data-fuel="gasolina" style="--fuel-color:#58a6ff">
                <span class="fuel-icon">⛽</span><span class="fuel-name">Gasolina</span>
            </div>
            <div class="fuel-btn" data-fuel="etanol" style="--fuel-color:#3fb950">
                <span class="fuel-icon">🍃</span><span class="fuel-name">Etanol</span>
            </div>
            <div class="fuel-btn" data-fuel="podium" style="--fuel-color:#f0883e">
                <span class="fuel-icon">🏆</span><span class="fuel-name">Podium</span>
            </div>
            <div class="fuel-btn" data-fuel="metanol" style="--fuel-color:#ff7b72">
                <span class="fuel-icon">🔥</span><span class="fuel-name">Metanol</span>
            </div>
        </div>
    </div>

    <div class="card">
        <h2>Controle Manual</h2>
        <div class="rpm-display" id="rpmValue">2 RPM</div>
        <input type="range" id="rpmSlider" min="0" max="12000" step="50" value="2">
    </div>

    <div class="card">
        <h2>Modo Puxada</h2>
        <div class="auto-grid">
            <div class="input-field">
                <label>Giro Inicial</label>
                <input type="number" id="rpmInit" value="2">
            </div>
            <div class="input-field">
                <label>Tempo (s)</label>
                <input type="number" id="runTime" value="60" step="1">
            </div>
            <div class="input-field">
                <label>Giro Final</label>
                <input type="number" id="rpmEnd" value="11500">
            </div>
        </div>
        <button class="btn" id="btnTrigger">Iniciar Puxada 🏁</button>
    </div>

    <div class="card">
        <h2>Métricas</h2>
        <div class="result-item">
            <span class="label">Combustível</span>
            <span class="value" id="valFuel">⛽ Gasolina</span>
        </div>
        <div class="result-item">
            <span class="label">Status</span>
            <span id="statusBadge" class="status-badge status-running">NORMAL</span>
        </div>
        <div class="result-item">
            <span class="label">Avanço</span>
            <span class="value" id="valAdvance">0.00 °</span>
        </div>
        <div class="result-item">
            <span class="label">Tempo/Volta</span>
            <span class="value" id="valTimePerRev">0.00 ms</span>
        </div>
        <div class="result-item">
            <span class="label">Dwell</span>
            <span class="value" id="valDwellDeg">0.00 °</span>
        </div>
    </div>
</div>

<div class="chart-panel" id="chartPanel">
    <div class="chart-header" id="chartHeader">
        <h3>Avanço × Tempo</h3>
        <div class="chart-actions">
            <button id="btnAddCurve" title="Adicionar nova curva">+ Curva</button>
            <button id="btnClearChart" title="Limpar">Limpar</button>
            <button id="btnPin" title="Fixar">📌</button>
            <button class="close-btn" id="closeChart">×</button>
        </div>
    </div>
    <div class="chart-body">
        <canvas id="chartCanvas"></canvas>
        <div class="chart-legend" id="chartLegend"></div>
    </div>
</div>

<script>
const slider = document.getElementById('rpmSlider');
const rpmValue = document.getElementById('rpmValue');
const btnTrigger = document.getElementById('btnTrigger');
const chartPanel = document.getElementById('chartPanel');
const chartHeader = document.getElementById('chartHeader');
const closeChart = document.getElementById('closeChart');
const btnPin = document.getElementById('btnPin');
const btnAddCurve = document.getElementById('btnAddCurve');
const btnClearChart = document.getElementById('btnClearChart');
const chartLegend = document.getElementById('chartLegend');

let autoInterval = null, currentFuel = "gasolina", chartInstance = null;
let isPinned = false, addAsNewCurve = false, curveCount = 0;
const COLORS = ['#58a6ff','#3fb950','#f0883e','#ff7b72','#8957e5','#d2a8ff','#79c0ff'];

let isDragging = false, startX, startY, origX, origY;
chartHeader.addEventListener('mousedown', e => {
    if (e.target.tagName === 'BUTTON') return;
    isDragging = true; startX = e.clientX; startY = e.clientY;
    const r = chartPanel.getBoundingClientRect(); origX = r.left; origY = r.top;
    e.preventDefault();
});
document.addEventListener('mousemove', e => {
    if (!isDragging) return;
    chartPanel.style.left = (origX + e.clientX - startX) + 'px';
    chartPanel.style.top = (origY + e.clientY - startY) + 'px';
    chartPanel.style.right = 'auto';
});
document.addEventListener('mouseup', () => isDragging = false);

btnPin.addEventListener('click', () => {
    isPinned = !isPinned;
    btnPin.classList.toggle('active-pin', isPinned);
    chartPanel.classList.toggle('pinned', isPinned);
    btnPin.textContent = isPinned ? '📍' : '📌';
});
closeChart.addEventListener('click', () => { if (!isPinned) chartPanel.classList.remove('show'); });
btnAddCurve.addEventListener('click', () => {
    addAsNewCurve = true;
    btnAddCurve.style.background = '#238636'; btnAddCurve.style.color = '#fff';
    setTimeout(() => { btnAddCurve.style.background = ''; btnAddCurve.style.color = ''; }, 500);
});
btnClearChart.addEventListener('click', () => {
    if (chartInstance) { chartInstance.data.datasets = []; chartInstance.data.labels = []; chartInstance.update(); }
    chartLegend.innerHTML = ''; curveCount = 0; addAsNewCurve = false;
});

document.querySelectorAll('.fuel-btn').forEach(btn => {
    btn.addEventListener('click', () => {
        document.querySelectorAll('.fuel-btn').forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
        currentFuel = btn.dataset.fuel;
        document.getElementById('valFuel').innerText = btn.querySelector('.fuel-icon').innerText + ' ' + btn.querySelector('.fuel-name').innerText;
        updateMetrics(slider.value);
    });
});

function updateMetrics(rpm) {
    rpmValue.innerText = Math.round(rpm) + " RPM";
    slider.value = rpm;
    return fetch(`/calculate?rpm=${rpm}&fuel=${currentFuel}`).then(r => r.json()).then(data => {
        document.getElementById('valAdvance').innerText = data.advance.toFixed(2) + " °";
        document.getElementById('valTimePerRev').innerText = data.time_per_rev_ms.toFixed(2) + " ms";
        document.getElementById('valDwellDeg').innerText = data.dwell_degrees.toFixed(2) + " °";
        const badge = document.getElementById('statusBadge');
        if (data.cut_active) { badge.innerText = "CORTE!"; badge.className = "status-badge status-limit"; }
        else if (autoInterval) { badge.innerText = "PUXADA"; badge.className = "status-badge status-auto"; }
        else { badge.innerText = "NORMAL"; badge.className = "status-badge status-running"; }
        return data;
    }).catch(() => null);
}

function ensureChart() {
    if (chartInstance) return;
    chartInstance = new Chart(document.getElementById('chartCanvas').getContext('2d'), {
        type: 'line', data: { labels: [], datasets: [] },
        options: {
            responsive: true, animation: { duration: 0 },
            scales: {
                x: { title: { display: true, text: 's', color: '#8b949e', font: { size: 9 } },
                     ticks: { color: '#8b949e', font: { size: 8 }, maxTicksLimit: 7 }, grid: { color: 'rgba(48,54,61,0.25)' } },
                y: { title: { display: true, text: '°', color: '#8b949e', font: { size: 9 } },
                     ticks: { color: '#8b949e', font: { size: 8 } }, grid: { color: 'rgba(48,54,61,0.25)' },
                     suggestedMin: 8, suggestedMax: 36 }
            },
            plugins: { legend: { display: false } }
        }
    });
}

function addLegendItem(label, color) {
    const el = document.createElement('div');
    el.className = 'legend-item';
    el.innerHTML = `<div class="legend-color" style="background:${color}"></div>${label}`;
    chartLegend.appendChild(el);
}

slider.addEventListener('input', e => {
    if (autoInterval) { clearInterval(autoInterval); autoInterval = null; btnTrigger.innerText = "Iniciar Puxada 🏁"; btnTrigger.classList.remove('stop'); }
    updateMetrics(e.target.value);
});

btnTrigger.addEventListener('click', () => {
    if (autoInterval) {
        clearInterval(autoInterval); autoInterval = null;
        btnTrigger.innerText = "Iniciar Puxada 🏁"; btnTrigger.classList.remove('stop');
        updateMetrics(slider.value); return;
    }
    const rStart = parseFloat(document.getElementById('rpmInit').value);
    const rEnd = parseFloat(document.getElementById('rpmEnd').value);
    const duration = parseFloat(document.getElementById('runTime').value) * 1000;
    if (isNaN(rStart) || isNaN(rEnd) || isNaN(duration) || duration <= 0) { alert("Valores inválidos!"); return; }

    chartPanel.classList.add('show'); ensureChart();
    const color = COLORS[curveCount % COLORS.length];
    const label = document.getElementById('valFuel').innerText + ' #' + (curveCount + 1);

    if (!addAsNewCurve && chartInstance.data.datasets.length > 0) {
        chartInstance.data.datasets = []; chartInstance.data.labels = [];
        chartLegend.innerHTML = ''; curveCount = 0;
    }
    chartInstance.data.datasets.push({
        label, data: [], borderColor: color, backgroundColor: color + '15',
        borderWidth: 2, pointRadius: 0, tension: 0.3, fill: false
    });
    addLegendItem(label, color); curveCount++; addAsNewCurve = false;
    const dsIdx = chartInstance.data.datasets.length - 1;

    const fps = 12, intervalTime = 1000 / fps, totalSteps = duration / intervalTime;
    let step = 0;
    btnTrigger.innerText = "Abortar 🛑"; btnTrigger.classList.add('stop');

    autoInterval = setInterval(async () => {
        step++;
        const progress = Math.min(step / totalSteps, 1);
        const rpm = rStart + (rEnd - rStart) * progress;
        const t = (progress * duration / 1000).toFixed(1);
        const data = await updateMetrics(rpm);
        if (data) {
            if (dsIdx === 0 || chartInstance.data.labels.length < step)
                chartInstance.data.labels.push(t);
            chartInstance.data.datasets[dsIdx].data.push(+data.advance.toFixed(2));
            chartInstance.update();
        }
        if (progress >= 1) {
            clearInterval(autoInterval); autoInterval = null;
            btnTrigger.innerText = "Iniciar Puxada 🏁"; btnTrigger.classList.remove('stop');
        }
    }, intervalTime);
});

updateMetrics(2);
</script>
</body>
</html>
"""

@app.route("/")
def index():
    return render_template_string(HTML_INTERFACE)

@app.route("/calculate")
def calculate():
    try:
        rpm = float(request.args.get("rpm", 2))
    except:
        rpm = 2.0
    fuel = request.args.get("fuel", "gasolina").lower()
    if fuel not in FUEL_MAPS: fuel = "gasolina"
    advance = get_advance_from_map(rpm, fuel)
    tpr = 60000.0 / rpm if rpm > 0 else 0.0
    dwell = (DWELL_US / 1e6) / (tpr / 1000.0) * 360.0 if tpr > 0 else 0.0
    return jsonify({
        "rpm": rpm, "fuel": fuel, "advance": advance,
        "time_per_rev_ms": tpr, "dwell_degrees": dwell,
        "cut_active": rpm >= MAX_RPM
    })

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
