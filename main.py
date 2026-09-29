from flask import Flask, jsonify, request, render_template_string
import os

app = Flask(__name__)

# CONFIGURAÇÕES REPLICADAS DO ESP32
DWELL_US = 3000
MAX_RPM = 11000

# MAPA DE AVANÇO ORIGINAL (Corrigido e restaurado)
rpmMap = [1000, 2000, 3000, 4000, 5000, 6000, 8000, 10000]
advanceMap = [12.0, 18.0, 22.0, 25.0, 26.0, 25.0, 20.0, 16.0]

def get_advance_from_map(rpm):
    # Proteção para rotações abaixo do mínimo do mapa
    if rpm <= rpmMap[0]:
        return advanceMap[0]
    # Proteção para rotações acima do máximo do mapa
    if rpm >= rpmMap[-1]:
        return advanceMap[-1]
        
    for i in range(len(rpmMap) - 1):
        if rpmMap[i] <= rpm <= rpmMap[i+1]:
            # Interpolação linear idêntica ao algoritmo em C++ do ESP32
            ratio = (rpm - rpmMap[i]) / (rpmMap[i+1] - rpmMap[i])
            return advanceMap[i] + ratio * (advanceMap[i+1] - advanceMap[i])
    return advanceMap[0]

# INTERFACE INTERATIVA (HTML + CSS + JS)
HTML_INTERFACE = """
<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Simulador CDI - Protótipo Arrancada 2T</title>
    <style>
        * {
            box-sizing: border-box;
            margin: 0;
            padding: 0;
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        }

        body {
            background-color: #0b0e14;
            color: #c9d1d9;
            display: flex;
            justify-content: center;
            align-items: center;
            min-height: 100vh;
            padding: 20px 0;
            overflow-y: auto;
            position: relative;
        }

        /* Imagem de fundo: Protótipo de Arrancada Técnico/Translúcido */
        body::before {
            content: "";
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background-image: url('https://freepik.com');
            background-size: contain;
            background-repeat: no-repeat;
            background-position: center;
            opacity: 0.09;
            z-index: 1;
            pointer-events: none;
        }

        .container {
            position: relative;
            z-index: 2;
            background: rgba(17, 22, 30, 0.9);
            backdrop-filter: blur(12px);
            border: 1px solid rgba(56, 139, 253, 0.2);
            border-radius: 20px;
            padding: 30px;
            width: 92%;
            max-width: 550px;
            box-shadow: 0 12px 40px rgba(0, 0, 0, 0.7), 0 0 20px rgba(88, 166, 255, 0.05);
        }

        h1 {
            font-size: 1.6rem;
            color: #58a6ff;
            text-align: center;
            margin-bottom: 25px;
            text-transform: uppercase;
            letter-spacing: 1.5px;
            text-shadow: 0 0 10px rgba(88, 166, 255, 0.3);
        }

        h2 {
            font-size: 1.1rem;
            color: #f0883e;
            margin-bottom: 15px;
            text-transform: uppercase;
            border-left: 3px solid #f0883e;
            padding-left: 8px;
        }

        .panel {
            background: rgba(30, 37, 48, 0.5);
            border: 1px solid #30363d;
            border-radius: 12px;
            padding: 20px;
            margin-bottom: 25px;
        }

        .control-group {
            margin-bottom: 15px;
        }

        label {
            display: block;
            font-size: 0.9rem;
            margin-bottom: 8px;
            color: #8b949e;
        }

        .rpm-display {
            font-size: 2.4rem;
            font-weight: bold;
            color: #58a6ff;
            text-align: center;
            margin-bottom: 12px;
            font-family: 'Courier New', Courier, monospace;
            text-shadow: 0 0 15px rgba(88, 166, 255, 0.2);
        }

        input[type="range"] {
            width: 100%;
            height: 8px;
            border-radius: 5px;
            background: #21262d;
            outline: none;
            -webkit-appearance: none;
        }

        input[type="range"]::-webkit-slider-thumb {
            -webkit-appearance: none;
            width: 22px;
            height: 22px;
            border-radius: 50%;
            background: #58a6ff;
            cursor: pointer;
            box-shadow: 0 0 12px rgba(88, 166, 255, 0.6);
            transition: transform 0.1s;
        }

        input[type="range"]::-webkit-slider-thumb:active {
            transform: scale(1.2);
        }

        .auto-grid {
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 10px;
            margin-bottom: 15px;
        }

        .input-field input {
            width: 100%;
            background: #0d1117;
            border: 1px solid #30363d;
            border-radius: 6px;
            padding: 8px;
            color: #c9d1d9;
            text-align: center;
            font-size: 1rem;
            font-family: monospace;
        }

        .input-field input:focus {
            border-color: #58a6ff;
            outline: none;
        }

        .btn {
            width: 100%;
            background: #238636;
            color: white;
            border: none;
            border-radius: 6px;
            padding: 12px;
            font-size: 1rem;
            font-weight: bold;
            cursor: pointer;
            text-transform: uppercase;
            transition: background 0.2s, transform 0.1s;
        }

        .btn:hover { background: #2ea043; }
        .btn:active { transform: scale(0.98); }
        .btn.stop { background: #da3633; }
        .btn.stop:hover { background: #f85149; }

        .results {
            background: rgba(1, 4, 9, 0.7);
            border-radius: 12px;
            padding: 20px;
            border: 1px solid #30363d;
        }

        .result-item {
            display: flex;
            justify-content: space-between;
            padding: 10px 0;
            border-bottom: 1px solid rgba(48, 54, 61, 0.5);
            font-size: 1rem;
        }

        .result-item:last-child {
            border-bottom: none;
        }

        .label { color: #8b949e; }
        .value {
            font-weight: bold;
            color: #f0883e;
            font-family: monospace;
        }

        .status-badge {
            display: inline-block;
            padding: 4px 10px;
            border-radius: 6px;
            font-size: 0.8rem;
            font-weight: bold;
        }
        
        .status-running { background: #238636; color: white; box-shadow: 0 0 10px rgba(35,134,54,0.4); }
        .status-limit { background: #da3633; color: white; box-shadow: 0 0 10px rgba(218,54,51,0.4); }
        .status-auto { background: #8957e5; color: white; box-shadow: 0 0 10px rgba(137,87,229,0.4); }
    </style>
</head>
<body>

    <div class="container">
        <h1>Biel CDI Drag-Sim</h1>
        
        <!-- MODO MANUAL -->
        <div class="panel">
            <h2>Controle Manual</h2>
            <div class="control-group">
                <div class="rpm-display" id="rpmValue">50 RPM</div>
                <input type="range" id="rpmSlider" min="50" max="12000" step="50" value="50">
            </div>
        </div>

        <!-- MODO ACELERAÇÃO AUTOMÁTICA -->
        <div class="panel">
            <h2>Modo Puxada (Automático)</h2>
            <div class="auto-grid">
                <div class="input-field">
                    <label>Giro Inicial (RPM)</label>
                    <input type="number" id="rpmInit" value="2000" min="50" max="12000">
                </div>
                <div class="input-field">
                    <label>Tempo (Segundos)</label>
                    <input type="number" id="runTime" value="5" min="1" max="30" step="0.5">
                </div>
                <div class="input-field">
                    <label>Giro Final (RPM)</label>
                    <input type="number" id="rpmEnd" value="11500" min="50" max="12000">
                </div>
            </div>
            <button class="btn" id="btnTrigger">Iniciar Puxada 🏁</button>
        </div>

        <!-- MONITOR DE DADOS -->
        <div class="results">
            <h2>Telemetria em Tempo Real</h2>
            <div class="result-item">
                <span class="label">Estado do Sistema:</span>
                <span id="status" class="status-badge status-running">MOTOR RODANDO</span>
            </div>
            <div class="result-item">
                <span class="label">Avanço da Ignição:</span>
                <span class="value" id="avanco">--</span>
            </div>
            <div class="result-item">
                <span class="label">Tempo de 1 Volta:</span>
                <span class="value" id="tempoVolta">--</span>
            </div>
            <div class="result-item">
                <span class="label">Tempo de Atraso (Espera):</span>
                <span class="value" id="tempoEspera">--</span>
            </div>
            <div class="result-item">
                <span class="label">Tempo de Carga (Dwell):</span>
                <span class="value" id="dwell">--</span>
            </div>
        </div>
    </div>

    <script>
        const slider = document.getElementById('rpmSlider');
        const rpmValue = document.getElementById('rpmValue');
        const btnTrigger = document.getElementById('btnTrigger');
        
        let autoInterval = null;
        let modoAutomaticoAtivo = false;

        function requisitarTelemetria(rpm, isAuto = false) {
            if (!isAuto) {
                rpmValue.innerText = rpm + " RPM";
            } else {
                rpmValue.innerText = rpm + " RPM (AUTO)";
                slider.value = rpm;
            }
            fetch(`/simular?rpm=${rpm}`)
                .then(response => response.json())
                .then(data => {
                    document.getElementById('avanco').innerText = data.avanco + '°';
                    document.getElementById('tempoVolta').innerText = data.tempo_volta + ' ms';
                    document.getElementById('tempoEspera').innerText = data.tempo_espera + ' ms';
                    document.getElementById('dwell').innerText = data.dwell + ' µs';

                    const statusEl = document.getElementById('status');
                    if (rpm >= 11000) {
                        statusEl.innerText = 'LIMITADOR DE ROTAÇÃO';
                        statusEl.className = 'status-badge status-limit';
                    } else if (isAuto) {
                        statusEl.innerText = 'MODO AUTOMÁTICO';
                        statusEl.className = 'status-badge status-auto';
                    } else {
                        statusEl.innerText = 'MOTOR RODANDO';
                        statusEl.className = 'status-badge status-running';
                    }
                })
                .catch(error => console.error('Erro ao buscar telemetria:', error));
        }

        slider.addEventListener('input', () => {
            if (modoAutomaticoAtivo) return;
            const rpm = parseInt(slider.value);
            requisitarTelemetria(rpm);
        });

        btnTrigger.addEventListener('click', () => {
            if (modoAutomaticoAtivo) {
                clearInterval(autoInterval);
                modoAutomaticoAtivo = false;
                btnTrigger.innerText = 'Iniciar Puxada 🏁';
                btnTrigger.classList.remove('stop');
                return;
            }

            const rpmInit = parseInt(document.getElementById('rpmInit').value);
            const rpmEnd = parseInt(document.getElementById('rpmEnd').value);
            const runTime = parseFloat(document.getElementById('runTime').value) * 1000;
            const steps = 50;
            const stepInterval = runTime / steps;
            let currentStep = 0;

            modoAutomaticoAtivo = true;
            btnTrigger.innerText = 'Parar Puxada ⏹';
            btnTrigger.classList.add('stop');

            autoInterval = setInterval(() => {
                currentStep++;
                const progress = currentStep / steps;
                const rpm = Math.round(rpmInit + (rpmEnd - rpmInit) * progress);
                requisitarTelemetria(rpm, true);

                if (currentStep >= steps) {
                    clearInterval(autoInterval);
                    modoAutomaticoAtivo = false;
                    btnTrigger.innerText = 'Iniciar Puxada 🏁';
                    btnTrigger.classList.remove('stop');
                }
            }, stepInterval);
        });

        requisitarTelemetria(50);
    </script>
</body>
</html>
"""

@app.route('/')
def index():
    return render_template_string(HTML_INTERFACE)


@app.route('/simular')
def simular():
    rpm = request.args.get('rpm', default=1000, type=int)
    if rpm > MAX_RPM:
        rpm = MAX_RPM
    if rpm < 0:
        rpm = 0

    avanco = get_advance_from_map(rpm)

    # Tempo de uma volta do motor (ms), baseado no RPM
    tempo_volta = (60000.0 / rpm) if rpm > 0 else 0

    # Tempo de espera até o ponto de ignição, baseado no avanço calculado
    tempo_espera = (avanco / 360.0) * tempo_volta

    return jsonify({
        'avanco': round(avanco, 2),
        'tempo_volta': round(tempo_volta, 3),
        'tempo_espera': round(tempo_espera, 3),
        'dwell': DWELL_US
    })


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
