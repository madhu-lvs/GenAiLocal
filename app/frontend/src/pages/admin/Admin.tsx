import { useContext, useEffect, useRef, useState } from "react";
import { useTranslation } from "react-i18next";
import { Helmet } from "react-helmet-async";
import { useMsal } from "@azure/msal-react";
import { useId } from "@fluentui/react-hooks";
import { LoginContext } from "../../loginContext";

export function Component(): JSX.Element {
    // Preserve all the hooks to maintain dependencies
    const [isConfigPanelOpen, setIsConfigPanelOpen] = useState(false);
    const [promptTemplate, setPromptTemplate] = useState<string>("");
    const [temperature, setTemperature] = useState<number>(0.7);
    const [seed, setSeed] = useState<number | null>(null);
    const [minimumRerankerScore, setMinimumRerankerScore] = useState<number>(0.02);
    const [minimumSearchScore, setMinimumSearchScore] = useState<number>(0.02);
    const [retrieveCount, setRetrieveCount] = useState<number>(5);
    const [useSemanticRanker, setUseSemanticRanker] = useState<boolean>(true);
    const [useSemanticCaptions, setUseSemanticCaptions] = useState<boolean>(false);
    const [excludeCategory, setExcludeCategory] = useState<string>("");
    const [question, setQuestion] = useState<string>("");
    const [useOidSecurityFilter, setUseOidSecurityFilter] = useState<boolean>(false);
    const [useGroupsSecurityFilter, setUseGroupsSecurityFilter] = useState<boolean>(false);
    const [isLoading, setIsLoading] = useState<boolean>(false);
    const [error, setError] = useState<unknown>();
    const audio = useRef(new Audio()).current;
    const [isPlaying, setIsPlaying] = useState(false);
    const lastQuestionRef = useRef<string>("");

    const client = useMsal().instance;
    const { loggedIn } = useContext(LoginContext);
    const { t, i18n } = useTranslation();

    useEffect(() => {
        // Keep empty useEffect to maintain component lifecycle
    }, []);

    return <div className="flex items-center justify-center min-h-screen text-4xl font-bold">ADMIN</div>;
}

Component.displayName = "Admin";

export default Component;
