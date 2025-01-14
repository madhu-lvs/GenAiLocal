import { ArrowDownload24Regular } from "@fluentui/react-icons";
import { Button } from "@fluentui/react-components";
import { useTranslation } from "react-i18next";
import JSZip from "jszip";
import { saveAs } from "file-saver";
import { jsPDF } from "jspdf";

import styles from "./SnapshotButton.module.css";
import { parseAnswerToHtml } from "../../components/Answer/AnswerParser";
import { getCitationFilePath } from "../../api";
import { useLogin, getToken } from "../../authConfig";
import { useMsal } from "@azure/msal-react";

interface Props {
    className?: string;
    answers: [string, any][];
    onSnapshotGenerated?: () => void; // Optional callback after snapshot is generated
    disabled?: boolean;
}

export const SnapshotButton = ({ className, answers, onSnapshotGenerated, disabled }: Props) => {
    const { t } = useTranslation();
    const client = useLogin ? useMsal().instance : undefined;
    const generatePdf = (title: string, dataCallback: (doc: jsPDF, pageWidth: number, pageHeight: number, margin: number, lineHeight: number) => void) => {
        const doc = new jsPDF();
        doc.setFontSize(16);
        doc.text(title, 10, 10);

        const pageWidth = doc.internal.pageSize.getWidth();
        const pageHeight = doc.internal.pageSize.getHeight();
        const margin = 10;
        const lineHeight = 10;
        let yPosition = 20;

        dataCallback(doc, pageWidth, pageHeight, margin, lineHeight);
        return doc.output("blob");
    };

    const generateChatHistoryPdf = () => {
        return generatePdf("Chat History Snapshot", (doc, pageWidth, pageHeight, margin, lineHeight) => {
            let yPosition = 20;

            answers.forEach((chat, index) => {
                const question = `Q${index + 1}: ${chat[0]}`;
                const response = `A${index + 1}: ${chat[1]?.message.content || ""}`;
                const questionLines = doc.splitTextToSize(question, pageWidth - margin * 2);
                const responseLines = doc.splitTextToSize(response, pageWidth - margin * 2);

                [...questionLines, ...responseLines].forEach(line => {
                    if (yPosition + lineHeight > pageHeight - margin) {
                        doc.addPage();
                        yPosition = margin;
                    }
                    doc.text(line, margin, yPosition);
                    yPosition += lineHeight;
                });

                yPosition += lineHeight;
            });
        });
    };

    const generateThoughtProcessPdf = () => {
        return generatePdf("Thought Process Snapshot", (doc, pageWidth, pageHeight, margin, lineHeight) => {
            let yPosition = 20;

            answers.forEach((chat, index) => {
                const question = `Q${index + 1}: ${chat[0]}`;
                const thoughts = chat[1]?.context?.thoughts || "No thought process available.";
                const thoughtsContent = typeof thoughts === "object" ? JSON.stringify(thoughts, null, 2) : thoughts;

                const questionLines = doc.splitTextToSize(question, pageWidth - margin * 2);
                const thoughtsLines = doc.splitTextToSize(`Thought Process:\n${thoughtsContent}`, pageWidth - margin * 2);

                [...questionLines, ...thoughtsLines].forEach(line => {
                    if (yPosition + lineHeight > pageHeight - margin) {
                        doc.addPage();
                        yPosition = margin;
                    }
                    doc.text(line, margin, yPosition);
                    yPosition += lineHeight;
                });

                yPosition += lineHeight;
            });
        });
    };

    const generateSupportingContentPdf = () => {
        return generatePdf("Supporting Content Snapshot", (doc, pageWidth, pageHeight, margin, lineHeight) => {
            let yPosition = 20;

            answers.forEach((chat, index) => {
                const userQuestion = `Q${index + 1}: ${chat[0]}`;
                const dataPoints = chat[1]?.context?.data_points || {};

                const questionLines = doc.splitTextToSize(userQuestion, pageWidth - margin * 2);
                questionLines.forEach((line: string) => {
                    if (yPosition + lineHeight > pageHeight - margin) {
                        doc.addPage();
                        yPosition = margin;
                    }
                    doc.text(line, margin, yPosition);
                    yPosition += lineHeight;
                });

                Object.entries(dataPoints).forEach(([key, value]) => {
                    const titleLines = doc.splitTextToSize(`Title: ${key}`, pageWidth - margin * 2);
                    const contentLines = doc.splitTextToSize(`Content: ${JSON.stringify(value, null, 2)}`, pageWidth - margin * 2);

                    [...titleLines, ...contentLines].forEach(line => {
                        if (yPosition + lineHeight > pageHeight - margin) {
                            doc.addPage();
                            yPosition = margin;
                        }
                        doc.text(line, margin, yPosition);
                        yPosition += lineHeight;
                    });

                    yPosition += lineHeight;
                });

                yPosition += lineHeight;
            });
        });
    };

    const fetchCitations = async (zip: JSZip) => {
        const citationPromises = answers.flatMap((chat, index) => {
            const parsedAnswer = parseAnswerToHtml(chat[1]?.message.content || "", false, () => {});
            return parsedAnswer.citations.map(async citation => {
                const filePath = getCitationFilePath(citation);
                if (filePath.endsWith(".pdf")) {
                    const token = client ? await getToken(client) : undefined;
                    const response = await fetch(filePath, {
                        method: "GET",
                        headers: token ? { Authorization: `Bearer ${token}` } : undefined
                    });

                    if (response.ok) {
                        const blob = await response.blob();
                        const fileName = `Citation-${index + 1}-${citation.replace(/[^\w-]/g, "_")}.pdf`;
                        zip.file(fileName, blob, { binary: true });
                    }
                }
            });
        });

        await Promise.all(citationPromises);
    };

    const handleDownloadSnapshot = async () => {
        const zip = new JSZip();

        // Add Chat History PDF
        const chatHistoryBlob = generateChatHistoryPdf();
        zip.file("Chat-History.pdf", chatHistoryBlob, { binary: true });

        // Add Thought Process PDF
        // const thoughtProcessBlob = generateThoughtProcessPdf();
        // zip.file("Thought-Process.pdf", thoughtProcessBlob, { binary: true });

        // Add Supporting Content PDF
        const supportingContentBlob = generateSupportingContentPdf();
        zip.file("Supporting-Content.pdf", supportingContentBlob, { binary: true });

        // Fetch and include citation PDFs
        await fetchCitations(zip);

        // Generate and download ZIP
        const zipBlob = await zip.generateAsync({ type: "blob" });
        const timestamp = new Date().toISOString().replace(/[:.]/g, "-");

        const filename = `Snapshot_${timestamp}.zip`;
        saveAs(zipBlob, filename);

        if (onSnapshotGenerated) onSnapshotGenerated();
    };

    return (
        <div className={`${styles.container} ${className ?? ""}`}>
            <Button icon={<ArrowDownload24Regular />} disabled={disabled} onClick={handleDownloadSnapshot}>
                {t("Snapshot")}
            </Button>
        </div>
    );
};
