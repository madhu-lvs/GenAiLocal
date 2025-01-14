import React, { createContext, useContext, useEffect, useState } from "react";
import ReactDOM from "react-dom/client";
import { createHashRouter, Navigate, Outlet, RouterProvider } from "react-router-dom";
import { I18nextProvider } from "react-i18next";
import { HelmetProvider } from "react-helmet-async";
import { initializeIcons } from "@fluentui/react";

import "./index.css";

import Chat from "./pages/chat/Chat";
import LayoutWrapper from "./layoutWrapper";
import i18next from "./i18n/config";

initializeIcons();

const AuthContext = createContext<{ isAuthenticated: boolean; setAuthenticated: (auth: boolean) => void }>({
    isAuthenticated: false,
    setAuthenticated: () => {}
});

const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
    const [isAuthenticated, setAuthenticated] = useState(false);

    useEffect(() => {
        const token = localStorage.getItem("access_token");
        setAuthenticated(!!token);
    }, []);

    return <AuthContext.Provider value={{ isAuthenticated, setAuthenticated }}>{children}</AuthContext.Provider>;
};

const useAuth = () => useContext(AuthContext);

const ProtectedRoute: React.FC = () => {
    const { isAuthenticated } = useAuth();
    return isAuthenticated ? <Outlet /> : <Navigate to="/login" />;
};

// Router definition
const router = createHashRouter([
    {
        path: "/",
        element: <ProtectedRoute />,
        children: [
            {
                path: "/",
                element: <LayoutWrapper />,
                children: [
                    { index: true, element: <Chat /> },
                    { path: "qa", lazy: () => import("./pages/ask/Ask") },
                    { path: "*", lazy: () => import("./pages/NoPage") },
                    { path: "manage", lazy: () => import("./pages/manage/Manage") },
                    { path: "lookup", lazy: () => import("./pages/lookup/Lookup") },
                    { path: "help", lazy: () => import("./pages/help/Help") }
                ]
            }
        ]
    },
    {
        path: "/login",
        lazy: () => import("./pages/login/Login")
    }
]);

ReactDOM.createRoot(document.getElementById("root") as HTMLElement).render(
    <React.StrictMode>
        <I18nextProvider i18n={i18next}>
            <HelmetProvider>
                <AuthProvider>
                    <RouterProvider router={router} />
                </AuthProvider>
            </HelmetProvider>
        </I18nextProvider>
    </React.StrictMode>
);
