import { Disclosure } from "@headlessui/react";
import DarkModeToggle from "./DarkModeToggle";
import logo from "./turris-logo-without-wording.svg";

const Navigation = () => {
    return (
        <Disclosure as="nav" className="bg-gray-800">
            <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
                <div className="border-b border-gray-700">
                    <div className="flex items-center justify-between h-16">
                        <div className="flex items-center">
                            <div className="flex-shrink-0">
                                <a href="/">
                                    <img
                                        className="h-8 w-8"
                                        src={logo}
                                        alt="Workflow"
                                    />
                                </a>
                            </div>
                            <div className="text-white text-2xl ml-5">
                                <a href="/">
                                    <h1>Pakon</h1>
                                </a>
                            </div>
                        </div>
                        <div className="hidden md:block">
                            <div className="ml-4 flex items-center md:ml-6">
                                <DarkModeToggle disabled/>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </Disclosure>
    );
};

export default Navigation;
