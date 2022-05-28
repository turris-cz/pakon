import React from "react";
import Navigation from "./Navigation";

const Header = () => {
    return (
        <>
            <Navigation />
            <header className="py-6">
                <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
                    <h2 className="text-3xl font-bold text-white">Dashboard</h2>
                </div>
            </header>
        </>
    );
};

export default Header;
