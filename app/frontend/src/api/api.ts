const BACKEND_URI = "https://app-backend-s6dpoygxjklmi.azurewebsites.net";

import { ChatAppResponse, ChatAppResponseOrError, ChatAppRequest, Config, SimpleAPIResponse } from "./models";
import { useLogin, getToken, isUsingAppServicesLogin } from "../authConfig";

export async function getHeaders(idToken: string | undefined): Promise<Record<string, string>> {
    const token = idToken || localStorage.getItem("access_token");
    if (token) {
        return { Authorization: `Bearer ${token}` };
    }

    return {};
}

export async function configApi(): Promise<Config> {
    const response = await fetch(`${BACKEND_URI}/config`, {
        method: "GET"
    });

    return (await response.json()) as Config;
}

export async function askApi(request: ChatAppRequest, idToken: string | undefined): Promise<ChatAppResponse> {
    const headers = await getHeaders(idToken);
    const response = await fetch(`${BACKEND_URI}/ask`, {
        method: "POST",
        headers: { ...headers, "Content-Type": "application/json" },
        body: JSON.stringify(request)
    });

    if (response.status > 299 || !response.ok) {
        throw Error(`Request failed with status ${response.status}`);
    }
    const parsedResponse: ChatAppResponseOrError = await response.json();
    if (parsedResponse.error) {
        throw Error(parsedResponse.error);
    }

    return parsedResponse as ChatAppResponse;
}

export async function chatApi(request: ChatAppRequest, shouldStream: boolean, idToken: string | undefined): Promise<Response> {
    let url = `/chat`;
    if (shouldStream) {
        url += "/stream";
    }
    const headers = await getHeaders(idToken);
    return await fetch(url, {
        method: "POST",
        headers: { ...headers, "Content-Type": "application/json" },
        body: JSON.stringify(request)
    });
}

export async function getSpeechApi(text: string): Promise<string | null> {
    return await fetch("/speech", {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify({
            text: text
        })
    })
        .then(response => {
            if (response.status == 200) {
                return response.blob();
            } else if (response.status == 400) {
                console.log("Speech synthesis is not enabled.");
                return null;
            } else {
                console.error("Unable to get speech synthesis.");
                return null;
            }
        })
        .then(blob => (blob ? URL.createObjectURL(blob) : null));
}

export function getCitationFilePath(citation: string): string {
    return `${BACKEND_URI}/content/${citation}`;
}

export async function uploadFileApi(request: FormData, idToken: string): Promise<SimpleAPIResponse> {
    const response = await fetch("/upload", {
        method: "POST",
        headers: await getHeaders(idToken),
        body: request
    });

    if (!response.ok) {
        throw new Error(`Uploading files failed: ${response.statusText}`);
    }

    const dataResponse: SimpleAPIResponse = await response.json();
    return dataResponse;
}

export async function deleteUploadedFileApi(filename: string, idToken: string): Promise<SimpleAPIResponse> {
    const headers = await getHeaders(idToken);
    const response = await fetch("/delete_uploaded", {
        method: "POST",
        headers: { ...headers, "Content-Type": "application/json" },
        body: JSON.stringify({ filename })
    });

    if (!response.ok) {
        throw new Error(`Deleting file failed: ${response.statusText}`);
    }

    const dataResponse: SimpleAPIResponse = await response.json();
    return dataResponse;
}

// export async function listUploadedFilesApi(idToken: string): Promise<string[]> {
//     const response = await fetch(`/list_uploaded`, {
//         method: "GET",
//         headers: await getHeaders(idToken)
//     });

//     if (!response.ok) {
//         throw new Error(`Listing files failed: ${response.statusText}`);
//     }

//     const dataResponse: string[] = await response.json();
//     return dataResponse;
// }
export async function downloadFileApi(filename: string, idToken: string): Promise<void> {
    const headers = await getHeaders(idToken);

    // Open the new tab early to avoid browser popup blockers
    const newTab = window.open("", "_blank");

    if (!newTab) {
        throw new Error("Unable to open new tab. Check browser settings or popup blocker.");
    }

    try {
        const url = `/content/${filename}?token=${encodeURIComponent(idToken)}`;
        newTab.location.href = url;
    } catch (err) {
        newTab.close();
    }
}

export async function rebuildIndexApi(idToken: string): Promise<SimpleAPIResponse> {
    const headers = await getHeaders(idToken);

    const response = await fetch("/rebuild_index", {
        method: "POST",
        headers: { ...headers, "Content-Type": "application/json" }
    });

    if (!response.ok) {
        throw new Error(`Rebuild index failed: ${response.statusText}`);
    }

    const dataResponse: SimpleAPIResponse = await response.json();
    return dataResponse;
}

export async function listUploadedFilesApi(idToken: string): Promise<string[]> {
    try {
        const response = await fetch(`/list_uploaded`, {
            method: "GET",
            headers: await getHeaders(idToken)
        });

        if (!response.ok) {
            throw new Error(`Listing files failed: ${response.statusText}`);
        }

        const dataResponse = await response.json();

        if (dataResponse && Array.isArray(dataResponse.blobs)) {
            return dataResponse.blobs;
        } else {
            throw new Error("Invalid response structure: 'blobs' array not found.");
        }
    } catch (error) {
        console.error("API call failed, returning mock data:", error);
        return [];
    }
}

export async function rerunIndex(idToken: string): Promise<SimpleAPIResponse> {
    const headers = await getHeaders(idToken);

    const response = await fetch("/rerun_index", {
        method: "POST",
        headers: { ...headers, "Content-Type": "application/json" }
    });

    if (!response.ok) {
        throw new Error(`Rerun index failed: ${response.statusText}`);
    }

    const dataResponse: SimpleAPIResponse = await response.json();
    return dataResponse;
}

export async function listLookupFiles(idToken: string, query: string): Promise<string[]> {
    try {
        const response = await fetch(`/lookup`, {
            method: "POST",
            headers: {
                ...(await getHeaders(idToken)),
                "Content-Type": "application/json"
            },
            body: JSON.stringify({ query })
        });

        if (!response.ok) {
            throw new Error(`Listing files failed: ${response.statusText}`);
        }

        const dataResponse = await response.json();

        if (dataResponse && Array.isArray(dataResponse)) {
            return dataResponse;
        } else {
            throw new Error("Invalid response structure: 'blobs' array not found.");
        }
    } catch (error) {
        console.error("API call failed, returning mock data:", error);
        return [];
    }
}
export async function loginApi(username: string, password: string): Promise<string> {
    try {
        const response = await fetch(`${BACKEND_URI}/login`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({ username, password })
        });

        if (!response.ok) {
            throw new Error(`Login failed: ${response.statusText}`);
        }

        const dataResponse = await response.json();

        if (!dataResponse.access_token) {
            throw new Error("Token not found in response.");
        }

        return dataResponse.access_token;
    } catch (error) {
        console.error("Error during login:", error);
        throw error;
    }
}
