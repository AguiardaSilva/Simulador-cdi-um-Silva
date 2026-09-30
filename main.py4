from flask import Flask, jsonify, request, render_template_string
import os

app = Flask(__name__)

DWELL_US = 3000
MAX_RPM = 11000

FUEL_MAPS = {
    "gasolina": {
        "name": "Gasolina",
        "icon": "⛽",
        "color": "#58a6ff",
        "rpm":  [800, 1500, 2000, 3000, 4000, 5000, 6000, 7000, 8000, 9000, 10000, 11000],
        "adv":  [12.0, 20.0, 24.0, 27.0, 28.0, 27.0, 25.0, 23.0, 21.0, 19.5, 18.0, 16.0]
    },
    "etanol": {
        "name": "Etanol",
        "icon": "🍃",
        "color": "#3fb950",
        "rpm":  [800, 1500, 2000, 3000, 4000, 5000, 6000, 7000, 8000, 9000, 10000, 11000],
        "adv":  [14.0, 22.5, 27.5, 30.5, 31.5, 30.5, 28.5, 26.5, 24.5, 23.0, 21.5, 19.5]
    },
    "podium": {
        "name": "Podium",
        "icon": "🏆",
        "color": "#f0883e",
        "rpm":  [800, 1500, 2000, 3000, 4000, 5000, 6000, 7000, 8000, 9000, 10000, 11000],
        "adv":  [13.0, 21.0, 25.5, 28.5, 29.5, 28.5, 26.5, 24.5, 22.5, 21.0, 19.5, 17.5]
    },
    "metanol": {
        "name": "Metanol",
        "icon": "🔥",
        "color": "#ff7b72",
        "rpm":  [800, 1500, 2000, 3000, 4000, 5000, 6000, 7000, 8000, 9000, 10000, 11000],
        "adv":  [16.0, 24.0, 29.0, 32.5, 33.5, 32.5, 30.5, 28.5, 26.5, 25.0, 23.5, 21.5]
    }
}

def get_advance_from_map(rpm, fuel="gasolina"):
    maps = FUEL_MAPS.get(fuel, FUEL_MAPS["gasolina"])
    rpmMap = maps["rpm"]
    advanceMap = maps["adv"]

    if rpm <= rpmMap[0]:
        return advanceMap[0]
    if rpm >= rpmMap[-1]:
        return advanceMap[-1]

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
    <title>Simulador CDI - Arrancada 2T</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        * { box-sizing: border-box; margin: 0; padding: 0; font-family: 'Segoe UI', system-ui, -apple-system, sans-serif; }
        body {
            background: linear-gradient(rgba(10, 12, 18, 0.45), rgba(10, 12, 18, 0.55)),
                        url('https://images.unsplash.com/photo-1493238792000-8113da705763?auto=format&fit=crop&w=1920&q=80') no-repeat center center fixed;
            background-size: cover;
            color: #e6edf3;
            display: flex; justify-content: center; align-items: flex-start;
            min-height: 100vh; padding: 30px 16px; overflow-y: auto;
        }
        .container {
            width: 100%; max-width: 480px;
            display: flex; flex-direction: column; gap: 16px;
        }
        .card {
            background: rgba(22, 27, 34, 0.82);
            backdrop-filter: blur(16px);
            border: 1px solid rgba(48, 54, 61, 0.8);
            border-radius: 16px;
            padding: 20px;
            box-shadow: 0 8px 24px rgba(0,0,0,0.35);
        }
        h1 {
            font-size: 1.35rem; color: #58a6ff; text-align: center;
            letter-spacing: 1px; text-transform: uppercase;
            margin-bottom: 4px;
        }
        .subtitle {
            text-align: center; color: #8b949e; font-size: 0.8rem; margin-bottom: 8px;
        }
        h2 {
            font-size: 0.85rem; color: #f0883e; margin-bottom: 14px;
            text-transform: uppercase; letter-spacing: 0.5px;
            display: flex; align-items: center; gap: 8px;
        }
        h2::before {
            content: ''; width: 3px; height: 14px; background: #f0883e; border-radius: 2px;
        }

        /* Combustível */
        .fuel-grid {
            display: grid; grid-template-columns: repeat(4, 1fr); gap: 10px;
        }
        .fuel-btn {
            background: rgba(13, 17, 23, 0.7);
            border: 2px solid #30363d;
            border-radius: 12px;
            padding: 12px 4px;
            cursor: pointer; text-align: center;
            transition: all 0.2s ease;
            color: #8b949e;
        }
        .fuel-btn:hover { border-color: #58a6ff; transform: translateY(-2px); }
        .fuel-btn.active {
            border-color: var(--fuel-color);
            background: rgba(88, 166, 255, 0.1);
            color: #e6edf3;
            box-shadow: 0 0 0 1px var(--fuel-color);
        }
        .fuel-icon { font-size: 1.5rem; display: block; margin-bottom: 4px; }
        .fuel-name { font-size: 0.68rem; font-weight: 600; text-transform: uppercase; }

        /* RPM */
        .rpm-display {
            font-size: 2.6rem; font-weight: 700; color: #58a6ff;
            text-align: center; margin: 8px 0 14px;
            font-family: 'Courier New', monospace;
            letter-spacing: -1px;
        }
        input[type="range"] {
            width: 100%; height: 6px; border-radius: 4px;
            background: #21262d; outline: none; -webkit-appearance: none;
        }
        input[type="range"]::-webkit-slider-thumb {
            -webkit-appearance: none; width: 20px; height: 20px;
            border-radius: 50%; background: #58a6ff; cursor: pointer;
            box-shadow: 0 0 8px rgba(88,166,255,0.5);
        }

        /* Inputs da puxada */
        .auto-grid {
            display: grid; grid-template-columns: repeat(3, 1fr); gap: 10px; margin-bottom: 14px;
        }
        .input-field label {
            display: block; font-size: 0.72rem; color: #8b949e; margin-bottom: 5px;
            text-transform: uppercase;
        }
        .input-field input {
            width: 100%; background: #0d1117; border: 1px solid #30363d;
            border-radius: 8px; padding: 10px 6px; color: #e6edf3;
            text-align: center; font-size: 0.95rem; font-weight: 600;
        }
        .input-field input:focus {
            outline: none; border-color: #58a6ff;
        }

        .btn {
            width: 100%; background: #238636; color: white; border: none;
            border-radius: 10px; padding: 14px; font-size: 0.95rem; font-weight: 700;
            cursor: pointer; text-transform: uppercase; letter-spacing: 0.5px;
            transition: all 0.2s;
        }
        .btn:hover { filter: brightness(1.12); transform: translateY(-1px); }
        .btn.stop { background: #da3633; }

        /* Métricas */
        .result-item {
            display: flex; justify-content: space-between; align-items: center;
            padding: 11px 0; border-bottom: 1px solid rgba(48, 54, 61, 0.5);
            font-size: 0.9rem;
        }
        .result-item:last-child { border-bottom: none; }
        .label { color: #8b949e; }
        .value { font-weight: 700; color: #f0883e; font-family: monospace; font-size: 0.95rem; }
        .status-badge {
            display: inline-block; padding: 4px 11px; border-radius: 6px;
            font-size: 0.72rem; font-weight: 700; letter-spacing: 0.3px;
        }
        .status-running { background: #238636; color: white; }
        .status-limit { background: #da3633; color: white; }
        .status-auto { background: #8957e5; color: white; }

        /* Painel do gráfico flutuante */
        .chart-panel {
            display: none;
            position: fixed;
            bottom: 20px; right: 20px;
            width: 36%; min-width: 300px; max-width: 440px;
            background: rgba(22, 27, 34, 0.9);
            backdrop-filter: blur(14px);
            border: 1px solid rgba(88, 166, 255, 0.3);
            border-radius: 14px;
            padding: 14px 16px 10px;
            z-index: 100;
            box-shadow: 0 12px 32px rgba(0,0,0,0.5);
        }
        .chart-panel.show { display: block; }
        .chart-panel h3 {
            color: #58a6ff; font-size: 0.9rem; margin-bottom: 8px;
            display: flex; justify-content: space-between; align-items: center;
        }
        .chart-panel .close-btn {
            background: none; border: none; color: #8b949e; font-size: 1.25rem;
            cursor: pointer; line-height: 1;
        }
        .chart-panel .close-btn:hover { color: #f0883e; }
        #chartCanvas { max-height: 200px; width: 100% !important; }
    </style>
</head>
<body>
    <div class="container">
        <div class="card" style="text-align:center; padding-bottom:12px;">
            <h1>Biel CDI Drag-Sim</h1>
            <div class="subtitle">Simulador de Avanço • 2 Tempos Arrancada</div>
        </div>

        <div class="card">
            <h2>Combustível</h2>
            <div class="fuel-grid">
                <div class="fuel-btn active" data-fuel="gasolina" style="--fuel-color: #58a6ff">
                    <span class="fuel-icon">⛽</span>
                    <span class="fuel-name">Gasolina</span>
                </div>
                <div class="fuel-btn" data-fuel="etanol" style="--fuel-color: #3fb950">
                    <span class="fuel-icon">🍃</span>
                    <span class="fuel-name">Etanol</span>
                </div>
                <div class="fuel-btn" data-fuel="podium" style="--fuel-color: #f0883e">
                    <span class="fuel-icon">🏆</span>
                    <span class="fuel-name">Podium</span>
                </div>
                <div class="fuel-btn" data-fuel="metanol" style="--fuel-color: #ff7b72">
                    <span class="fuel-icon">🔥</span>
                    <span class="fuel-name">Metanol</span>
                </div>
            </div>
        </div>

        <div class="card">
            <h2>Controle Manual</h2>
            <div class="rpm-display" id="rpmValue">2 RPM</div>
            <input type="range" id="rpmSlider" min="0" max="12000" step="50" value="2">
        </div>

        <div class="card">
            <h2>Modo Puxada (Automático)</h2>
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
            <h2>Métricas em Tempo Real</h2>
            <div class="result-item">
                <span class="label">Combustível</span>
                <span class="value" id="valFuel">⛽ Gasolina</span>
            </div>
            <div class="result-item">
                <span class="label">Status do Motor</span>
                <span id="statusBadge" class="status-badge status-running">NORMAL</span>
            </div>
            <div class="result-item">
                <span class="label">Avanço de Ignição</span>
                <span class="value" id="valAdvance">0.00 °</span>
            </div>
            <div class="result-item">
                <span class="label">Tempo por Volta</span>
                <span class="value" id="valTimePerRev">0.00 ms</span>
            </div>
            <div class="result-item">
                <span class="label">Dwell na Volta</span>
                <span class="value" id="valDwellDeg">0.00 °</span>
            </div>
        </div>
    </div>

    <div class="chart-panel" id="chartPanel">
        <h3>
            <span>Avanço × Tempo</span>
            <button class="close-btn" id="closeChart">×</button>
        </h3>
        <canvas id="chartCanvas"></canvas>
    </div>

    <script>
        const slider = document.getElementById('rpmSlider');
        const rpmValue = document.getElementById('rpmValue');
        const btnTrigger = document.getElementById('btnTrigger');
        const chartPanel = document.getElementById('chartPanel');
        const closeChart = document.getElementById('closeChart');
        let autoInterval = null;
        let currentFuel = "gasolina";
        let chartInstance = null;
        let chartData = { labels: [], values: [] };

        document.querySelectorAll('.fuel-btn').forEach(btn => {
            btn.addEventListener('click', () => {
                document.querySelectorAll('.fuel-btn').forEach(b => b.classList.remove('active'));
                btn.classList.add('active');
                currentFuel = btn.dataset.fuel;
                const icon = btn.querySelector('.fuel-icon').innerText;
                const name = btn.querySelector('.fuel-name').innerText;
                document.getElementById('valFuel').innerText = `${icon} ${name}`;
                updateMetrics(slider.value);
            });
        });

        closeChart.addEventListener('click', () => chartPanel.classList.remove('show'));

        function updateMetrics(rpm) {
            rpmValue.innerText = Math.round(rpm) + " RPM";
            slider.value = rpm;

            return fetch(`/calculate?rpm=${rpm}&fuel=${currentFuel}`)
                .then(res => res.json())
                .then(data => {
                    document.getElementById('valAdvance').innerText = data.advance.toFixed(2) + " °";
                    document.getElementById('valTimePerRev').innerText = data.time_per_rev_ms.toFixed(2) + " ms";
                    document.getElementById('valDwellDeg').innerText = data.dwell_degrees.toFixed(2) + " °";

                    const badge = document.getElementById('statusBadge');
                    if (data.cut_active) {
                        badge.innerText = "CORTE DE GIRO! ⚠️";
                        badge.className = "status-badge status-limit";
                    } else if (autoInterval) {
                        badge.innerText = "PUXADA ATIVA ⚡";
                        badge.className = "status-badge status-auto";
                    } else {
                        badge.innerText = "NORMAL";
                        badge.className = "status-badge status-running";
                    }
                    return data;
                })
                .catch(() => null);
        }

        function createChart() {
            const ctx = document.getElementById('chartCanvas').getContext('2d');
            if (chartInstance) chartInstance.destroy();
            chartInstance = new Chart(ctx, {
                type: 'line',
                data: {
                    labels: chartData.labels,
                    datasets: [{
                        label: 'Avanço (°)',
                        data: chartData.values,
                        borderColor: '#58a6ff',
                        backgroundColor: 'rgba(88, 166, 255, 0.1)',
                        borderWidth: 2,
                        pointRadius: 2,
                        pointBackgroundColor: '#f0883e',
                        tension: 0.3,
                        fill: true
                    }]
                },
                options: {
                    responsive: true,
                    animation: { duration: 0 },
                    scales: {
                        x: {
                            title: { display: true, text: 'Tempo (s)', color: '#8b949e', font: { size: 10 } },
                            ticks: { color: '#8b949e', font: { size: 9 }, maxTicksLimit: 8 },
                            grid: { color: 'rgba(48,54,61,0.35)' }
                        },
                        y: {
                            title: { display: true, text: '° BTDC', color: '#8b949e', font: { size: 10 } },
                            ticks: { color: '#8b949e', font: { size: 9 } },
                            grid: { color: 'rgba(48,54,61,0.35)' },
                            suggestedMin: 8,
                            suggestedMax: 36
                        }
                    },
                    plugins: { legend: { display: false } }
                }
            });
        }

        slider.addEventListener('input', (e) => {
            if (autoInterval) {
                clearInterval(autoInterval);
                autoInterval = null;
                btnTrigger.innerText = "Iniciar Puxada 🏁";
                btnTrigger.classList.remove('stop');
            }
            updateMetrics(e.target.value);
        });

        btnTrigger.addEventListener('click', () => {
            if (autoInterval) {
                clearInterval(autoInterval);
                autoInterval = null;
                btnTrigger.innerText = "Iniciar Puxada 🏁";
                btnTrigger.classList.remove('stop');
                updateMetrics(slider.value);
                return;
            }

            const rStart = parseFloat(document.getElementById('rpmInit').value);
            const rEnd = parseFloat(document.getElementById('rpmEnd').value);
            const duration = parseFloat(document.getElementById('runTime').value) * 1000;

            if (isNaN(rStart) || isNaN(rEnd) || isNaN(duration) || duration <= 0) {
                alert("Valores inválidos!");
                return;
            }

            chartData = { labels: [], values: [] };
            chartPanel.classList.add('show');
            createChart();

            const fps = 15;
            const intervalTime = 1000 / fps;
            const totalSteps = duration / intervalTime;
            let currentStep = 0;

            btnTrigger.innerText = "Abortar Puxada 🛑";
            btnTrigger.classList.add('stop');

            autoInterval = setInterval(async () => {
                currentStep++;
                let progress = Math.min(currentStep / totalSteps, 1);
                let currentRpm = rStart + (rEnd - rStart) * progress;
                let timeSec = (progress * duration / 1000).toFixed(1);

                const data = await updateMetrics(currentRpm);
                if (data) {
                    chartData.labels.push(timeSec);
                    chartData.values.push(parseFloat(data.advance.toFixed(2)));
                    if (chartInstance) {
                        chartInstance.data.labels = chartData.labels;
                        chartInstance.data.datasets[0].data = chartData.values;
                        chartInstance.update();
                    }
                }

                if (progress >= 1) {
                    clearInterval(autoInterval);
                    autoInterval = null;
                    btnTrigger.innerText = "Iniciar Puxada 🏁";
                    btnTrigger.classList.remove('stop');
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
    except (TypeError, ValueError):
        rpm = 2.0

    fuel = request.args.get("fuel", "gasolina").lower()
    if fuel not in FUEL_MAPS:
        fuel = "gasolina"

    advance = get_advance_from_map(rpm, fuel)

    if rpm > 0:
        time_per_rev_ms = 60000.0 / rpm
    else:
        time_per_rev_ms = 0.0

    dwell_seconds = DWELL_US / 1_000_000.0
    if time_per_rev_ms > 0:
        dwell_degrees = (dwell_seconds / (time_per_rev_ms / 1000.0)) * 360.0
    else:
        dwell_degrees = 0.0

    cut_active = rpm >= MAX_RPM

    return jsonify({
        "rpm": rpm,
        "fuel": fuel,
        "advance": advance,
        "time_per_rev_ms": time_per_rev_ms,
        "dwell_degrees": dwell_degrees,
        "cut_active": cut_active
    })

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
