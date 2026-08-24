import React from "react";
import { PakonContext } from "../../context/PakonContext";
import Details from "./Details";
import Graph from "./Graph";
import { DownloadIcon } from "@heroicons/react/solid";

export default class Table extends React.Component {
    static contextType = PakonContext;

    constructor(props) {
        super(props);
        this.state = {
            tabs: [
                { name: "Details", href: "", current: true },
                { name: "Visualization", href: "", current: false }
            ],
            isVisualization: false
        };
    }

    classNames(...classes) {
        return classes.filter(Boolean).join(" ");
    }

    handleOnClick(dtn) {
        if (dtn === "Details") {
            this.setState({
                tabs: [
                    { name: "Details", href: "", current: true },
                    { name: "Visualization", href: "", current: false }
                ],
                isVisualization: false
            });
        } else {
            this.setState({
                tabs: [
                    { name: "Details", href: "", current: false },
                    { name: "Visualization", href: "", current: true }
                ],
                isVisualization: true
            });
        }
    }

    render() {
        const { downloadCSV, filteredData } = this.context || {};
        const hasData = filteredData && filteredData.length > 0;

        return (
            <div className="px-4 pt-5 sm:px-6 bg-white dark:bg-gray-800 transition-colors duration-300">
                {/* Results Header with Title and Download Action */}
                <div className="flex justify-between items-center pb-3 border-b border-gray-100 dark:border-gray-700">
                    <h3 className="text-lg leading-6 font-medium text-gray-900 dark:text-white">
                        Results
                    </h3>
                    {downloadCSV && (
                        <button
                            type="button"
                            onClick={downloadCSV}
                            disabled={!hasData}
                            className={`inline-flex items-center px-3 py-1.5 border border-transparent text-xs font-semibold rounded shadow-sm text-white transition-all duration-150 ${
                                hasData
                                    ? "bg-emerald-600 hover:bg-emerald-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-emerald-500"
                                    : "bg-gray-300 dark:bg-gray-700 text-gray-400 dark:text-gray-500 cursor-not-allowed"
                            }`}
                            title={hasData ? "Download CSV" : "No results to download"}
                        >
                            <DownloadIcon className="h-4 w-4 mr-1" />
                            CSV
                        </button>
                    )}
                </div>

                <div className="pb-5 sm:pb-0">
                    <div className="mt-3 sm:mt-4">
                        <div className="sm:hidden">
                            <label htmlFor="current-tab" className="sr-only">
                                Select a tab
                            </label>
                            <select
                                id="current-tab"
                                name="current-tab"
                                className="block w-full pl-3 pr-10 py-2 text-base border-gray-300 dark:border-gray-600 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm rounded-md bg-white dark:bg-gray-750 text-gray-700 dark:text-gray-250"
                                defaultValue={
                                    this.state.tabs.find((tab) => tab.current).name
                                }
                                onChange={(e) => this.handleOnClick(e.target.value)}
                            >
                                {this.state.tabs.map((tab) => (
                                    <option key={tab.name}>{tab.name}</option>
                                ))}
                            </select>
                        </div>
                        
                        <div className="hidden sm:block">
                            <nav className="-mb-px flex space-x-8">
                                {this.state.tabs.map((tab) => (
                                    <li
                                        key={tab.name}
                                        onClick={() => this.handleOnClick(tab.name)}
                                        className={this.classNames(
                                            tab.current
                                                ? "border-indigo-500 text-indigo-600 dark:text-indigo-400 list-none cursor-pointer"
                                                : "border-transparent text-gray-500 hover:text-gray-700 dark:hover:text-gray-300 hover:border-gray-300 list-none cursor-pointer",
                                            "whitespace-nowrap pb-4 px-1 border-b-2 font-medium text-sm transition-colors duration-150"
                                        )}
                                        aria-current={
                                            tab.current ? "page" : undefined
                                        }
                                    >
                                        {tab.name}
                                    </li>
                                ))}
                            </nav>
                        </div>
                    </div>
                </div>

                <div className="mt-4">
                    {!this.state.isVisualization && <Details />}
                    {this.state.isVisualization && <Graph />}
                </div>
            </div>
        );
    }
}
