import { renderToStaticMarkup } from "react-dom/server";
import { getCitationFilePath } from "../../api";

type HtmlParsedAnswer = {
    answerHtml: string;
    citations: string[];
};

export function parseAnswerToHtml(answer: string, isStreaming: boolean, onCitationClicked: (citationFilePath: string) => void): HtmlParsedAnswer {
    const citations: string[] = [];

    // trim any whitespace from the end of the answer after removing follow-up questions
    let parsedAnswer = answer.trim();

    // Omit a citation that is still being typed during streaming
    if (isStreaming) {
        let lastIndex = parsedAnswer.length;
        for (let i = parsedAnswer.length - 1; i >= 0; i--) {
            if (parsedAnswer[i] === "]") {
                break;
            } else if (parsedAnswer[i] === "[") {
                lastIndex = i;
                break;
            }
        }
        const truncatedAnswer = parsedAnswer.substring(0, lastIndex);
        parsedAnswer = truncatedAnswer;
    }

    const parts = parsedAnswer.split(/(\[[^\]]+\]\.pdf|\[[^\]]+\])/g); // Match citations

    const fragments: string[] = parts.map((part, index) => {
        if (index % 2 === 0) {
            return part;
        } else {
            let citation = part.trim();

            // Remove enclosing brackets for citation processing
            citation = citation.replace(/^\[|\]$/g, ""); // Removes "[" and "]" at the start/end

            // Ensure no "[" exists in the citation content
            if (citation.startsWith("[")) {
                citation = citation.slice(1);
            }

            let citationIndex: number;
            if (citations.indexOf(citation) !== -1) {
                citationIndex = citations.indexOf(citation) + 1;
            } else {
                citations.push(citation);
                citationIndex = citations.length;
            }

            const path = getCitationFilePath(citation);

            return renderToStaticMarkup(
                <a className="supContainer" title={citation} onClick={() => onCitationClicked(path)}>
                    <sup>{citationIndex}</sup>
                </a>
            );
        }
    });

    return {
        answerHtml: fragments.join(""),
        citations
    };
}
