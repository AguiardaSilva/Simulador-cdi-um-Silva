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
    <title>Simulador CDI - Protótipo Arrancada 2T</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        * { box-sizing: border-box; margin: 0; padding: 0; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; }
        body {
            background: linear-gradient(rgba(11, 14, 20, 0.55), rgba(11, 14, 20, 0.65)),
                        url('https://images.unsplash.com/photo-1558981806-ec527fa84c39?auto=format&fit=crop&w=1920&q=80') no-repeat center center fixed;
            background-size: cover;
            color: #c9d1d9;
            display: flex; justify-content: center; align-items: center;
            min-height: 100vh; padding: 20px 0; overflow-y: auto;
        }
        .container {
            position: relative; background: rgba(17, 22, 30, 0.88);
            backdrop-filter: blur(12px); border: 1px solid rgba(56, 139, 253, 0.25);
            border-radius: 20px; padding: 28px; width: 92%; max-width: 540px;
            box-shadow: 0 12px 40px rgba(0, 0, 0, 0.6);
            z-index: 10;
        }
        h1 {
            font-size: 1.5rem; color: #58a6ff; text-align: center; margin-bottom: 20px;
            text-transform: uppercase; letter-spacing: 1.4px;
            text-shadow: 0 0 10px rgba(88, 166, 255, 0.3);
        }
        h2 {
            font-size: 1.05rem; color: #f0883e; margin-bottom: 12px;
            text-transform: uppercase; border-left: 3px solid #f0883e; padding-left: 8px;
        }
        .panel {
            background: rgba(30, 37, 48, 0.5); border: 1px solid #30363d;
            border-radius: 12px; padding: 16px; margin-bottom: 18px;
        }
        .control-group { margin-bottom: 10px; }
        label { display: block; font-size: 0.85rem; margin-bottom: 5px; color: #8b949e; }
        .rpm-display {
            font-size: 2.2rem; font-weight: bold; color: #58a6ff;
            text-align: center; margin-bottom: 8px; font-family: 'Courier New', Courier, monospace;
        }
        input[type="range"] {
            width: 100%; height: 8px; border-radius: 5px; background: #21262d;
            outline: none; -webkit-appearance: none;
        }
        input[type="range"]::-webkit-slider-thumb {
            -webkit-appearance: none; width: 20px; height: 20px;
            border-radius: 50%; background: #58a6ff; cursor: pointer;
        }
        .auto-grid {
            display: grid; grid-template-columns: repeat(3, 1fr); gap: 8px; margin-bottom: 10px;
        }
        .input-field input {
            width: 100%; background: #0d1117; border: 1px solid #30363d;
            border-radius: 6px; padding: 7px; color: #c9d1d9; text-align: center; font-size: 0.95rem;
        }
        .btn {
            width: 100%; background: #238636; color: white; border: none;
            border-radius: 6px; padding: 11px; font-size: 0.95rem; font-weight: bold;
            cursor: pointer; text-transform: uppercase; transition: 0.2s;
        }
        .btn:hover { filter: brightness(1.1); }
        .btn.stop { background: #da3633; }

        .fuel-grid {
            display: grid; grid-template-columns: repeat(4, 1fr); gap: 8px;
        }
        .fuel-btn {
            background: #0d1117; border: 2px solid #30363d; border-radius: 10px;
            padding: 9px 4px; cursor: pointer; text-align: center; transition: all 0.2s;
            color: #8b949e;
        }
        .fuel-btn:hover { border-color: #58a6ff; transform: translateY(-1px); }
        .fuel-btn.active {
            border-color: var(--fuel-color); background: rgba(88, 166, 255, 0.12);
            color: #c9d1d9; box-shadow: 0 0 10px rgba(88, 166, 255, 0.2);
        }
        .fuel-icon { font-size: 1.6rem; display: block; margin-bottom: 2px; }
        .fuel-name { font-size: 0.7rem; font-weight: 600; text-transform: uppercase; }

        .results {
            background: rgba(1, 4, 9, 0.7); border-radius: 12px; padding: 16px; border: 1px solid #30363d;
        }
        .result-item {
            display: flex; justify-content: space-between; padding: 8px 0;
            border-bottom: 1px solid rgba(48, 54, 61, 0.45); font-size: 0.92rem;
        }
        .result-item:last-child { border-bottom: none; }
        .label { color: #8b949e; }
        .value { font-weight: bold; color: #f0883e; font-family: monospace; }
        .status-badge {
            display: inline-block; padding: 3px 9px; border-radius: 5px;
            font-size: 0.75rem; font-weight: bold;
        }
        .status-running { background: #238636; color: white; }
        .status-limit { background: #da3633; color: white; }
        .status-auto { background: #8957e5; color: white; }

        /* Painel flutuante do gráfico (~30-40% da tela) */
        .chart-panel {
            display: none;
            position: fixed;
            bottom: 18px;
            right: 18px;
            width: 38%;
            min-width: 320px;
            max-width: 480px;
            background: rgba(17, 22, 30, 0.82);
            backdrop-filter: blur(10px);
            border: 1px solid rgba(88, 166, 255, 0.35);
            border-radius: 14px;
            padding: 14px 16px 12px;
            z-index: 100;
            box-shadow: 0 10px 30px rgba(0,0,0,0.45);
        }
        .chart-panel.show { display: block; }
        .chart-panel h3 {
            color: #58a6ff; font-size: 0.95rem; margin-bottom: 8px;
            display: flex; justify-content: space-between; align-items: center;
        }
        .chart-panel .close-btn {
            background: none; border: none; color: #8b949e; font-size: 1.3rem;
            cursor: pointer; line-height: 1;
        }
        .chart-panel .close-btn:hover { color: #f0883e; }
        #chartCanvas { max-height: 220px; width: 100% !important; }
    </style>
</head>
<body>
    <div class="container">
        <h1>Biel CDI Drag-Sim</h1>

        <div class="panel">
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

        <div class="panel">
            <h2>Controle Manual</h2>
            <div class="control-group">
                <div class="rpm-display" id="rpmValue">2000 RPM</div>
                <input type="range" id="rpmSlider" min="800" max="12000" step="50" value="2000">
            </div>
        </div>

        <div class="panel">
            <h2>Modo Puxada (Automático)</h2>
            <div class="auto-grid">
                <div class="input-field">
                    <label>Giro Inicial</label>
                    <input type="number" id="rpmInit" value="2000">
                </div>
                <div class="input-field">
                    <label>Tempo (s)</label>
                    <input type="number" id="runTime" value="2.5" step="0.5">
                </div>
                <div class="input-field">
                    <label>Giro Final</label>
                    <input type="number" id="rpmEnd" value="11500">
                </div>
            </div>
            <button class="btn" id="btnTrigger">Iniciar Puxada 🏁</button>
        </div>

        <div class="results">
            <h2>Métricas em Tempo Real</h2>
            <div class="result-item">
                <span class="label">Combustível:</span>
                <span class="value" id="valFuel">⛽ Gasolina</span>
            </div>
            <div class="result-item">
                <span class="label">Status do Motor:</span>
                <span id="statusBadge" class="status-badge status-running">NORMAL</span>
            </div>
            <div class="result-item">
                <span class="label">Avanço de Ignição:</span>
                <span class="value" id="valAdvance">0.00 °</span>
            </div>
            <div class="result-item">
                <span class="label">Tempo por Volta:</span>
                <span class="value" id="valTimePerRev">0.00 ms</span>
            </div>
            <div class="result-item">
                <span class="label">Dwell Ocupado na Volta:</span>
                <span class="value" id="valDwellDeg">0.00 °</span>
            </div>
        </div>
    </div>

    <!-- Painel flutuante do gráfico (sobreposto ~30-40%) -->
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

        closeChart.addEventListener('click', () => {
            chartPanel.classList.remove('show');
        });

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
                        badge.innerText = "OPERANDO";
                        badge.className = "status-badge status-running";
                    }
                    return data;
                })
                .catch(err => {
                    console.error("Erro:", err);
                    return null;
                });
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
                        backgroundColor: 'rgba(88, 166, 255, 0.12)',
                        borderWidth: 2,
                        pointRadius: 2.5,
                        pointBackgroundColor: '#f0883e',
                        tension: 0.25,
                        fill: true
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: true,
                    animation: { duration: 0 },
                    scales: {
                        x: {
                            title: { display: true, text: 'Tempo (s)', color: '#8b949e', font: { size: 11 } },
                            ticks: { color: '#8b949e', font: { size: 10 } },
                            grid: { color: 'rgba(48,54,61,0.4)' }
                        },
                        y: {
                            title: { display: true, text: '° BTDC', color: '#8b949e', font: { size: 11 } },
                            ticks: { color: '#8b949e', font: { size: 10 } },
                            grid: { color: 'rgba(48,54,61,0.4)' },
                            suggestedMin: 10,
                            suggestedMax: 35
                        }
                    },
                    plugins: {
                        legend: { display: false }
                    }
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

            const fps = 20;
            const intervalTime = 1000 / fps;
            const totalSteps = duration / intervalTime;
            let currentStep = 0;

            btnTrigger.innerText = "Abortar Puxada 🛑";
            btnTrigger.classList.add('stop');

            autoInterval = setInterval(async () => {
                currentStep++;
                let progress = Math.min(currentStep / totalSteps, 1);
                let currentRpm = rStart + (rEnd - rStart) * progress;
                let timeSec = (progress * duration / 1000).toFixed(2);

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

        updateMetrics(2000);
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
        rpm = float(request.args.get("rpm", 1000))
    except (TypeError, ValueError):
        rpm = 1000.0

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
