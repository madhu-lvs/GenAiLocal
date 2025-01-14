import React, { useState } from "react";
import { loginApi } from "../../api";
import { useNavigate } from "react-router-dom";

export function Component(): JSX.Element {
    const [username, setUsername] = useState("");
    const [password, setPassword] = useState("");
    const [error, setError] = useState("");
    const [loading, setLoading] = useState(false);
    const navigate = useNavigate();

    const handleLogin = async (e: React.FormEvent) => {
        e.preventDefault();
        setError("");
        setLoading(true);

        try {
            const token = await loginApi(username, password);

            if (!token || token.trim() === "") {
                throw new Error("Invalid token received from server.");
            }

            localStorage.setItem("access_token", token);

            const tokenUpdatedEvent = new Event("tokenUpdated");
            window.dispatchEvent(tokenUpdatedEvent);

            setTimeout(() => {
                window.location.href = "/";
                setLoading(false);
            }, 1000);
        } catch (err: any) {
            setError(err.message || "Login failed. Please try again.");
        }
        // finally {
        //     setLoading(false);
        // }
    };

    return (
        <div
            style={{
                display: "flex",
                justifyContent: "center",
                alignItems: "flex-start",
                height: "100vh",
                paddingTop: "150px",
                backgroundColor: "#f5f5f5"
            }}
        >
            <form
                onSubmit={handleLogin}
                style={{
                    padding: "20px",
                    borderRadius: "8px",
                    boxShadow: "0 2px 4px rgba(0, 0, 0, 0.1)",
                    backgroundColor: "#fff",
                    maxWidth: "400px",
                    width: "100%"
                }}
            >
                <h2 style={{ textAlign: "center" }}>Login</h2>

                {error && <p style={{ color: "red", textAlign: "center" }}>{error}</p>}

                <div style={{ marginBottom: "15px" }}>
                    <label htmlFor="username" style={{ display: "block", marginBottom: "5px" }}>
                        Username
                    </label>
                    <input
                        type="text"
                        id="username"
                        value={username}
                        onChange={e => setUsername(e.target.value)}
                        style={{
                            width: "100%",
                            padding: "10px",
                            border: "1px solid #ccc",
                            borderRadius: "4px"
                        }}
                        required
                    />
                </div>

                <div style={{ marginBottom: "15px" }}>
                    <label htmlFor="password" style={{ display: "block", marginBottom: "5px" }}>
                        Password
                    </label>
                    <input
                        type="password"
                        id="password"
                        value={password}
                        onChange={e => setPassword(e.target.value)}
                        style={{
                            width: "100%",
                            padding: "10px",
                            border: "1px solid #ccc",
                            borderRadius: "4px"
                        }}
                        required
                    />
                </div>

                <button
                    type="submit"
                    disabled={loading}
                    style={{
                        width: "100%",
                        padding: "10px",
                        backgroundColor: "#ea0029",
                        color: "#fff",
                        border: "none",
                        borderRadius: "4px",
                        cursor: "pointer"
                    }}
                >
                    {loading ? "Logging in..." : "Login"}
                </button>

                <p
                    style={{
                        marginTop: "15px",
                        textAlign: "center",
                        fontSize: "14px",
                        color: "#555"
                    }}
                >
                    <a
                        href="/static/docs/NavigationGuide.pdf"
                        target="_blank"
                        rel="noopener noreferrer"
                        style={{ color: "#ea0029", textDecoration: "underline" }}
                    >
                        Check the navigation guide
                    </a>
                    .
                </p>
            </form>
        </div>
    );
}

Component.displayName = "Login";

export default Component;
