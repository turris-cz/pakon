import React, { createContext, useState, useEffect, useMemo } from "react";

export const PakonContext = createContext();

// Format helpers
export function formatBytes(bytes) {
    const BASE = 1024;
    const SIZES = ["B", "KiB", "MiB", "GiB", "TiB", "PiB"];
    if (!bytes || Number(bytes) === 0) return "0 B";
    const i = Math.floor(Math.log(Number(bytes)) / Math.log(BASE));
    return parseFloat((Number(bytes) / Math.pow(BASE, i)).toFixed(2)) + " " + SIZES[i];
}

export function formatDuration(seconds) {
    if (!seconds) return "00:00:00";
    const h = Math.floor(seconds / 3600);
    const m = Math.floor((seconds - h * 3600) / 60);
    const s = Math.floor(seconds - h * 3600 - m * 60);
    return `${String(h).padStart(2, "0")}:${String(m).padStart(2, "0")}:${String(s).padStart(2, "0")}`;
}

// Map raw flow array item to structured React objects
const mapFlow = (flow) => {
    const isMac = flow[2] && flow[2].includes(":");
    return {
        client: isMac ? "" : flow[2],
        mac: isMac ? flow[2] : "",
        hostname: flow[3],
        date: flow[0],
        duration: formatDuration(flow[1]),
        port: flow[4],
        sent: formatBytes(flow[6]),
        received: formatBytes(flow[7]),
        // Raw properties for sorting/filtering
        rawDuration: flow[1],
        rawSent: flow[6],
        rawReceived: flow[7],
        rawClient: flow[2],
        rawPort: flow[4],
        rawProto: flow[5],
        children: flow[8] ? flow[8].map(mapFlow) : null
    };
};

export const PakonProvider = ({ children }) => {
    // Default: 24 hours ago to now
    const initialDates = useMemo(() => {
        const now = new Date();
        const oneDayAgo = new Date(now.getTime() - 24 * 60 * 60 * 1000);
        
        const pad = (n) => String(n).padStart(2, "0");
        const formatDate = (d) => `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}`;
        const formatTime = (d) => `${pad(d.getHours())}:${pad(d.getMinutes())}`;
        
        return {
            dateFrom: formatDate(oneDayAgo),
            timeFrom: formatTime(oneDayAgo),
            dateTo: formatDate(now),
            timeTo: formatTime(now),
        };
    }, []);

    // Filter Form state
    const [dateFrom, setDateFrom] = useState(initialDates.dateFrom);
    const [timeFrom, setTimeFrom] = useState(initialDates.timeFrom);
    const [dateTo, setDateTo] = useState(initialDates.dateTo);
    const [timeTo, setTimeTo] = useState(initialDates.timeTo);
    const [hostnameFilter, setHostnameFilter] = useState("");
    const [clientFilter, setClientFilter] = useState("");
    const [aggregate, setAggregate] = useState(true);

    // API Data state
    const [fullData, setFullData] = useState([]);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);

    // Pagination/Sort state
    const [currentPage, setCurrentPage] = useState(0);
    const [pageSize, setPageSize] = useState(50);
    const [sortBy, setSortBy] = useState([3, -1]); // Default sort by Date (index 3), descending (-1)
    const [expandedRows, setExpandedRows] = useState(new Set());

    // Fetch data from CGI backend
    const fetchData = async () => {
        setLoading(true);
        setError(null);
        try {
            // Build absolute timestamps
            const fromTimestamp = Math.floor(Date.parse(`${dateFrom}T${timeFrom || "00:00:00"}`) / 1000);
            const toTimestamp = Math.floor(Date.parse(`${dateTo}T${timeTo || "00:00:00"}`) / 1000);

            if (isNaN(fromTimestamp) || isNaN(toTimestamp)) {
                throw new Error("Invalid date/time range");
            }

            // The pakon CGI parses this body line by line with sed, so each key
            // has to sit on its own line. JSON.stringify() emits it all on one
            // line, which makes the CGI hand pakon-show a mangled -s/-e value.
            const query = `{\n"start":${fromTimestamp},\n"end":${toTimestamp}}`;

            const response = await fetch("/repakon/api", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                body: query
            });

            if (!response.ok) {
                throw new Error(`Server returned status ${response.status}`);
            }

            const data = await response.json();
            
            // Expected format: Array of arrays:
            // 0: datetime, 1: duration, 2: client (friendly or MAC), 3: hostname, 4: port, 5: proto, 6: sent, 7: received
            setFullData(Array.isArray(data) ? data : []);
            setCurrentPage(0);
            setExpandedRows(new Set());
        } catch (err) {
            console.error("Fetch pakon API failed:", err);
            setError(err.message || "Failed to fetch network insights.");
        } finally {
            setLoading(false);
        }
    };

    // Auto-fetch on mount
    useEffect(() => {
        fetchData();
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, []);

    // Quick filters click interface (e.g. clicking magnifying glass in cells)
    const addHostnameFilter = (host) => {
        if (!host) return;
        setHostnameFilter(prev => {
            const list = prev ? prev.split(",").map(x => x.trim()) : [];
            if (list.includes(host)) return prev;
            return [...list, host].join(", ");
        });
    };

    const addClientFilter = (client) => {
        if (!client) return;
        setClientFilter(prev => {
            const list = prev ? prev.split(",").map(x => x.trim()) : [];
            if (list.includes(client)) return prev;
            return [...list, client].join(", ");
        });
    };

    // Client-side filtering logic
    const filteredData = useMemo(() => {
        // Compile regular expressions for hostname
        const hostRegexes = hostnameFilter
            ? hostnameFilter.split(",").map(h => h.trim()).filter(Boolean).map(h => {
                try {
                    return new RegExp(h, "i");
                } catch {
                    // Fallback to literal search if regex compiles with error
                    return new RegExp(h.replace(/[-\\^$*+?.()|[\]{}]/g, '\\$&'), "i");
                }
              })
            : [];

        // Compile regular expressions for client
        const clientRegexes = clientFilter
            ? clientFilter.split(",").map(c => c.trim()).filter(Boolean).map(c => {
                try {
                    return new RegExp(c, "i");
                } catch {
                    return new RegExp(c.replace(/[-\\^$*+?.()|[\]{}]/g, '\\$&'), "i");
                }
              })
            : [];

        return fullData.filter(flow => {
            // flow[3] is hostname, flow[2] is client name/MAC
            const host = flow[3] || "";
            const client = flow[2] || "";

            // Check hostname filter match
            let hostMatched = hostRegexes.length === 0;
            for (const rx of hostRegexes) {
                if (rx.test(host)) {
                    hostMatched = true;
                    break;
                }
            }

            // Check client filter match
            let clientMatched = clientRegexes.length === 0;
            for (const rx of clientRegexes) {
                if (rx.test(client)) {
                    clientMatched = true;
                    break;
                }
            }

            return hostMatched && clientMatched;
        });
    }, [fullData, hostnameFilter, clientFilter]);

    // Client-side hostname aggregation + sorting
    const processedData = useMemo(() => {
        const mapped = filteredData.map(mapFlow);

        let dataToProcess = mapped;

        if (aggregate) {
            // Aggregate by Hostname + Client
            const sortedForAgg = [...mapped].sort((a, b) => {
                if (a.hostname !== b.hostname) {
                    return a.hostname < b.hostname ? -1 : 1;
                }
                if (a.rawClient !== b.rawClient) {
                    return a.rawClient < b.rawClient ? -1 : 1;
                }
                return new Date(a.date) - new Date(b.date);
            });

            const aggregated = [];
            let currentGroup = [];

            const flushGroup = () => {
                if (currentGroup.length === 0) return;
                if (currentGroup.length === 1) {
                    aggregated.push(currentGroup[0]);
                } else {
                    const first = currentGroup[0];
                    let totalSent = 0;
                    let totalReceived = 0;
                    let minDate = new Date(first.date);
                    let maxDate = new Date(new Date(first.date).getTime() + first.rawDuration * 1000);
                    let firstPort = first.rawPort;
                    let samePort = true;

                    currentGroup.forEach(item => {
                        totalSent += item.rawSent;
                        totalReceived += item.rawReceived;

                        const itemStart = new Date(item.date);
                        const itemEnd = new Date(itemStart.getTime() + item.rawDuration * 1000);

                        if (itemStart < minDate) minDate = itemStart;
                        if (itemEnd > maxDate) maxDate = itemEnd;

                        if (item.rawPort !== firstPort) {
                            samePort = false;
                        }
                    });

                    const durationSec = Math.max(0, Math.floor((maxDate - minDate) / 1000));
                    const printDate = (d) => {
                        const pad = (n) => String(n).padStart(2, "0");
                        return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())} ${pad(d.getHours())}:${pad(d.getMinutes())}:${pad(d.getSeconds())}`;
                    };

                    aggregated.push({
                        client: first.client,
                        mac: first.mac,
                        hostname: first.hostname,
                        date: printDate(minDate),
                        duration: formatDuration(durationSec),
                        port: samePort ? firstPort : "",
                        sent: formatBytes(totalSent),
                        received: formatBytes(totalReceived),
                        rawDuration: durationSec,
                        rawSent: totalSent,
                        rawReceived: totalReceived,
                        rawClient: first.rawClient,
                        rawPort: samePort ? firstPort : "",
                        children: currentGroup
                    });
                }
            };

            sortedForAgg.forEach(item => {
                if (currentGroup.length === 0) {
                    currentGroup.push(item);
                } else {
                    const first = currentGroup[0];
                    if (item.hostname === first.hostname && item.rawClient === first.rawClient) {
                        currentGroup.push(item);
                    } else {
                        flushGroup();
                        currentGroup = [item];
                    }
                }
            });
            flushGroup();
            dataToProcess = aggregated;
        }

        // Apply column sorting
        // Headers: 0: Client, 1: MAC, 2: Hostname, 3: Date, 4: Duration, 5: Port, 6: Sent, 7: Received
        const [sortCol, sortDir] = sortBy;
        dataToProcess.sort((a, b) => {
            let valA, valB;
            switch (sortCol) {
                case 0: // Client
                    valA = a.client || a.rawClient || "";
                    valB = b.client || b.rawClient || "";
                    break;
                case 1: // MAC
                    valA = a.mac || a.rawClient || "";
                    valB = b.mac || b.rawClient || "";
                    break;
                case 2: // Hostname
                    valA = a.hostname || "";
                    valB = b.hostname || "";
                    break;
                case 3: // Date
                    valA = a.date || "";
                    valB = b.date || "";
                    break;
                case 4: // Duration
                    valA = a.rawDuration || 0;
                    valB = b.rawDuration || 0;
                    break;
                case 5: // Port
                    valA = a.rawPort || "";
                    valB = b.rawPort || "";
                    break;
                case 6: // Sent
                    valA = a.rawSent || 0;
                    valB = b.rawSent || 0;
                    break;
                case 7: // Received
                    valA = a.rawReceived || 0;
                    valB = b.rawReceived || 0;
                    break;
                default:
                    valA = a.date || "";
                    valB = b.date || "";
            }

            if (valA === valB) return 0;
            const res = valA < valB ? -1 : 1;
            return res * sortDir;
        });

        return dataToProcess;
    }, [filteredData, aggregate, sortBy]);

    // Paginated subset
    const paginatedData = useMemo(() => {
        if (pageSize === 0) return processedData; // 0 means show everything
        const start = currentPage * pageSize;
        return processedData.slice(start, start + pageSize);
    }, [processedData, currentPage, pageSize]);

    // Handle toggling of parent rows
    const toggleRowExpansion = (rowKey) => {
        setExpandedRows(prev => {
            const next = new Set(prev);
            if (next.has(rowKey)) {
                next.delete(rowKey);
            } else {
                next.add(rowKey);
            }
            return next;
        });
    };

    // Download CSV action (filtered list)
    const downloadCSV = () => {
        let csvContent = "date;duration;client;hostname;port;sent(B);received(B)\n";
        filteredData.forEach(flow => {
            const dateStr = flow[0];
            const durationStr = formatDuration(flow[1]);
            const clientStr = flow[2] || "";
            const hostnameStr = flow[3] || "";
            const portStr = flow[4] || "";
            const sentBytes = flow[6] || 0;
            const receivedBytes = flow[7] || 0;

            csvContent += `${dateStr};${durationStr};${clientStr};${hostnameStr};${portStr};${sentBytes};${receivedBytes}\n`;
        });

        const uri = "data:text/csv;charset=utf-8," + encodeURIComponent(csvContent);
        const link = document.createElement("a");
        link.href = uri;
        link.style.visibility = "hidden";
        link.download = "pakon.csv";
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
    };

    return (
        <PakonContext.Provider
            value={{
                dateFrom, setDateFrom,
                timeFrom, setTimeFrom,
                dateTo, setDateTo,
                timeTo, setTimeTo,
                hostnameFilter, setHostnameFilter,
                clientFilter, setClientFilter,
                aggregate, setAggregate,
                
                loading,
                error,
                filteredData,
                processedData,
                paginatedData,
                currentPage, setCurrentPage,
                pageSize, setPageSize,
                sortBy, setSortBy,
                expandedRows, toggleRowExpansion,
                
                fetchData,
                addHostnameFilter,
                addClientFilter,
                downloadCSV
            }}
        >
            {children}
        </PakonContext.Provider>
    );
};
