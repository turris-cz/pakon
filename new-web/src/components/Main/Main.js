import React from "react";
import Filter from "./Filter";
import Results from "./Results";

const Main = () => {
    return (
        <main className="-mt-32 mb-auto">
            <div className="max-w-7xl mx-auto pb-12 px-4 sm:px-6 lg:px-8">
                <Filter />
                <Results />
            </div>
        </main>
    );
};

export default Main;
