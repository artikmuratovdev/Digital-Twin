document.addEventListener("DOMContentLoaded", () => {
    const chartScript = document.getElementById("chart-data");
    const chartCanvas = document.getElementById("historyChart");
    const chartEmptyState = document.getElementById("historyChartEmpty");

    if (!chartScript || !chartCanvas || typeof Chart === "undefined") {
        return;
    }

    const chartData = JSON.parse(chartScript.textContent);
    const hasData = Array.isArray(chartData.labels) && chartData.labels.length > 0;
    if (!hasData) {
        chartCanvas.style.display = "none";
        if (chartEmptyState) {
            chartEmptyState.hidden = false;
        }
        return;
    }

    new Chart(chartCanvas, {
        type: "line",
        data: {
            labels: chartData.labels,
            datasets: [
                {
                    label: "Glyukoza",
                    data: chartData.glucose,
                    borderColor: "#1769aa",
                    backgroundColor: "rgba(23, 105, 170, 0.15)",
                    yAxisID: "yGlucose",
                    tension: 0.35,
                    borderWidth: 3,
                    pointRadius: 4,
                    pointHoverRadius: 6,
                },
                {
                    label: "BMI",
                    data: chartData.bmi,
                    borderColor: "#14916b",
                    backgroundColor: "rgba(20, 145, 107, 0.15)",
                    yAxisID: "yBmi",
                    tension: 0.35,
                    borderWidth: 3,
                    pointRadius: 4,
                    pointHoverRadius: 6,
                },
            ],
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            interaction: {
                mode: "index",
                intersect: false,
            },
            plugins: {
                legend: {
                    position: "top",
                },
            },
            scales: {
                yGlucose: {
                    type: "linear",
                    position: "left",
                    beginAtZero: false,
                    title: {
                        display: true,
                        text: "Glyukoza",
                    },
                },
                yBmi: {
                    type: "linear",
                    position: "right",
                    beginAtZero: false,
                    grid: {
                        drawOnChartArea: false,
                    },
                    title: {
                        display: true,
                        text: "BMI",
                    },
                },
                x: {
                    title: {
                        display: true,
                        text: "Sana",
                    },
                },
            },
        },
    });
});
