@props(['context' => null, 'machineId' => 'MACHINE-001'])

@php
    $timeseries = $context['timeseries'] ?? [];
    $hasData = !empty($timeseries);
@endphp

<div class="bg-white rounded-xl shadow-xs border border-slate-200 p-6 space-y-5" id="telemetryChartContainer">
    <!-- Header with Live Metric Controls & Mode Switchers -->
    <div class="flex flex-col md:flex-row justify-between items-start md:items-center gap-4 pb-3 border-b border-slate-100">
        <div>
            <div class="flex items-center space-x-2">
                <span class="inline-flex items-center px-2 py-0.5 rounded bg-emerald-50 text-emerald-700 text-[11px] font-mono font-bold border border-emerald-200">
                    <span class="w-2 h-2 rounded-full bg-emerald-500 animate-pulse mr-1.5"></span>
                    LIVE TELEMETRY STREAM
                </span>
                <h3 class="text-base font-bold text-slate-900">Multi-Function Telemetry & Physics Analyzer</h3>
                <span class="text-[10px] font-mono font-bold bg-slate-100 text-slate-700 border border-slate-200 px-2 py-0.5 rounded">
                    {{ $machineId }}
                </span>
            </div>
            <p class="text-xs text-slate-500 mt-1">Real shift-level OEE calculations, vibration/thermal physics, and defect loss breakdown</p>
        </div>

        <!-- Metric Mode Buttons -->
        <div class="flex flex-wrap items-center gap-1.5 bg-slate-100 p-1 rounded-lg border border-slate-200">
            <button type="button" onclick="switchChartMode('oee')" id="modeBtn_oee" class="text-xs font-bold px-3 py-1.5 rounded-md transition shadow-2xs bg-white text-blue-700">
                OEE & Components
            </button>
            <button type="button" onclick="switchChartMode('scrap')" id="modeBtn_scrap" class="text-xs font-semibold px-3 py-1.5 rounded-md transition text-slate-600 hover:text-slate-900">
                Scrap & Defects
            </button>
            <button type="button" onclick="switchChartMode('loss')" id="modeBtn_loss" class="text-xs font-semibold px-3 py-1.5 rounded-md transition text-slate-600 hover:text-slate-900">
                Loss Attribution
            </button>
            <button type="button" onclick="switchChartMode('physics')" id="modeBtn_physics" class="text-xs font-semibold px-3 py-1.5 rounded-md transition text-slate-600 hover:text-slate-900">
                Vibration & Thermal
            </button>
        </div>
    </div>

    <!-- Secondary Filter Bar & Horizon Controls -->
    <div class="flex flex-wrap justify-between items-center gap-3 text-xs">
        <!-- Shift Filter Tabs -->
        <div class="flex items-center space-x-1">
            <span class="text-slate-400 font-medium mr-1.5">Shift Filter:</span>
            <button type="button" onclick="filterShift('ALL')" id="shiftBtn_ALL" class="px-2.5 py-1 rounded font-bold bg-blue-600 text-white shadow-2xs">All</button>
            <button type="button" onclick="filterShift('S1')" id="shiftBtn_S1" class="px-2.5 py-1 rounded font-medium bg-slate-100 text-slate-700 hover:bg-slate-200">S1 (Morning)</button>
            <button type="button" onclick="filterShift('S2')" id="shiftBtn_S2" class="px-2.5 py-1 rounded font-medium bg-slate-100 text-slate-700 hover:bg-slate-200">S2 (Afternoon)</button>
            <button type="button" onclick="filterShift('S3')" id="shiftBtn_S3" class="px-2.5 py-1 rounded font-medium bg-slate-100 text-slate-700 hover:bg-slate-200">S3 (Night)</button>
        </div>

        <!-- Production Stream Controls & Export -->
        <div class="flex items-center space-x-2">
            <button type="button" onclick="jumpToAnomaly()" id="btnJumpAnomaly" class="inline-flex items-center space-x-1 text-xs font-bold bg-amber-50 hover:bg-amber-100 text-amber-800 px-2.5 py-1.5 rounded-lg border border-amber-300 transition">
                <span>⚠️</span>
                <span>Jump to Incident Shift</span>
            </button>
            <button type="button" onclick="refreshTelemetryData()" id="btnRefresh" class="inline-flex items-center space-x-1 text-xs font-bold bg-white hover:bg-slate-50 text-slate-700 px-2.5 py-1.5 rounded-lg border border-slate-200 transition shadow-2xs">
                <span id="refreshSpinner">🔄</span>
                <span>Refresh Data</span>
            </button>
            <button type="button" onclick="exportTimeseriesCSV()" class="text-xs font-semibold bg-white hover:bg-slate-50 text-slate-700 px-3 py-1.5 rounded-lg border border-slate-200 transition shadow-2xs">
                Export CSV
            </button>
        </div>
    </div>

    <!-- Canvas Chart Container with Click Instruction -->
    <div class="relative w-full h-72 bg-slate-50/50 rounded-xl p-2 border border-slate-100">
        <div class="absolute top-3 right-4 z-10 text-[10px] font-mono text-slate-400 bg-white/80 backdrop-blur-xs px-2 py-0.5 rounded border border-slate-200/60">
            Click any point on chart to inspect shift telemetry
        </div>
        <canvas id="telemetryCanvas" class="w-full h-full cursor-crosshair"></canvas>
    </div>

    <!-- Interactive Operation Timeline & Shift Telemetry Inspector -->
    <div class="bg-slate-50 border border-slate-200/80 rounded-xl p-4 space-y-3">
        <div class="flex justify-between items-center">
            <div class="flex items-center space-x-2">
                <span class="text-xs font-bold text-slate-700 uppercase tracking-wider font-mono">
                    Shift Telemetry Inspector
                </span>
                <span id="anomalyTag" class="hidden text-[10px] font-bold bg-red-100 text-red-700 px-2 py-0.5 rounded border border-red-300">
                    ANOMALY BREACH
                </span>
            </div>
            <div class="flex items-center space-x-2">
                <button type="button" onclick="stepShift(-1)" class="text-xs font-bold bg-white px-2 py-0.5 rounded border border-slate-200 text-slate-700 hover:bg-slate-100">◀ Prev Shift</button>
                <span id="scrubberLabel" class="text-xs font-mono font-bold text-blue-600 bg-blue-50 px-2.5 py-0.5 rounded border border-blue-200">
                    Latest Shift
                </span>
                <button type="button" onclick="stepShift(1)" class="text-xs font-bold bg-white px-2 py-0.5 rounded border border-slate-200 text-slate-700 hover:bg-slate-100">Next Shift ▶</button>
            </div>
        </div>

        <!-- Range Slider -->
        <input type="range" id="telemetryScrubber" min="0" max="10" value="10" oninput="onScrubChange(this.value)" class="w-full h-2 bg-slate-200 rounded-lg appearance-none cursor-pointer accent-blue-600">

        <!-- Inspector Telemetry Metrics Grid -->
        <div class="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-2.5 pt-1" id="scrubberDetails">
            <div class="bg-white p-2.5 rounded-lg border border-slate-200 text-center shadow-2xs">
                <span class="text-[10px] text-slate-400 font-semibold uppercase block">OEE (Avail × Perf × Qual)</span>
                <span class="text-sm font-black text-slate-900" id="detail_oee">--</span>
            </div>
            <div class="bg-white p-2.5 rounded-lg border border-slate-200 text-center shadow-2xs">
                <span class="text-[10px] text-slate-400 font-semibold uppercase block">Good / Total Units</span>
                <span class="text-sm font-black text-slate-900 font-mono" id="detail_units">--</span>
            </div>
            <div class="bg-white p-2.5 rounded-lg border border-slate-200 text-center shadow-2xs">
                <span class="text-[10px] text-slate-400 font-semibold uppercase block">Scrap Rate %</span>
                <span class="text-sm font-black text-slate-900" id="detail_scrap">--</span>
            </div>
            <div class="bg-white p-2.5 rounded-lg border border-slate-200 text-center shadow-2xs">
                <span class="text-[10px] text-slate-400 font-semibold uppercase block">Unplanned Downtime</span>
                <span class="text-sm font-black text-slate-900" id="detail_downtime">--</span>
            </div>
            <div class="bg-white p-2.5 rounded-lg border border-slate-200 text-center shadow-2xs">
                <span class="text-[10px] text-slate-400 font-semibold uppercase block">Vibration RMS</span>
                <span class="text-sm font-black text-slate-900 font-mono" id="detail_vibration">--</span>
            </div>
            <div class="bg-white p-2.5 rounded-lg border border-slate-200 text-center shadow-2xs">
                <span class="text-[10px] text-slate-400 font-semibold uppercase block">Shift Lead / Tech</span>
                <span class="text-xs font-bold text-slate-800 truncate block mt-0.5" id="detail_operator">--</span>
            </div>
        </div>
    </div>
</div>

<script>
let rawTimeseriesData = @json($timeseries);
let currentMode = 'oee';
let currentShiftFilter = 'ALL';
let chartInstance = null;

function getFilteredData() {
    if (currentShiftFilter === 'ALL') return rawTimeseriesData;
    return rawTimeseriesData.filter(d => d.shift_id === currentShiftFilter);
}

function initTelemetryChart() {
    const canvas = document.getElementById('telemetryCanvas');
    if (!canvas || !window.Chart) return;

    const data = getFilteredData();
    const scrubber = document.getElementById('telemetryScrubber');
    if (scrubber) {
        scrubber.max = Math.max(0, data.length - 1);
        scrubber.value = scrubber.max;
    }

    if (data.length > 0) {
        updateScrubberDetails(data[data.length - 1]);
    }
    renderChart();
}

function renderChart() {
    const canvas = document.getElementById('telemetryCanvas');
    if (!canvas || !window.Chart) return;
    const ctx = canvas.getContext('2d');

    if (chartInstance) {
        chartInstance.destroy();
    }

    const data = getFilteredData();
    const labels = data.map(d => d.timestamp_label);

    let datasets = [];
    let scalesConfig = {
        x: {
            grid: { display: false },
            ticks: { font: { size: 10, family: 'Inter' }, color: '#64748b' }
        },
        y: {
            grid: { color: '#f1f5f9' },
            ticks: { font: { size: 10, family: 'Inter' }, color: '#64748b' }
        }
    };

    if (currentMode === 'oee') {
        datasets = [
            {
                label: 'OEE (%)',
                data: data.map(d => d.oee_pct),
                borderColor: '#2563eb',
                backgroundColor: 'rgba(37, 99, 235, 0.08)',
                borderWidth: 2.5,
                fill: true,
                tension: 0.3,
                pointRadius: data.map(d => d.has_anomaly ? 6 : 3),
                pointBackgroundColor: data.map(d => d.has_anomaly ? '#ef4444' : '#2563eb'),
                pointBorderColor: '#fff',
                pointBorderWidth: 2
            },
            {
                label: 'Availability (%)',
                data: data.map(d => d.availability_pct),
                borderColor: '#10b981',
                borderWidth: 1.5,
                borderDash: [3, 3],
                tension: 0.3,
                pointRadius: 0
            },
            {
                label: 'Performance (%)',
                data: data.map(d => d.performance_pct),
                borderColor: '#f59e0b',
                borderWidth: 1.5,
                borderDash: [3, 3],
                tension: 0.3,
                pointRadius: 0
            },
            {
                label: 'Quality (%)',
                data: data.map(d => d.quality_pct),
                borderColor: '#8b5cf6',
                borderWidth: 1.5,
                borderDash: [3, 3],
                tension: 0.3,
                pointRadius: 0
            },
            {
                label: 'Target Baseline (85%)',
                data: data.map(() => 85.0),
                borderColor: '#94a3b8',
                borderWidth: 1.5,
                borderDash: [6, 4],
                pointRadius: 0,
                fill: false
            }
        ];
        scalesConfig.y.min = 40;
        scalesConfig.y.max = 100;
        scalesConfig.y.title = { display: true, text: 'Percentage (%)', font: { size: 10, weight: 'bold' } };

    } else if (currentMode === 'scrap') {
        datasets = [
            {
                type: 'line',
                label: 'Scrap Rate (%)',
                data: data.map(d => d.scrap_rate_pct),
                borderColor: '#ef4444',
                backgroundColor: 'rgba(239, 68, 68, 0.1)',
                borderWidth: 2.5,
                fill: true,
                tension: 0.3,
                pointRadius: data.map(d => d.has_anomaly ? 6 : 3),
                pointBackgroundColor: data.map(d => d.has_anomaly ? '#dc2626' : '#ef4444'),
                yAxisID: 'y'
            },
            {
                type: 'bar',
                label: 'Scrap Units (Rejects)',
                data: data.map(d => d.rejected_units),
                backgroundColor: 'rgba(239, 68, 68, 0.25)',
                borderRadius: 4,
                yAxisID: 'y1'
            },
            {
                type: 'line',
                label: 'Max Tolerance Limit (4%)',
                data: data.map(() => 4.0),
                borderColor: '#f87171',
                borderDash: [4, 4],
                borderWidth: 1.5,
                pointRadius: 0,
                yAxisID: 'y'
            }
        ];
        scalesConfig.y.title = { display: true, text: 'Scrap Rate (%)', font: { size: 10, weight: 'bold' } };
        scalesConfig.y1 = {
            position: 'right',
            grid: { display: false },
            title: { display: true, text: 'Scrap Units', font: { size: 10, weight: 'bold' } },
            ticks: { font: { size: 10 } }
        };

    } else if (currentMode === 'loss') {
        datasets = [
            {
                type: 'bar',
                label: 'Availability Loss (Unplanned Mins)',
                data: data.map(d => d.downtime_min),
                backgroundColor: '#f87171',
                stack: 'loss',
                borderRadius: 4
            },
            {
                type: 'bar',
                label: 'Cycle Throttling Loss (Units)',
                data: data.map(d => Math.max(0, 1000 - d.total_units)),
                backgroundColor: '#fbbf24',
                stack: 'loss',
                borderRadius: 4
            }
        ];
        scalesConfig.y.title = { display: true, text: 'Attributed Loss Magnitude', font: { size: 10, weight: 'bold' } };

    } else if (currentMode === 'physics') {
        datasets = [
            {
                label: 'Vibration RMS (mm/s)',
                data: data.map(d => d.vibration_mm_s),
                borderColor: '#dc2626',
                borderWidth: 2,
                tension: 0.3,
                pointRadius: 3,
                yAxisID: 'y'
            },
            {
                label: 'ISO Warning Limit (4.5 mm/s)',
                data: data.map(() => 4.5),
                borderColor: '#ea580c',
                borderDash: [4, 4],
                borderWidth: 1.5,
                pointRadius: 0,
                yAxisID: 'y'
            },
            {
                label: 'Spindle Temperature (°C)',
                data: data.map(d => d.temperature_c),
                borderColor: '#2563eb',
                borderWidth: 2,
                tension: 0.3,
                pointRadius: 3,
                yAxisID: 'y1'
            }
        ];
        scalesConfig.y.title = { display: true, text: 'Vibration (mm/s)', font: { size: 10, weight: 'bold' } };
        scalesConfig.y1 = {
            position: 'right',
            grid: { display: false },
            title: { display: true, text: 'Temperature (°C)', font: { size: 10, weight: 'bold' } },
            ticks: { font: { size: 10 } }
        };
    }

    chartInstance = new Chart(ctx, {
        type: 'line',
        data: { labels, datasets },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            interaction: {
                mode: 'index',
                intersect: false,
            },
            onClick: (e, elements) => {
                if (elements && elements.length > 0) {
                    const clickedIndex = elements[0].index;
                    const scrubber = document.getElementById('telemetryScrubber');
                    if (scrubber) {
                        scrubber.value = clickedIndex;
                        onScrubChange(clickedIndex);
                    }
                }
            },
            plugins: {
                legend: {
                    position: 'top',
                    labels: {
                        boxWidth: 10,
                        font: { size: 11, family: 'Inter', weight: 'bold' },
                        padding: 12
                    }
                },
                tooltip: {
                    backgroundColor: 'rgba(15, 23, 42, 0.95)',
                    titleFont: { size: 12, family: 'Inter', weight: 'bold' },
                    bodyFont: { size: 11, family: 'Inter' },
                    padding: 10,
                    cornerRadius: 8
                }
            },
            scales: scalesConfig
        }
    });
}

function switchChartMode(mode) {
    currentMode = mode;
    ['oee', 'scrap', 'loss', 'physics'].forEach(m => {
        const btn = document.getElementById(`modeBtn_${m}`);
        if (btn) {
            if (m === mode) {
                btn.className = 'text-xs font-bold px-3 py-1.5 rounded-md transition shadow-2xs bg-white text-blue-700';
            } else {
                btn.className = 'text-xs font-semibold px-3 py-1.5 rounded-md transition text-slate-600 hover:text-slate-900';
            }
        }
    });
    renderChart();
}

function filterShift(shift) {
    currentShiftFilter = shift;
    ['ALL', 'S1', 'S2', 'S3'].forEach(s => {
        const btn = document.getElementById(`shiftBtn_${s}`);
        if (btn) {
            if (s === shift) {
                btn.className = 'px-2.5 py-1 rounded font-bold bg-blue-600 text-white shadow-2xs';
            } else {
                btn.className = 'px-2.5 py-1 rounded font-medium bg-slate-100 text-slate-700 hover:bg-slate-200';
            }
        }
    });
    const data = getFilteredData();
    const scrubber = document.getElementById('telemetryScrubber');
    if (scrubber) {
        scrubber.max = Math.max(0, data.length - 1);
        scrubber.value = scrubber.max;
    }
    if (data.length > 0) {
        updateScrubberDetails(data[data.length - 1]);
    }
    renderChart();
}

function onScrubChange(val) {
    const data = getFilteredData();
    const idx = parseInt(val, 10);
    const item = data[idx];
    if (item) {
        updateScrubberDetails(item);
    }
}

function stepShift(direction) {
    const scrubber = document.getElementById('telemetryScrubber');
    if (!scrubber) return;
    const current = parseInt(scrubber.value, 10);
    const max = parseInt(scrubber.max, 10);
    const target = Math.max(0, Math.min(max, current + direction));
    scrubber.value = target;
    onScrubChange(target);
}

function jumpToAnomaly() {
    const data = getFilteredData();
    const anomalyIndex = data.findIndex(d => d.has_anomaly);
    if (anomalyIndex !== -1) {
        const scrubber = document.getElementById('telemetryScrubber');
        if (scrubber) {
            scrubber.value = anomalyIndex;
            onScrubChange(anomalyIndex);
        }
    }
}

function updateScrubberDetails(item) {
    if (!item) return;
    const label = document.getElementById('scrubberLabel');
    if (label) label.innerText = `${item.timestamp_label} • ${item.shift_name} Shift`;

    const anomalyTag = document.getElementById('anomalyTag');
    if (anomalyTag) {
        if (item.has_anomaly) {
            anomalyTag.classList.remove('hidden');
        } else {
            anomalyTag.classList.add('hidden');
        }
    }

    const oeeEl = document.getElementById('detail_oee');
    if (oeeEl) {
        oeeEl.innerText = `${item.oee_pct}%`;
        oeeEl.className = item.oee_pct >= 85 ? 'text-sm font-black text-emerald-600' : 'text-sm font-black text-amber-600';
    }

    const unitsEl = document.getElementById('detail_units');
    if (unitsEl) unitsEl.innerText = `${item.good_units} / ${item.total_units}`;

    const scrapEl = document.getElementById('detail_scrap');
    if (scrapEl) {
        scrapEl.innerText = `${item.scrap_rate_pct}% (${item.rejected_units} units)`;
        scrapEl.className = item.scrap_rate_pct <= 4.0 ? 'text-sm font-black text-slate-900' : 'text-sm font-black text-red-600';
    }

    const dtEl = document.getElementById('detail_downtime');
    if (dtEl) dtEl.innerText = `${item.downtime_min} min`;

    const vibEl = document.getElementById('detail_vibration');
    if (vibEl) {
        vibEl.innerText = `${item.vibration_mm_s} mm/s`;
        vibEl.className = item.vibration_mm_s > 4.5 ? 'text-sm font-black text-red-600' : 'text-sm font-black text-slate-900';
    }

    const opEl = document.getElementById('detail_operator');
    if (opEl) opEl.innerText = item.operator;
}

function refreshTelemetryData() {
    const spinner = document.getElementById('refreshSpinner');
    if (spinner) spinner.classList.add('animate-spin');

    fetch(`http://127.0.0.1:8080/machine/context?machine_id={{ $machineId }}&days=14`)
        .then(res => res.json())
        .then(data => {
            if (data.timeseries) {
                rawTimeseriesData = data.timeseries;
                initTelemetryChart();
            }
        })
        .catch(err => {
            console.warn('Live refresh fallback:', err);
        })
        .finally(() => {
            setTimeout(() => {
                if (spinner) spinner.classList.remove('animate-spin');
            }, 500);
        });
}

function exportTimeseriesCSV() {
    const data = getFilteredData();
    if (!data.length) return;
    const headers = ["Date", "Shift", "OEE (%)", "Availability (%)", "Performance (%)", "Quality (%)", "Scrap Rate (%)", "Total Units", "Good Units", "Rejects", "Downtime (min)", "Vibration (mm/s)", "Temp (C)", "Operator"];
    const rows = data.map(d => [
        d.date, d.shift_id, d.oee_pct, d.availability_pct, d.performance_pct, d.quality_pct, d.scrap_rate_pct, d.total_units, d.good_units, d.rejected_units, d.downtime_min, d.vibration_mm_s, d.temperature_c, `"${d.operator}"`
    ]);

    const csvContent = "data:text/csv;charset=utf-8," + [headers.join(","), ...rows.map(e => e.join(","))].join("\n");
    const encodedUri = encodeURI(csvContent);
    const link = document.createElement("a");
    link.setAttribute("href", encodedUri);
    link.setAttribute("download", `telemetry_audit_${data[0].date}_${data[data.length-1].date}.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
}

// Initial boot
document.addEventListener('DOMContentLoaded', () => {
    initTelemetryChart();
});
</script>
