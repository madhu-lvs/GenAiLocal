import React, { useState, useEffect } from "react";
import { Helmet } from "react-helmet-async";
import styles from "./Lookup.module.css";
import { downloadFileApi } from "../../api";
import { listLookupFiles } from "../../api";

export function Component(): JSX.Element {
    const [searchQuery, setSearchQuery] = useState<string>("");
    const [searchResults, setSearchResults] = useState<any[]>([]);
    const [isLoading, setIsLoading] = useState<boolean>(false);
    const [error, setError] = useState<string | null>(null);
    const [currentPage, setCurrentPage] = useState<number>(1);
    const resultsPerPage = 10;

    const fetchFilteredData = async () => {
        setIsLoading(true);
        try {
            const idToken = "";
            const response = await listLookupFiles(idToken, searchQuery);

            const filteredData = response.map((item: any) => ({
                sourcePage: item.sourcepage,
                score: parseFloat(item.score.toFixed(4))
            }));
            setSearchResults(filteredData || []);
            setIsLoading(false);
        } catch (err) {
            console.error("Error fetching data:", err);
            setError("Failed to fetch data. Please try again later.");
            setIsLoading(false);
        }
    };

    const handleInputChange = (event: React.ChangeEvent<HTMLInputElement>) => {
        setSearchQuery(event.target.value);
    };

    const handleSearch = (event: React.FormEvent<HTMLFormElement>) => {
        event.preventDefault();

        if (!searchQuery.trim()) {
            setError("Please enter a search query.");
            setSearchResults([]);
            setCurrentPage(1);
            return;
        }

        fetchFilteredData();
    };

    const handleView = async (sourcePage: string) => {
        try {
            const idToken = "";
            await downloadFileApi(sourcePage, idToken);
        } catch (err) {
            setError("File download failed. Please try again.");
        }
    };

    const totalPages = Math.ceil(searchResults.length / resultsPerPage);
    const paginatedResults = searchResults?.slice((currentPage - 1) * resultsPerPage, currentPage * resultsPerPage);

    const handlePageChange = (page: number) => {
        if (page >= 1 && page <= totalPages) {
            setCurrentPage(page);
        }
    };

    return (
        <div className={styles.container}>
            <Helmet>
                <title>Search</title>
            </Helmet>
            <div className={styles.searchBox}>
                <h1 className={styles.searchTitle}>Search for specific content</h1>
                <form onSubmit={handleSearch} className={styles.searchForm}>
                    <input type="text" placeholder="Look specific content" value={searchQuery} onChange={handleInputChange} className={styles.searchInput} />
                    <button type="submit" className={styles.searchButton} disabled={isLoading}>
                        {isLoading ? "Searching..." : "Search"}
                    </button>
                </form>
                {error && <div className={styles.errorMessage}>{error}</div>}

                <div className={styles.searchResults}>
                    {paginatedResults.length > 0 && (
                        <table className={styles.resultsTable}>
                            <thead>
                                <tr>
                                    <th>Source Page</th>
                                    <th>Score</th>
                                    <th>Actions</th>
                                </tr>
                            </thead>
                            <tbody>
                                {paginatedResults.map((result, index) => (
                                    <tr key={index}>
                                        <td>{result.sourcePage}</td>
                                        <td>{result.score}</td>
                                        <td>
                                            <button className={styles.actionButton} onClick={() => handleView(result.sourcePage)}>
                                                <i className="fas fa-eye"></i> View
                                            </button>
                                        </td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    )}
                    {!isLoading && searchResults.length === 0 && searchQuery && (
                        <div className={styles.noResultsMessage}>No results found for "{searchQuery}".</div>
                    )}
                </div>
                <div className={styles.pagination}>
                    <button onClick={() => handlePageChange(currentPage - 1)} disabled={currentPage === 1} className={styles.pageButton}>
                        Previous
                    </button>
                    <span className={styles.pageIndicator}>
                        Page {currentPage} of {totalPages}
                    </span>
                    <button onClick={() => handlePageChange(currentPage + 1)} disabled={currentPage === totalPages} className={styles.pageButton}>
                        Next
                    </button>
                </div>
            </div>
        </div>
    );
}

Component.displayName = "Lookup";

export default Component;
