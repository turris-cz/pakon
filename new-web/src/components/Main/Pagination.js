import React, { useContext } from "react";
import { PakonContext } from "../../context/PakonContext";
import { ChevronLeftIcon, ChevronRightIcon } from "@heroicons/react/solid";

export default function Pagination() {
    const {
        currentPage,
        setCurrentPage,
        pageSize,
        setPageSize,
        processedData
    } = useContext(PakonContext);

    const totalResults = processedData.length;
    const totalPages = pageSize === 0 ? 1 : Math.ceil(totalResults / pageSize);
    const startIndex = totalResults === 0 ? 0 : currentPage * pageSize + 1;
    const endIndex = pageSize === 0 ? totalResults : Math.min(totalResults, (currentPage + 1) * pageSize);

    const handlePrev = (e) => {
        e.preventDefault();
        if (currentPage > 0) setCurrentPage(currentPage - 1);
    };

    const handleNext = (e) => {
        e.preventDefault();
        if (currentPage < totalPages - 1) setCurrentPage(currentPage + 1);
    };

    const handlePageClick = (pageIdx, e) => {
        e.preventDefault();
        setCurrentPage(pageIdx);
    };

    const handlePageSizeChange = (e) => {
        setPageSize(Number(e.target.value));
        setCurrentPage(0);
    };

    // Generate page links to display (e.g. 1 2 3 ... 9 10)
    const getPageNumbers = () => {
        const pages = [];
        const maxVisible = 5;

        if (totalPages <= maxVisible) {
            for (let i = 0; i < totalPages; i++) pages.push(i);
        } else {
            // Always include first page
            pages.push(0);

            let start = Math.max(1, currentPage - 1);
            let end = Math.min(totalPages - 2, currentPage + 1);

            // Adjust window boundaries if at start/end
            if (currentPage <= 2) {
                end = 3;
            } else if (currentPage >= totalPages - 3) {
                start = totalPages - 4;
            }

            if (start > 1) {
                pages.push("ellipsis-1");
            }

            for (let i = start; i <= end; i++) {
                pages.push(i);
            }

            if (end < totalPages - 2) {
                pages.push("ellipsis-2");
            }

            // Always include last page
            pages.push(totalPages - 1);
        }
        return pages;
    };

    if (totalResults === 0) return null;

    return (
        <div className="px-4 py-3 flex items-center justify-between border-t border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 transition-colors duration-300">
            {/* Mobile View */}
            <div className="flex-1 flex justify-between sm:hidden">
                <button
                    onClick={handlePrev}
                    disabled={currentPage === 0}
                    className={`relative inline-flex items-center px-4 py-2 border border-gray-300 dark:border-gray-600 text-sm font-medium rounded-md text-gray-700 dark:text-gray-200 bg-white dark:bg-gray-750 transition-colors ${
                        currentPage === 0 ? "opacity-50 cursor-not-allowed" : "hover:bg-gray-50 dark:hover:bg-gray-700"
                    }`}
                >
                    Previous
                </button>
                <span className="text-sm text-gray-700 dark:text-gray-300 self-center">
                    Page {currentPage + 1} of {totalPages}
                </span>
                <button
                    onClick={handleNext}
                    disabled={currentPage === totalPages - 1}
                    className={`ml-3 relative inline-flex items-center px-4 py-2 border border-gray-300 dark:border-gray-600 text-sm font-medium rounded-md text-gray-700 dark:text-gray-200 bg-white dark:bg-gray-750 transition-colors ${
                        currentPage === totalPages - 1 ? "opacity-50 cursor-not-allowed" : "hover:bg-gray-50 dark:hover:bg-gray-700"
                    }`}
                >
                    Next
                </button>
            </div>

            {/* Desktop View */}
            <div className="hidden sm:flex-1 sm:flex sm:items-center sm:justify-between">
                {/* Result range and page size selector */}
                <div className="flex items-center space-x-4">
                    <p className="text-sm text-gray-700 dark:text-gray-300">
                        Showing <span className="font-semibold text-gray-900 dark:text-white">{startIndex}</span> to{" "}
                        <span className="font-semibold text-gray-900 dark:text-white">{endIndex}</span> of{" "}
                        <span className="font-semibold text-gray-900 dark:text-white">{totalResults}</span> results
                    </p>
                    
                    <div className="flex items-center space-x-1.5 text-sm text-gray-500 dark:text-gray-400">
                        <span>•</span>
                        <label htmlFor="pagesize" className="sr-only">Page Size</label>
                        <select
                            id="pagesize"
                            value={pageSize}
                            onChange={handlePageSizeChange}
                            className="block pl-2 pr-8 py-1.5 text-sm border-gray-300 dark:border-gray-600 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 rounded bg-white dark:bg-gray-750 text-gray-700 dark:text-gray-200"
                        >
                            <option value="25">25 per page</option>
                            <option value="50">50 per page</option>
                            <option value="100">100 per page</option>
                            <option value="200">200 per page</option>
                            <option value="500">500 per page</option>
                            <option value="0">Show everything</option>
                        </select>
                    </div>
                </div>

                {/* Page number buttons */}
                {totalPages > 1 && (
                    <div>
                        <nav
                            className="relative z-0 inline-flex rounded-md shadow-sm -space-x-px"
                            aria-label="Pagination"
                        >
                            <button
                                onClick={handlePrev}
                                disabled={currentPage === 0}
                                className={`relative inline-flex items-center px-2 py-2 rounded-l-md border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-750 text-sm font-medium text-gray-500 dark:text-gray-300 transition-colors ${
                                    currentPage === 0 ? "opacity-50 cursor-not-allowed" : "hover:bg-gray-50 dark:hover:bg-gray-700"
                                }`}
                            >
                                <span className="sr-only">Previous</span>
                                <ChevronLeftIcon className="h-5 w-5" aria-hidden="true" />
                            </button>

                            {getPageNumbers().map((pageNum, idx) => {
                                if (pageNum === "ellipsis-1" || pageNum === "ellipsis-2") {
                                    return (
                                        <span
                                            key={`ellipsis-${idx}`}
                                            className="relative inline-flex items-center px-4 py-2 border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-750 text-sm font-medium text-gray-700 dark:text-gray-350"
                                        >
                                            ...
                                        </span>
                                    );
                                }

                                const isActive = currentPage === pageNum;
                                return (
                                    <button
                                        key={pageNum}
                                        onClick={(e) => handlePageClick(pageNum, e)}
                                        aria-current={isActive ? "page" : undefined}
                                        className={`relative inline-flex items-center px-4 py-2 border text-sm font-medium transition-colors ${
                                            isActive
                                                ? "z-10 bg-indigo-50 dark:bg-indigo-900 border-indigo-500 dark:border-indigo-600 text-indigo-600 dark:text-indigo-200"
                                                : "bg-white dark:bg-gray-750 border-gray-300 dark:border-gray-600 text-gray-500 dark:text-gray-350 hover:bg-gray-50 dark:hover:bg-gray-700"
                                        }`}
                                    >
                                        {pageNum + 1}
                                    </button>
                                );
                            })}

                            <button
                                onClick={handleNext}
                                disabled={currentPage === totalPages - 1}
                                className={`relative inline-flex items-center px-2 py-2 rounded-r-md border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-750 text-sm font-medium text-gray-500 dark:text-gray-300 transition-colors ${
                                    currentPage === totalPages - 1 ? "opacity-50 cursor-not-allowed" : "hover:bg-gray-50 dark:hover:bg-gray-700"
                                }`}
                            >
                                <span className="sr-only">Next</span>
                                <ChevronRightIcon className="h-5 w-5" aria-hidden="true" />
                            </button>
                        </nav>
                    </div>
                )}
            </div>
        </div>
    );
}
