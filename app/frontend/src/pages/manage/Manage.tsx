import React, { useState, useEffect } from "react";
import { Helmet } from "react-helmet-async";
import styles from "./Manage.module.css";
import { listUploadedFilesApi, uploadFileApi, deleteUploadedFileApi, downloadFileApi, rebuildIndexApi, rerunIndex } from "../../api";

export function Component(): JSX.Element {
    const [searchQuery, setSearchQuery] = useState<string>("");
    const [searchResults, setSearchResults] = useState<any[]>([]);
    const [isLoading, setIsLoading] = useState<boolean>(false);
    const [isRebuilding, setIsRebuilding] = useState<boolean>(false);
    const [error, setError] = useState<string | null>(null);
    const [apiData, setApiData] = useState<string[]>([]);
    const [currentPage, setCurrentPage] = useState<number>(1);
    const [uploading, setUploading] = useState<boolean>(false);
    const [deleting, setDeleting] = useState<boolean>(false);
    const [uploadStatus, setUploadStatus] = useState<{ [key: string]: string }>({});

    const resultsPerPage = 10;

    useEffect(() => {
        const fetchData = async () => {
            setIsLoading(true);
            try {
                const files = await listUploadedFilesApi("");
                setApiData(files || []);
                setSearchResults(files || []);
                setIsLoading(false);
            } catch (err) {
                setError("Failed to fetch data. Please try again later.");
                setIsLoading(false);
            }
        };

        fetchData();
    }, []);

    const handleInputChange = (event: React.ChangeEvent<HTMLInputElement>) => {
        setSearchQuery(event.target.value);
    };

    const handleSearch = (event: React.FormEvent<HTMLFormElement>) => {
        event.preventDefault();

        setIsLoading(true);
        setError(null);

        setTimeout(() => {
            // If the search query is empty, reset the search results to all data
            const filteredResults = searchQuery.trim() ? apiData.filter(item => item.toLowerCase().includes(searchQuery.toLowerCase())) : apiData;

            setSearchResults(filteredResults);
            setCurrentPage(1);
            setIsLoading(false);

            if (filteredResults.length === 0) {
            }
        }, 500);
    };

    const handleFileUpload = async (event: React.ChangeEvent<HTMLInputElement>) => {
        const files = Array.from(event.target.files || []);
        if (files.length === 0) return;

        setUploading(true);
        setError(null);
        const updatedStatus: { [key: string]: string } = {};

        const idToken = ""; // Replace with logic to fetch ID token if needed
        let allUploadsSuccessful = true; // Track if all uploads are successful

        for (const file of files) {
            if (file.type !== "application/pdf" && file.type !== "application/vnd.openxmlformats-officedocument.wordprocessingml.document") {
                updatedStatus[file.name] = "Invalid file type";
                setUploadStatus({ ...updatedStatus });
                allUploadsSuccessful = false; // Mark as failed if file type is invalid
                continue;
            }

            const formData = new FormData();
            formData.append("file", file);

            updatedStatus[file.name] = "Uploading...";
            setUploadStatus({ ...updatedStatus });

            try {
                await uploadFileApi(formData, idToken);
                updatedStatus[file.name] = "Uploaded successfully";

                const newFiles = await listUploadedFilesApi("");
                setApiData(newFiles || []);
                setSearchResults(newFiles || []);
            } catch (err) {
                console.error(`Error uploading file "${file.name}":`, err);
                updatedStatus[file.name] = "Upload failed";
                allUploadsSuccessful = false;
            }

            setUploadStatus({ ...updatedStatus });
        }

        setUploading(false);

        if (allUploadsSuccessful) {
            try {
                const rerunResponse = await rerunIndex(idToken);
                console.log("Index rerun successfully:", rerunResponse);
            } catch (error) {
                console.error("Error rerunning index:", error);
                setError("Failed to rerun index. Please try again.");
            }
        }
    };

    const handleDelete = async (filename: string) => {
        setDeleting(true);
        setError(null);

        try {
            const idToken = "";
            await deleteUploadedFileApi(filename, idToken);
            alert(`File "${filename}" deleted successfully!`);

            const updatedFiles = apiData.filter(file => file !== filename);
            setApiData(updatedFiles);
            setSearchResults(updatedFiles);
        } catch (err) {
            setError("File deletion failed. Please try again.");
        } finally {
            setDeleting(false);
        }
    };

    const handleView = async (filename: string) => {
        try {
            const idToken = "";
            await downloadFileApi(filename, idToken);
        } catch (err) {
            setError("File download failed. Please try again.");
        }
    };

    const handleRebuild = async () => {
        const userConfirmed = window.confirm(
            "Warning: This will reset the indexer and rebuild the index which can take up to 24 hours due to high volume of data. This should only be triggered in cases where some files have been deleted and are still picked up by the agent"
        );
        if (!userConfirmed) {
            return;
        }
        setIsRebuilding(true);
        setError(null);

        try {
            const idToken = "";
            const result = await rebuildIndexApi(idToken);
            alert(`Rebuild successful: ${result.message}`);
        } catch (err) {
            setError("Rebuild failed. Please try again.");
        } finally {
            setIsRebuilding(false);
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
                <title>Manage Files</title>
            </Helmet>
            <div className={styles.searchBox}>
                <div className={styles.topActions}>
                    <label className={styles.actionButton}>
                        <i className="fas fa-plus"></i> Add New File
                        <input type="file" multiple style={{ display: "none" }} onChange={handleFileUpload} disabled={uploading} />
                    </label>
                </div>
                <div className={styles.uploadStatus}>
                    {Object.entries(uploadStatus).map(([fileName, status], index) => (
                        <div key={index} className={status === "Upload failed" || status === "Invalid file type" ? styles.error : ""}>
                            {fileName}: {status}
                        </div>
                    ))}
                </div>
                <br />

                <h1 className={styles.searchTitle}>Manage Your Files</h1>
                <form onSubmit={handleSearch} className={styles.searchForm}>
                    <input type="text" placeholder="Enter search query..." value={searchQuery} onChange={handleInputChange} className={styles.searchInput} />
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
                                    <th>Title</th>
                                    <th>Actions</th>
                                </tr>
                            </thead>
                            <tbody>
                                {paginatedResults.map((result, index) => (
                                    <tr key={index}>
                                        <td>{result}</td>
                                        <td>
                                            <button className={styles.actionButton} onClick={() => handleDelete(result)} disabled={deleting}>
                                                <i className="fas fa-trash-alt"></i> Remove
                                            </button>
                                            <button className={styles.actionButton} onClick={() => handleView(result)}>
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
                <button className={styles.rebuild} onClick={handleRebuild} disabled={isLoading}>
                    {isRebuilding ? "Rebuilding..." : "Rebuild"}
                </button>
            </div>
        </div>
    );
}

Component.displayName = "Manage";

export default Component;
