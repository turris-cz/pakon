import Main from "./components/Main/Main";
import Header from "./components/Header/Header";
import Footer from "./components/Footer/Footer";
import { PakonProvider } from "./context/PakonContext";

import "./App.css";

function App() {
    return (
        <PakonProvider>
            <div className="flex flex-col h-screen justify-between">
                <div className="bg-gray-800 pb-32">
                    <Header />
                </div>
                <Main />
                <Footer />
            </div>
        </PakonProvider>
    );
}

export default App;
