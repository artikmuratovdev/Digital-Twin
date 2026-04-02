function getCookie(name) {
    const value = `; ${document.cookie}`;
    const parts = value.split(`; ${name}=`);
    if (parts.length === 2) {
        return parts.pop().split(";").shift();
    }
    return "";
}

function setupStrictNumericInputs() {
    const numericInputs = document.querySelectorAll('input[data-numeric-strict="true"]');
    numericInputs.forEach((input) => {
        input.addEventListener("keydown", (event) => {
            if (["e", "E", "+", "-"].includes(event.key)) {
                event.preventDefault();
            }
        });

        input.addEventListener("paste", (event) => {
            const pasted = event.clipboardData?.getData("text") || "";
            if (/[a-zA-Z+\-]/.test(pasted)) {
                event.preventDefault();
            }
        });

        input.addEventListener("input", () => {
            let value = input.value.replace(/[^0-9.]/g, "");
            const firstDotIndex = value.indexOf(".");
            if (firstDotIndex !== -1) {
                value =
                    value.slice(0, firstDotIndex + 1) +
                    value.slice(firstDotIndex + 1).replace(/\./g, "");
            }
            input.value = value;

            const numericValue = Number(value);
            const min = Number(input.min);
            const max = Number(input.max);
            if (!value) {
                input.setCustomValidity("");
                return;
            }
            if (!Number.isFinite(numericValue) || numericValue === 0 || numericValue < min || numericValue > max) {
                input.setCustomValidity(`${input.min} dan ${input.max} gacha qiymat kiriting. 0 qabul qilinmaydi.`);
            } else {
                input.setCustomValidity("");
            }
        });
    });
}

document.addEventListener("DOMContentLoaded", () => {
    setupStrictNumericInputs();

    const patientId = document.body.dataset.patientId;
    if (!patientId) {
        return;
    }

    const simulationChartScript = document.getElementById("simulation-chart-data");
    const simulationChartHost = document.getElementById("simulationChart");
    const simulationChartEmpty = document.getElementById("simulationChartEmpty");
    if (simulationChartScript && simulationChartHost) {
        const simulationChartData = JSON.parse(simulationChartScript.textContent);
        const hasSimulationData =
            Array.isArray(simulationChartData.labels) && simulationChartData.labels.length > 0;

        if (!hasSimulationData) {
            simulationChartHost.style.display = "none";
            if (simulationChartEmpty) {
                simulationChartEmpty.hidden = false;
            }
        } else {
            const labels = simulationChartData.labels;
            const oldRiskValues = simulationChartData.old_risk.map(Number);
            const newRiskValues = simulationChartData.new_risk.map(Number);
            const differenceValues = simulationChartData.difference.map(Number);
            const series = [{ label: "Farq", color: "#497fd1", values: differenceValues, dashed: true }];
            const allValues = differenceValues;
            const minValue = Math.min(...allValues);
            const maxValue = Math.max(...allValues);
            const yPadding = Math.max((maxValue - minValue) * 0.15, 2);
            const yMin = Math.floor(minValue - yPadding);
            const yMax = Math.ceil(maxValue + yPadding);
            const width = 960;
            const height = 320;
            const padding = { top: 20, right: 24, bottom: 56, left: 56 };
            const plotWidth = width - padding.left - padding.right;
            const plotHeight = height - padding.top - padding.bottom;
            const ns = "http://www.w3.org/2000/svg";

            const toX = (index) => {
                if (labels.length === 1) {
                    return padding.left + plotWidth / 2;
                }
                return padding.left + (plotWidth * index) / (labels.length - 1);
            };
            const toY = (value) => {
                if (yMax === yMin) {
                    return padding.top + plotHeight / 2;
                }
                return padding.top + plotHeight - ((value - yMin) / (yMax - yMin)) * plotHeight;
            };

            simulationChartHost.innerHTML = "";

            const legend = document.createElement("div");
            legend.className = "simulation-chart-legend";
            series.forEach((item) => {
                const legendItem = document.createElement("div");
                legendItem.className = "simulation-chart-legend-item";
                const swatch = document.createElement("span");
                swatch.className = "simulation-chart-swatch";
                swatch.style.backgroundColor = item.color;
                swatch.style.color = item.color;
                if (item.dashed) {
                    swatch.classList.add("simulation-chart-swatch-dashed");
                }
                const text = document.createElement("span");
                text.textContent = item.label;
                legendItem.appendChild(swatch);
                legendItem.appendChild(text);
                legend.appendChild(legendItem);
            });
            simulationChartHost.appendChild(legend);

            const tooltip = document.createElement("div");
            tooltip.className = "simulation-chart-tooltip";
            tooltip.hidden = true;
            simulationChartHost.appendChild(tooltip);

            const svg = document.createElementNS(ns, "svg");
            svg.setAttribute("viewBox", `0 0 ${width} ${height}`);
            svg.setAttribute("class", "simulation-chart-svg");
            svg.setAttribute("role", "img");
            svg.setAttribute("aria-label", "Simulyatsiya tarix diagrammasi");

            for (let i = 0; i < 5; i += 1) {
                const value = yMin + ((yMax - yMin) * i) / 4;
                const y = padding.top + plotHeight - (plotHeight * i) / 4;

                const gridLine = document.createElementNS(ns, "line");
                gridLine.setAttribute("x1", String(padding.left));
                gridLine.setAttribute("y1", String(y));
                gridLine.setAttribute("x2", String(width - padding.right));
                gridLine.setAttribute("y2", String(y));
                gridLine.setAttribute("class", "simulation-chart-grid");
                svg.appendChild(gridLine);

                const yLabel = document.createElementNS(ns, "text");
                yLabel.setAttribute("x", String(padding.left - 10));
                yLabel.setAttribute("y", String(y + 4));
                yLabel.setAttribute("text-anchor", "end");
                yLabel.setAttribute("class", "simulation-chart-axis-label");
                yLabel.textContent = `${value.toFixed(0)}%`;
                svg.appendChild(yLabel);
            }

            labels.forEach((label, index) => {
                const x = toX(index);

                const tick = document.createElementNS(ns, "line");
                tick.setAttribute("x1", String(x));
                tick.setAttribute("y1", String(height - padding.bottom));
                tick.setAttribute("x2", String(x));
                tick.setAttribute("y2", String(height - padding.bottom + 6));
                tick.setAttribute("class", "simulation-chart-tick");
                svg.appendChild(tick);

                const xLabel = document.createElementNS(ns, "text");
                xLabel.setAttribute("x", String(x));
                xLabel.setAttribute("y", String(height - 20));
                xLabel.setAttribute("text-anchor", "middle");
                xLabel.setAttribute("class", "simulation-chart-axis-label");
                xLabel.textContent = label.slice(5);
                svg.appendChild(xLabel);
            });

            const axisX = document.createElementNS(ns, "line");
            axisX.setAttribute("x1", String(padding.left));
            axisX.setAttribute("y1", String(height - padding.bottom));
            axisX.setAttribute("x2", String(width - padding.right));
            axisX.setAttribute("y2", String(height - padding.bottom));
            axisX.setAttribute("class", "simulation-chart-axis");
            svg.appendChild(axisX);

            const axisY = document.createElementNS(ns, "line");
            axisY.setAttribute("x1", String(padding.left));
            axisY.setAttribute("y1", String(padding.top));
            axisY.setAttribute("x2", String(padding.left));
            axisY.setAttribute("y2", String(height - padding.bottom));
            axisY.setAttribute("class", "simulation-chart-axis");
            svg.appendChild(axisY);

            series.forEach((item) => {
                const polyline = document.createElementNS(ns, "polyline");
                const points = item.values.map((value, index) => `${toX(index)},${toY(Number(value))}`).join(" ");
                polyline.setAttribute("points", points);
                polyline.setAttribute("fill", "none");
                polyline.setAttribute("stroke", item.color);
                polyline.setAttribute("stroke-width", item.dashed ? "2.5" : "3.5");
                polyline.setAttribute("stroke-linecap", "round");
                polyline.setAttribute("stroke-linejoin", "round");
                if (item.dashed) {
                    polyline.setAttribute("stroke-dasharray", "8 6");
                }
                svg.appendChild(polyline);

                item.values.forEach((value, index) => {
                    const pointX = toX(index);
                    const pointY = toY(Number(value));

                    const hitArea = document.createElementNS(ns, "circle");
                    hitArea.setAttribute("cx", String(pointX));
                    hitArea.setAttribute("cy", String(pointY));
                    hitArea.setAttribute("r", "18");
                    hitArea.setAttribute("fill", "#ffffff");
                    hitArea.setAttribute("fill-opacity", "0.001");
                    hitArea.setAttribute("class", "simulation-chart-hit-area");

                    const circle = document.createElementNS(ns, "circle");
                    circle.setAttribute("cx", String(pointX));
                    circle.setAttribute("cy", String(pointY));
                    circle.setAttribute("r", item.dashed ? "5" : "6");
                    circle.setAttribute("fill", item.color);
                    circle.setAttribute("class", "simulation-chart-point");

                    const showTooltip = (event) => {
                        const differenceValue = differenceValues[index];
                        const differenceClass =
                            differenceValue > 0
                                ? "simulation-chart-tooltip-diff-positive"
                                : "simulation-chart-tooltip-diff-negative";
                        tooltip.hidden = false;
                        tooltip.innerHTML =
                            `<strong>${labels[index]}</strong>` +
                            `<span>Eski risk: ${oldRiskValues[index].toFixed(2)}%</span>` +
                            `<span>Yangi risk: ${newRiskValues[index].toFixed(2)}%</span>` +
                            `<span class="${differenceClass}">Farq: ${differenceValue.toFixed(2)}%</span>`;

                        const hostRect = simulationChartHost.getBoundingClientRect();
                        const tooltipWidth = 190;
                        const x = Math.min(
                            Math.max(event.clientX - hostRect.left + 14, 8),
                            hostRect.width - tooltipWidth
                        );
                        const y = Math.max(event.clientY - hostRect.top - 88, 8);
                        tooltip.style.left = `${x}px`;
                        tooltip.style.top = `${y}px`;
                    };

                    const hideTooltip = () => {
                        tooltip.hidden = true;
                    };

                    hitArea.addEventListener("mouseenter", showTooltip);
                    hitArea.addEventListener("mousemove", showTooltip);
                    hitArea.addEventListener("mouseleave", hideTooltip);
                    circle.addEventListener("mouseenter", showTooltip);
                    circle.addEventListener("mousemove", showTooltip);
                    circle.addEventListener("mouseleave", hideTooltip);
                    svg.appendChild(hitArea);
                    svg.appendChild(circle);
                });
            });

            simulationChartHost.addEventListener("mouseleave", () => {
                tooltip.hidden = true;
            });

            simulationChartHost.appendChild(svg);
        }
    }

    const summaryBtn = document.getElementById("summaryBtn");
    const summaryOutput = document.getElementById("summaryOutput");
    const loadSummary = async () => {
        if (!summaryOutput) {
            return;
        }

        summaryOutput.textContent = "AI xulosa tayyorlanmoqda...";
        try {
            const response = await fetch(`/ai/summary/${patientId}/`);
            const data = await response.json();
            summaryOutput.textContent = data.summary || "Xulosa olinmadi.";
        } catch (error) {
            summaryOutput.textContent = "AI xulosa vaqtincha mavjud emas.";
        }
    };

    if (summaryBtn && summaryOutput) {
        summaryBtn.addEventListener("click", loadSummary);
    }

    void loadSummary();

    const chatForm = document.getElementById("chatForm");
    const chatOutput = document.getElementById("chatOutput");
    if (chatForm && chatOutput) {
        chatForm.addEventListener("submit", async (event) => {
            event.preventDefault();
            chatOutput.textContent = "AI javob tayyorlanmoqda...";
            const formData = new FormData(chatForm);

            try {
                const response = await fetch(`/ai/chat/${patientId}/`, {
                    method: "POST",
                    headers: {
                        "X-CSRFToken": getCookie("csrftoken"),
                    },
                    body: new URLSearchParams(formData),
                });
                const data = await response.json();
                chatOutput.textContent = data.reply || "Javob olinmadi.";
            } catch (error) {
                chatOutput.textContent = "AI chat vaqtincha ishlamayapti.";
            }
        });
    }
});
