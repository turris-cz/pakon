import React, { useContext } from "react";
import { PakonContext } from "../../context/PakonContext";

export default function Filter() {
    const {
        dateFrom, setDateFrom,
        timeFrom, setTimeFrom,
        dateTo, setDateTo,
        timeTo, setTimeTo,
        hostnameFilter, setHostnameFilter,
        clientFilter, setClientFilter,
        aggregate, setAggregate,
        loading,
        fetchData
    } = useContext(PakonContext);

    const fromVal = dateFrom && timeFrom ? `${dateFrom}T${timeFrom}` : "";
    const toVal = dateTo && timeTo ? `${dateTo}T${timeTo}` : "";

    const handleFromChange = (e) => {
        const val = e.target.value;
        if (val) {
            const [d, t] = val.split("T");
            setDateFrom(d);
            setTimeFrom(t || "00:00");
        } else {
            setDateFrom("");
            setTimeFrom("");
        }
    };

    const handleToChange = (e) => {
        const val = e.target.value;
        if (val) {
            const [d, t] = val.split("T");
            setDateTo(d);
            setTimeTo(t || "00:00");
        } else {
            setDateTo("");
            setTimeTo("");
        }
    };

    return (
        <div className="bg-white dark:bg-gray-800 shadow-lg sm:rounded-lg mb-10 border border-gray-100 dark:border-gray-750 transition-all duration-300">
            <div className="px-4 py-5 sm:p-6">
                <div className="grid grid-cols-1 gap-y-6 gap-x-4 sm:grid-cols-8">
                    {/* From Date-Time */}
                    <div className="sm:col-span-2 border border-gray-300 dark:border-gray-600 rounded-md px-3 py-2 shadow-sm focus-within:ring-1 focus-within:ring-indigo-600 focus-within:border-indigo-600 dark:bg-gray-700">
                        <label
                            htmlFor="date-from"
                            className="block text-xs font-medium text-gray-500 dark:text-gray-300"
                        >
                            From
                        </label>
                        <input
                            type="datetime-local"
                            name="date-from"
                            id="date-from"
                            value={fromVal}
                            onChange={handleFromChange}
                            className="block w-full border-0 p-0 text-gray-900 dark:text-white placeholder-gray-500 focus:ring-0 sm:text-sm focus:outline-none bg-transparent"
                        />
                    </div>

                    {/* To Date-Time */}
                    <div className="sm:col-span-2 border border-gray-300 dark:border-gray-600 rounded-md px-3 py-2 shadow-sm focus-within:ring-1 focus-within:ring-indigo-600 focus-within:border-indigo-600 dark:bg-gray-700">
                        <label
                            htmlFor="date-to"
                            className="block text-xs font-medium text-gray-500 dark:text-gray-300"
                        >
                            To
                        </label>
                        <input
                            type="datetime-local"
                            name="date-to"
                            id="date-to"
                            value={toVal}
                            onChange={handleToChange}
                            className="block w-full border-0 p-0 text-gray-900 dark:text-white placeholder-gray-500 focus:ring-0 sm:text-sm focus:outline-none bg-transparent"
                        />
                    </div>

                    {/* Hostname Filter */}
                    <div className="sm:col-span-2 border border-gray-300 dark:border-gray-600 rounded-md px-3 py-2 shadow-sm focus-within:ring-1 focus-within:ring-indigo-600 focus-within:border-indigo-600 dark:bg-gray-700">
                        <label
                            htmlFor="hostname"
                            className="block text-xs font-medium text-gray-500 dark:text-gray-300"
                        >
                            Hostname
                        </label>
                        <input
                            type="text"
                            name="hostname"
                            id="hostname"
                            value={hostnameFilter}
                            onChange={(e) => setHostnameFilter(e.target.value)}
                            className="block w-full border-0 p-0 text-gray-900 dark:text-white placeholder-gray-500 focus:ring-0 sm:text-sm focus:outline-none bg-transparent"
                            placeholder="mail.nic.cz"
                        />
                    </div>

                    {/* Client Filter */}
                    <div className="sm:col-span-2 border border-gray-300 dark:border-gray-600 rounded-md px-3 py-2 shadow-sm focus-within:ring-1 focus-within:ring-indigo-600 focus-within:border-indigo-600 dark:bg-gray-700">
                        <label
                            htmlFor="client"
                            className="block text-xs font-medium text-gray-500 dark:text-gray-300"
                        >
                            Client
                        </label>
                        <input
                            type="text"
                            name="client"
                            id="client"
                            value={clientFilter}
                            onChange={(e) => setClientFilter(e.target.value)}
                            className="block w-full border-0 p-0 text-gray-900 dark:text-white placeholder-gray-500 focus:ring-0 sm:text-sm focus:outline-none bg-transparent"
                            placeholder="00:AA:BB:CC:DD:11"
                        />
                    </div>

                    {/* Aggregation */}
                    <div className="sm:col-span-6">
                        <div className="relative flex items-start">
                            <div className="flex items-center h-5">
                                <input
                                    id="aggregation"
                                    aria-describedby="aggregation-description"
                                    name="aggregation"
                                    type="checkbox"
                                    checked={aggregate}
                                    onChange={(e) => setAggregate(e.target.checked)}
                                    className="focus:ring-indigo-500 h-4 w-4 text-indigo-600 border-gray-300 dark:border-gray-650 rounded dark:bg-gray-700"
                                />
                            </div>
                            <div className="ml-3 text-sm">
                                <label
                                    htmlFor="aggregation"
                                    className="font-medium text-gray-700 dark:text-gray-200"
                                >
                                    Aggregate by hostname
                                </label>
                                <p className="text-gray-500 dark:text-gray-400 text-xs">
                                    This option aggregates concurrent/simultaneous flows to the same hostname per client.
                                </p>
                            </div>
                        </div>
                    </div>

                    {/* Action Button */}
                    <div className="sm:col-span-2 text-right w-full flex justify-end items-center">
                        <button
                            type="button"
                            onClick={fetchData}
                            disabled={loading}
                            className={`inline-flex items-center px-4 py-2 border border-transparent text-sm leading-5 font-medium rounded-md shadow-sm text-white transition-all duration-150 ${
                                loading
                                    ? "bg-indigo-400 cursor-not-allowed"
                                    : "bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
                            }`}
                        >
                            {loading ? (
                                <>
                                    <svg
                                        className="animate-spin -ml-1 mr-2 h-4 w-4 text-white"
                                        fill="none"
                                        viewBox="0 0 24 24"
                                    >
                                        <circle
                                            className="opacity-25"
                                            cx="12"
                                            cy="12"
                                            r="10"
                                            stroke="currentColor"
                                            strokeWidth="4"
                                        />
                                        <path
                                            className="opacity-75"
                                            fill="currentColor"
                                            d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                                        />
                                    </svg>
                                    Loading...
                                </>
                            ) : (
                                "Explore"
                            )}
                        </button>
                    </div>
                </div>
            </div>
        </div>
    );
}
