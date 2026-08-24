import React, { useContext } from "react";
import { PakonContext } from "../../context/PakonContext";
import Pagination from "./Pagination";
import {
    ChevronDownIcon,
    ChevronRightIcon,
    SearchIcon,
    ArrowSmUpIcon,
    ArrowSmDownIcon,
    ExternalLinkIcon
} from "@heroicons/react/solid";

export default function Details() {
    const {
        paginatedData,
        sortBy,
        setSortBy,
        expandedRows,
        toggleRowExpansion,
        addHostnameFilter,
        addClientFilter,
        loading
    } = useContext(PakonContext);

    // Column definition: [label, index, sortable]
    const columns = [
        { label: "Client", index: 0, sortable: true },
        { label: "MAC", index: 1, sortable: true },
        { label: "Hostname", index: 2, sortable: true },
        { label: "Date", index: 3, sortable: true },
        { label: "Duration", index: 4, sortable: true },
        { label: "Port", index: 5, sortable: true },
        { label: "Sent", index: 6, sortable: true },
        { label: "Received", index: 7, sortable: true }
    ];

    const handleSort = (colIndex) => {
        const [currentCol, currentDir] = sortBy;
        if (currentCol === colIndex) {
            // Toggle direction: -1 (desc) -> 1 (asc) -> -1 (desc)
            setSortBy([colIndex, currentDir === -1 ? 1 : -1]);
        } else {
            // Default to ascending for columns, except date/sent/received/duration which default to desc
            const defaultDesc = [3, 4, 6, 7].includes(colIndex);
            setSortBy([colIndex, defaultDesc ? -1 : 1]);
        }
    };

    const getRowKey = (item) => {
        return `${item.date}_${item.hostname}_${item.client || item.mac}`;
    };

    const renderSortIcon = (colIndex) => {
        const [currentCol, currentDir] = sortBy;
        if (currentCol !== colIndex) return null;
        return currentDir === 1 ? (
            <ArrowSmUpIcon className="ml-1 h-4 w-4 text-indigo-500 inline" />
        ) : (
            <ArrowSmDownIcon className="ml-1 h-4 w-4 text-indigo-500 inline" />
        );
    };

    const renderCellWithSearch = (text, onClickSearch, showExternalLink = false) => {
        if (!text) return "-";
        return (
            <div className="flex items-center space-x-1 group">
                <span className="truncate max-w-[180px]" title={text}>{text}</span>
                <button
                    type="button"
                    onClick={(e) => {
                        e.stopPropagation();
                        onClickSearch();
                    }}
                    className="opacity-0 group-hover:opacity-100 focus:opacity-100 text-gray-400 hover:text-indigo-600 transition-opacity p-0.5 rounded"
                    title={`Filter by ${text}`}
                >
                    <SearchIcon className="h-3.5 w-3.5" />
                </button>
                {showExternalLink && (
                    <a
                        href={`https://${text}`}
                        target="_blank"
                        rel="noreferrer"
                        className="opacity-0 group-hover:opacity-100 focus:opacity-100 text-gray-400 hover:text-indigo-600 transition-opacity p-0.5 rounded"
                        title={`Open ${text} in new tab`}
                    >
                        <ExternalLinkIcon className="h-3.5 w-3.5" />
                    </a>
                )}
            </div>
        );
    };

    return (
        <div className="flex flex-col px-4 py-4 bg-white dark:bg-gray-800 transition-colors duration-300">
            <div className="overflow-x-auto border border-gray-200 dark:border-gray-700 sm:rounded-lg shadow-inner">
                <div className="py-2 align-middle inline-block min-w-full">
                    <div className="overflow-hidden">
                        <table className="min-w-full divide-y divide-gray-200 dark:divide-gray-700 rounded-sm">
                            <thead className="bg-gray-50 dark:bg-gray-750">
                                <tr>
                                    {/* Action Column for Aggregated Expansion */}
                                    <th scope="col" className="w-10 px-3 py-3" />
                                    
                                    {columns.map((col) => (
                                        <th
                                            key={col.label}
                                            scope="col"
                                            onClick={() => col.sortable && handleSort(col.index)}
                                            className={`px-4 py-3 text-left text-xs font-semibold text-gray-600 dark:text-gray-300 uppercase tracking-wider ${
                                                col.sortable ? "cursor-pointer select-none hover:text-indigo-600 dark:hover:text-indigo-400 transition-colors" : ""
                                            }`}
                                        >
                                            <div className="flex items-center">
                                                {col.label}
                                                {col.sortable && renderSortIcon(col.index)}
                                            </div>
                                        </th>
                                    ))}
                                </tr>
                            </thead>
                            <tbody className="divide-y divide-gray-100 dark:divide-gray-750 bg-white dark:bg-gray-800">
                                {loading && paginatedData.length === 0 ? (
                                    <tr>
                                        <td colSpan={9} className="px-6 py-10 text-center text-sm text-gray-500 dark:text-gray-400">
                                            <div className="flex justify-center items-center space-x-2">
                                                <svg className="animate-spin h-5 w-5 text-indigo-600" fill="none" viewBox="0 0 24 24">
                                                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                                                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                                                </svg>
                                                <span>Fetching flows...</span>
                                            </div>
                                        </td>
                                    </tr>
                                ) : paginatedData.length === 0 ? (
                                    <tr>
                                        <td colSpan={9} className="px-6 py-12 text-center text-sm text-gray-500 dark:text-gray-400 font-medium">
                                            No records found matching filters.
                                        </td>
                                    </tr>
                                ) : (
                                    paginatedData.map((item, itemIdx) => {
                                        const key = getRowKey(item);
                                        const isExpanded = expandedRows.has(key);
                                        const hasChildren = item.children && item.children.length > 0;

                                        return (
                                            <React.Fragment key={key}>
                                                {/* Parent Row */}
                                                <tr
                                                    className={`hover:bg-indigo-50/30 dark:hover:bg-gray-750/30 transition-colors ${
                                                        itemIdx % 2 === 0 ? "bg-white dark:bg-gray-800" : "bg-gray-50/50 dark:bg-gray-750/10"
                                                    }`}
                                                >
                                                    {/* Expansion Button */}
                                                    <td className="px-3 py-3 whitespace-nowrap text-center text-sm font-medium">
                                                        {hasChildren && (
                                                            <button
                                                                type="button"
                                                                onClick={() => toggleRowExpansion(key)}
                                                                className="text-gray-400 hover:text-indigo-600 focus:outline-none"
                                                            >
                                                                {isExpanded ? (
                                                                    <ChevronDownIcon className="h-5 w-5" />
                                                                ) : (
                                                                    <ChevronRightIcon className="h-5 w-5" />
                                                                )}
                                                            </button>
                                                        )}
                                                    </td>

                                                    {/* Client Name */}
                                                    <td className="px-4 py-3 whitespace-nowrap text-sm font-medium text-gray-900 dark:text-white">
                                                        {renderCellWithSearch(item.client, () => addClientFilter(item.client))}
                                                    </td>

                                                    {/* Client MAC */}
                                                    <td className="px-4 py-3 whitespace-nowrap text-sm text-gray-500 dark:text-gray-300 font-mono">
                                                        {renderCellWithSearch(item.mac, () => addClientFilter(item.mac))}
                                                    </td>

                                                    {/* Hostname */}
                                                    <td className="px-4 py-3 whitespace-nowrap text-sm text-gray-500 dark:text-gray-300">
                                                        {renderCellWithSearch(item.hostname, () => addHostnameFilter(item.hostname), item.port === "http" || item.port === "https")}
                                                    </td>

                                                    {/* Date */}
                                                    <td className="px-4 py-3 whitespace-nowrap text-sm text-gray-500 dark:text-gray-400">
                                                        {item.date}
                                                    </td>

                                                    {/* Duration */}
                                                    <td className="px-4 py-3 whitespace-nowrap text-sm text-gray-500 dark:text-gray-400">
                                                        {item.duration}
                                                    </td>

                                                    {/* Port / Protocol */}
                                                    <td className="px-4 py-3 whitespace-nowrap text-sm text-gray-500 dark:text-gray-400 font-medium">
                                                        {item.port || "-"}
                                                    </td>

                                                    {/* Sent Bytes */}
                                                    <td className="px-4 py-3 whitespace-nowrap text-sm text-gray-500 dark:text-gray-400">
                                                        {item.sent}
                                                    </td>

                                                    {/* Received Bytes */}
                                                    <td className="px-4 py-3 whitespace-nowrap text-sm text-gray-500 dark:text-gray-400">
                                                        {item.received}
                                                    </td>
                                                </tr>

                                                {/* Expanded Children Rows */}
                                                {hasChildren && isExpanded && (
                                                    item.children.map((child, childIdx) => (
                                                        <tr
                                                            key={`${key}_child_${childIdx}`}
                                                            className="bg-indigo-50/20 dark:bg-gray-800/40 border-l-4 border-indigo-400"
                                                        >
                                                            <td className="px-3 py-2" />
                                                            <td className="px-4 py-2 whitespace-nowrap text-xs text-gray-400 dark:text-gray-500 pl-8">
                                                                └─ {child.client || "-"}
                                                            </td>
                                                            <td className="px-4 py-2 whitespace-nowrap text-xs text-gray-400 dark:text-gray-500 font-mono">
                                                                {child.mac || "-"}
                                                            </td>
                                                            <td className="px-4 py-2 whitespace-nowrap text-xs text-gray-400 dark:text-gray-500">
                                                                {child.hostname || "-"}
                                                            </td>
                                                            <td className="px-4 py-2 whitespace-nowrap text-xs text-gray-400 dark:text-gray-500">
                                                                {child.date}
                                                            </td>
                                                            <td className="px-4 py-2 whitespace-nowrap text-xs text-gray-400 dark:text-gray-500">
                                                                {child.duration}
                                                            </td>
                                                            <td className="px-4 py-2 whitespace-nowrap text-xs text-gray-400 dark:text-gray-500">
                                                                {child.port || "-"}
                                                            </td>
                                                            <td className="px-4 py-2 whitespace-nowrap text-xs text-gray-400 dark:text-gray-500">
                                                                {child.sent}
                                                            </td>
                                                            <td className="px-4 py-2 whitespace-nowrap text-xs text-gray-400 dark:text-gray-500">
                                                                {child.received}
                                                            </td>
                                                        </tr>
                                                    ))
                                                )}
                                            </React.Fragment>
                                        );
                                    })
                                )}
                            </tbody>
                        </table>
                    </div>
                </div>
            </div>
            
            {/* Pagination Controls */}
            <Pagination />
        </div>
    );
}
