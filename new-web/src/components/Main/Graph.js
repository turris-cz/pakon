import React, { useContext, useState, useMemo } from "react";
import { PakonContext, formatBytes } from "../../context/PakonContext";
import { Chart as ChartJS, ArcElement, Tooltip, Legend } from "chart.js";
import { Pie } from "react-chartjs-2";

ChartJS.register(ArcElement, Tooltip, Legend);

// Harmonious color palette for modern design
const BASE_COLORS = [
    "#4f46e5", // Indigo
    "#06b6d4", // Cyan
    "#10b981", // Emerald
    "#f59e0b", // Amber
    "#ec4899", // Pink
    "#8b5cf6", // Purple
    "#ef4444", // Red
    "#3b82f6"  // Blue
];
const OTHER_COLOR = "#6b7280"; // Gray

export default function Graph() {
    const { filteredData } = useContext(PakonContext);
    const [dimension, setDimension] = useState("protocol"); // protocol | client | hostname
    const [metric, setMetric] = useState("total"); // total | sent | received

    const chartData = useMemo(() => {
        if (!filteredData || filteredData.length === 0) {
            return {
                labels: ["No Data"],
                datasets: [{
                    data: [1],
                    backgroundColor: ["#e5e7eb"],
                    borderWidth: 1
                }]
            };
        }

        const groupings = {};

        filteredData.forEach(flow => {
            // Determine grouping key
            let key = "Unknown";
            if (dimension === "protocol") {
                const portVal = flow[4] || "";
                const lower = portVal.toLowerCase();
                if (lower.includes("https") || lower === "443") key = "HTTPS";
                else if (lower.includes("http") || lower === "80") key = "HTTP";
                else if (lower.includes("dns") || lower === "53") key = "DNS";
                else if (lower.includes("ssh") || lower === "22") key = "SSH";
                else key = portVal ? portVal.toUpperCase() : "Other";
            } else if (dimension === "client") {
                key = flow[2] || "Unknown Client";
            } else if (dimension === "hostname") {
                key = flow[3] || "Direct IP / Unknown";
            }

            // Determine metric value
            let value = 0;
            if (metric === "total") {
                value = (flow[6] || 0) + (flow[7] || 0);
            } else if (metric === "sent") {
                value = flow[6] || 0;
            } else if (metric === "received") {
                value = flow[7] || 0;
            }

            groupings[key] = (groupings[key] || 0) + value;
        });

        // Convert to sorted array
        let sortedGroups = Object.entries(groupings)
            .map(([label, val]) => ({ label, val }))
            .sort((a, b) => b.val - a.val);

        // Group minor entries into "Others" if too many labels (keep top 6)
        const limit = 6;
        let finalLabels = [];
        let finalVals = [];
        let finalColors = [];

        if (sortedGroups.length > limit) {
            const top = sortedGroups.slice(0, limit - 1);
            const minor = sortedGroups.slice(limit - 1);
            const othersVal = minor.reduce((sum, item) => sum + item.val, 0);

            top.forEach((item, idx) => {
                finalLabels.push(item.label);
                finalVals.push(item.val);
                finalColors.push(BASE_COLORS[idx % BASE_COLORS.length]);
            });

            finalLabels.push("Others");
            finalVals.push(othersVal);
            finalColors.push(OTHER_COLOR);
        } else {
            sortedGroups.forEach((item, idx) => {
                finalLabels.push(item.label);
                finalVals.push(item.val);
                finalColors.push(BASE_COLORS[idx % BASE_COLORS.length]);
            });
        }

        return {
            labels: finalLabels,
            datasets: [{
                data: finalVals,
                backgroundColor: finalColors,
                borderColor: finalColors.map(c => c + "22"), // Subtle borders
                borderWidth: 1
            }]
        };
    }, [filteredData, dimension, metric]);

    const chartOptions = {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
            legend: {
                position: "right",
                labels: {
                    font: {
                        family: "Inter, sans-serif",
                        size: 11
                    },
                    boxWidth: 12
                }
            },
            tooltip: {
                callbacks: {
                    label: function (context) {
                        let label = context.label || "";
                        if (label) {
                            label += ": ";
                        }
                        if (context.raw !== null) {
                            label += formatBytes(context.raw);
                        }
                        return label;
                    }
                }
            }
        }
    };

    const totalVolume = useMemo(() => {
        let sum = 0;
        filteredData.forEach(flow => {
            if (metric === "total") sum += (flow[6] || 0) + (flow[7] || 0);
            else if (metric === "sent") sum += (flow[6] || 0);
            else if (metric === "received") sum += (flow[7] || 0);
        });
        return formatBytes(sum);
    }, [filteredData, metric]);

    return (
        <div className="flex flex-col md:flex-row px-6 py-6 bg-white dark:bg-gray-800 transition-colors duration-300">
            {/* Visual Control Board */}
            <div className="w-full md:w-1/3 flex flex-col space-y-4 pr-0 md:pr-6 border-b md:border-b-0 md:border-r border-gray-100 dark:border-gray-700 pb-4 md:pb-0 mb-4 md:mb-0">
                <h4 className="text-sm font-semibold text-gray-700 dark:text-gray-200">
                    Visualization Settings
                </h4>
                
                <div>
                    <label htmlFor="dimension-select" className="block text-xs font-medium text-gray-500 dark:text-gray-400 mb-1">
                        Group By
                    </label>
                    <select
                        id="dimension-select"
                        value={dimension}
                        onChange={(e) => setDimension(e.target.value)}
                        className="block w-full text-sm border-gray-300 dark:border-gray-650 rounded-md bg-white dark:bg-gray-750 text-gray-700 dark:text-gray-200 focus:outline-none focus:ring-indigo-500"
                    >
                        <option value="protocol">Protocol</option>
                        <option value="client">Client</option>
                        <option value="hostname">Hostname</option>
                    </select>
                </div>

                <div>
                    <label htmlFor="metric-select" className="block text-xs font-medium text-gray-500 dark:text-gray-400 mb-1">
                        Metric Volume
                    </label>
                    <select
                        id="metric-select"
                        value={metric}
                        onChange={(e) => setMetric(e.target.value)}
                        className="block w-full text-sm border-gray-300 dark:border-gray-650 rounded-md bg-white dark:bg-gray-750 text-gray-700 dark:text-gray-200 focus:outline-none focus:ring-indigo-500"
                    >
                        <option value="total">Total Traffic</option>
                        <option value="sent">Sent Bytes</option>
                        <option value="received">Received Bytes</option>
                    </select>
                </div>

                <div className="pt-2">
                    <span className="block text-xs font-medium text-gray-500 dark:text-gray-400">
                        Total Volume in Selection
                    </span>
                    <span className="text-xl font-bold text-indigo-600 dark:text-indigo-400">
                        {totalVolume}
                    </span>
                </div>
            </div>

            {/* Chart Canvas */}
            <div className="w-full md:w-2/3 flex justify-center items-center h-[350px]">
                {filteredData && filteredData.length > 0 ? (
                    <Pie data={chartData} options={chartOptions} />
                ) : (
                    <span className="text-sm text-gray-400">No data available to plot.</span>
                )}
            </div>
        </div>
    );
}
