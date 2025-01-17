import { useEffect, useState } from "react";
import { Helmet } from "react-helmet-async";
import styles from "./Help.module.css";

export function Component(): JSX.Element {
    const [activeTab, setActiveTab] = useState("generativeAI"); // State to manage active tab

    useEffect(() => {}, []);

    return (
        <div style={{ display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", minHeight: "100vh", padding: "20px" }}>
            <Helmet>
                <title>Help with AI FAQs</title>
            </Helmet>

            <div className="navbar">
                <button onClick={() => setActiveTab("generativeAI")} className={`${styles.tabButton} ${activeTab === "generativeAI" ? styles.active : ""}`}>
                    Generative AI FAQ
                </button>
                <button
                    onClick={() => setActiveTab("promptOptimization")}
                    className={`${styles.tabButton} ${activeTab === "promptOptimization" ? styles.active : ""}`}
                >
                    Prompt Optimization FAQ
                </button>
            </div>
            <div className={styles.card} style={{ marginTop: 20 }}>
                {activeTab === "generativeAI" && (
                    <div>
                        <p>
                            <strong>Q: What are some common uses of generative AI?</strong>
                            <br />
                            A: Generative AI is commonly used to improve work, automate repetitive tasks, summarize meetings and customer engagements, and
                            synthesize information.
                        </p>
                        <p>
                            <strong>Q: How does generative AI typically work?</strong>
                            <br />
                            A: Generative AI relies on natural language processing (NLP) to understand requests and generate relevant results based on pattern
                            recognition and pattern assembly.
                        </p>
                        <p>
                            <strong>Q: What mindset shift is necessary to use AI creatively?</strong>
                            <br />
                            A: The necessary mindset shift involves recognizing AI as a partner in innovation and exploring the unfamiliar, rather than just a
                            tool for predictable results.
                        </p>
                        <p>
                            <strong>Q: How can AI enhance competitiveness?</strong>
                            <br />
                            A: AI can enhance competitiveness by making tasks more efficient, scalable, less expensive, and more automated. It also supercharges
                            capabilities to achieve what was previously impossible.
                        </p>
                        <p>
                            <strong>Q: What are some practical applications of Generative AI?</strong>
                            <br />
                            A: Generative AI can assist in writing, researching, summarizing, translating, and coding.
                        </p>
                        <p>
                            <strong>Q: How can individuals work more creatively with AI?</strong>
                            <br />
                            A: Here are twelve ways to enhance creativity with AI:
                            <ol>
                                <li>Setting a daily "exploratory prompting" practice.</li>
                                <li>Framing prompts around "What if" and "How might we" questions.</li>
                                <li>Embracing ambiguity and curiosity in prompts.</li>
                                <li>Using prompts to explore rather than solve.</li>
                                <li>Chaining prompts to develop ideas iteratively.</li>
                                <li>Thinking metaphorically or analogically.</li>
                                <li>Prompting for perspectives beyond facts.</li>
                                <li>Experimenting with "role-play" prompts.</li>
                                <li>Asking for impossibilities and involving experiential scenarios.</li>
                                <li>Reimagining AI's role in the solution itself.</li>
                                <li>Establishing a weekly "future-driven prompt" session.</li>
                                <li>Keeping a journal of "breakthrough prompts."</li>
                            </ol>
                        </p>
                        <p>
                            <strong>Q: How does AI enhance today's work while unlocking tomorrow's opportunities?</strong>
                            <br />
                            A: AI enhances today's work by making tasks more efficient, scalable, less expensive, and more automated. It also unlocks tomorrow's
                            opportunities by supercharging capabilities to achieve what was previously impossible.
                        </p>
                        <p>
                            <strong>Q: How can AI be used to break free from linear transactions to more creative outcomes?</strong>
                            <br />
                            A: AI can be used to break free from linear transactions by creating unique outcomes through human and machine collaboration. For
                            instance, AI can assist researchers by analyzing vast amounts of data to identify unique patterns and insights, or by generating new
                            hypotheses based on existing research findings. This collaborative approach can lead to more creative and groundbreaking
                            discoveries.
                        </p>
                        <p>
                            <strong>Q: What is the importance of rethinking collaboration with AI for more creative outcomes?</strong>
                            <br />
                            A: Rethinking collaboration with AI is important because it involves the willingness to explore the unknown, learn, unlearn, and
                            experiment. It allows for more creative and innovative outcomes by treating AI as a collaborative partner rather than just a tool.
                        </p>
                        <p>
                            <strong>Q: What is the concept of "WWAID" and how does it help in using AI creatively?</strong>
                            <br />
                            A: "WWAID" stands for "What would AI do?" It helps in using AI creatively by encouraging users to step aside from their cognitive
                            biases and open themselves up to new exchanges and experiences, yielding unexpected results.
                        </p>
                        <p>
                            <strong>Q: How can individuals foster a culture of creativity and innovation with AI?</strong>
                            <br />
                            A: Individuals can foster a culture of creativity and innovation with AI by embracing mindshifts in their own approach, using AI as
                            a collaborative partner, and challenging their own assumptions to see possibilities that others might miss. This creates an
                            environment where "the impossible" becomes a daily challenge and achievement.
                        </p>
                        <p>
                            <strong>Q: How does generative AI work?</strong>
                            <br />
                            A: Generative AI models are sophisticated pattern recognition and imitation tools. They are typically trained on large amounts of
                            sample data, often collected through web-scraping tools. These models learn through observation and pattern matching.
                        </p>
                        <p>
                            <strong>Q: What are Large Language Models (LLMs)?</strong>
                            <br />
                            A: Large Language Models (LLMs) are generative AI models that can predict words likely to come next based on the user’s prompt and
                            the text generated so far. They are flexible and can respond to the same prompt with different responses based on patterns
                            identified from their training data.
                        </p>
                    </div>
                )}
                {activeTab === "promptOptimization" && (
                    <div>
                        <p>
                            <strong>Q: What is prompt optimization?</strong>
                            <br />
                            A: Prompt optimization is the art of crafting effective prompts to guide AI behavior. It involves designing inputs that clearly
                            convey the task to the AI, ensuring accurate and relevant responses. This process is crucial for maximizing the potential of AI
                            tools, as the quality of the prompt directly influences the output.
                        </p>
                        <p>
                            <strong>Q: Why are well-structured prompts important?</strong>
                            <br />
                            A: Well-structured prompts ensure that the AI understands the task clearly and produces accurate, relevant, and high-quality
                            responses. They provide clear task context, specific output expectations, and necessary details, which guide the AI effectively.
                        </p>
                        <p>
                            <strong>Q: What are the key elements of a prompt?</strong>
                            <br />
                            A: The key elements of a prompt include the task, context, expectations, and output. These elements help the AI understand what
                            needs to be done, the data to be acted on, the goals and expectations for the response, and the desired format of the output.
                        </p>
                        <p>
                            <strong>Q: What are some principles of effective prompt design?</strong>
                            <br />
                            A: Effective prompt design involves clarity and specificity, avoiding vague language, ensuring contextual relevance, and considering
                            the intended audience. Clear and specific prompts help the AI understand the task, while relevant prompts ensure high-quality
                            output.
                        </p>
                        <p>
                            <strong>Q: What are common pitfalls in prompt design and how can they be avoided?</strong>
                            <br />
                            A: Common pitfalls include vague or ambiguous language, overly complex prompts, and open-ended prompts. These can be avoided by
                            using clear and specific language, keeping prompts simple and manageable, and providing clear guidelines and examples for responses.
                        </p>
                        <p>
                            <strong>Q: How can output formatting improve prompt optimization?</strong>
                            <br />
                            A: Output formatting specifies how you want the AI’s response to be structured. By clearly defining the desired format, style, and
                            length of the output, you can enhance the readability and usability of the AI's responses, making them more aligned with your
                            specific needs and objectives.
                        </p>
                        <p>
                            <strong>Q: What are some do's and don'ts of prompting?</strong>
                            <br />
                            A: Do's include being clear and specific, providing necessary context, and setting clear expectations. Don'ts include using vague
                            language, creating overly complex prompts, and relying on open-ended prompts without clear guidelines.
                        </p>
                        <p>
                            <strong>Resource Document:</strong>
                            <br />
                            <a href="/static/docs/PromptOptimizationGuide.pdf" target="_blank" rel="noopener noreferrer">
                                Open or Download PDF
                            </a>
                        </p>
                    </div>
                )}
            </div>
        </div>
    );
}

Component.displayName = "Help";

export default Component;
