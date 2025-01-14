import React, { useState, useEffect, useRef, RefObject } from "react";
import { Outlet, NavLink, Link, useNavigate } from "react-router-dom";
import { useTranslation } from "react-i18next";
import styles from "./Layout.module.css";
import { IconButton } from "@fluentui/react";
import { jwtDecode, JwtPayload } from "jwt-decode";

const Layout = () => {
    const { t } = useTranslation();
    const [menuOpen, setMenuOpen] = useState(false);
    const menuRef: RefObject<HTMLDivElement> = useRef(null);
    const [isAuthenticated, setIsAuthenticated] = useState(false);
    const [userRole, setUserRole] = useState<string | null>(null);
    const navigate = useNavigate();

    const isTokenExpired = (token: string): boolean => {
        try {
            const decoded = jwtDecode<JwtPayload>(token);
            if (decoded.exp && decoded.exp * 1000 < Date.now()) {
                return true;
            }
            return false;
        } catch (error) {
            console.error("Error decoding token:", error);
            return true;
        }
    };

    useEffect(() => {
        const handleTokenUpdate = () => {
            const token = localStorage.getItem("access_token");
            if (token && !isTokenExpired(token)) {
                setIsAuthenticated(true);
                try {
                    const decoded = jwtDecode<{ role: string }>(token);
                    setUserRole(decoded.role);
                    if (!isAuthenticated) {
                        navigate("/", { replace: true });
                    }
                } catch (error) {
                    console.error("Error decoding token:", error);
                    setIsAuthenticated(false);
                    setUserRole(null);
                }
            } else {
                localStorage.removeItem("access_token");
                setIsAuthenticated(false);
                setUserRole(null);
                if (location.pathname !== "/login") {
                    navigate("/login", { replace: true });
                }
            }
        };

        window.addEventListener("tokenUpdated", handleTokenUpdate);
        handleTokenUpdate();
        return () => {
            window.removeEventListener("tokenUpdated", handleTokenUpdate);
        };
    }, [navigate, isAuthenticated]);

    useEffect(() => {
        if (isAuthenticated) {
            navigate("/");
        }
    }, [isAuthenticated, navigate]);

    const toggleMenu = () => {
        setMenuOpen(!menuOpen);
    };

    const handleClickOutside = (event: MouseEvent) => {
        if (menuRef.current && !menuRef.current.contains(event.target as Node)) {
            setMenuOpen(false);
        }
    };

    useEffect(() => {
        if (menuOpen) {
            document.addEventListener("mousedown", handleClickOutside);
        } else {
            document.removeEventListener("mousedown", handleClickOutside);
        }
        return () => {
            document.removeEventListener("mousedown", handleClickOutside);
        };
    }, [menuOpen]);

    const handleLogout = () => {
        localStorage.removeItem("access_token");
        setIsAuthenticated(false);
        setUserRole(null);
        navigate("/login", { replace: true });
    };

    return (
        <div className={styles.layout}>
            <header className={styles.header} role={"banner"}>
                <div className={styles.headerContainer} ref={menuRef}>
                    <Link to="/" className={styles.headerTitleContainer}>
                        <h3 className={styles.headerTitle}>{t("headerTitle")}</h3>
                    </Link>
                    <nav>
                        <ul className={`${styles.headerNavList} ${menuOpen ? styles.show : ""}`}>
                            <li>
                                <NavLink
                                    to="/"
                                    className={({ isActive }) => (isActive ? styles.headerNavPageLinkActive : styles.headerNavPageLink)}
                                    onClick={() => setMenuOpen(false)}
                                >
                                    {t("chat")}
                                </NavLink>
                            </li>
                            <li>
                                <NavLink
                                    to="/lookup"
                                    className={({ isActive }) => (isActive ? styles.headerNavPageLinkActive : styles.headerNavPageLink)}
                                    onClick={() => setMenuOpen(false)}
                                >
                                    {t("Lookup")}
                                </NavLink>
                            </li>
                            {userRole === "Admin" && (
                                <li>
                                    <NavLink
                                        to="/manage"
                                        className={({ isActive }) => (isActive ? styles.headerNavPageLinkActive : styles.headerNavPageLink)}
                                        onClick={() => setMenuOpen(false)}
                                    >
                                        {t("admin")}
                                    </NavLink>
                                </li>
                            )}
                            <li>
                                <NavLink
                                    to="/help"
                                    className={({ isActive }) => (isActive ? styles.headerNavPageLinkActive : styles.headerNavPageLink)}
                                    onClick={() => setMenuOpen(false)}
                                >
                                    {t("help")}
                                </NavLink>
                            </li>
                            <li>
                                {isAuthenticated ? (
                                    <NavLink
                                        to="/login"
                                        className={({ isActive }) => (isActive ? styles.headerNavPageLinkActive : styles.headerNavPageLink)}
                                        onClick={handleLogout}
                                    >
                                        {t("Logout")}
                                    </NavLink>
                                ) : (
                                    <NavLink
                                        to="/login"
                                        className={({ isActive }) => (isActive ? styles.headerNavPageLinkActive : styles.headerNavPageLink)}
                                        onClick={() => setMenuOpen(false)}
                                    >
                                        {t("Login")}
                                    </NavLink>
                                )}
                            </li>
                        </ul>
                    </nav>
                    <div className={styles.loginMenuContainer}>
                        <IconButton
                            iconProps={{ iconName: "GlobalNavButton" }}
                            className={styles.menuToggle}
                            onClick={toggleMenu}
                            ariaLabel={t("labels.toggleMenu")}
                        />
                    </div>
                </div>
            </header>

            <Outlet context={{ userRole }} />
        </div>
    );
};

export default Layout;
