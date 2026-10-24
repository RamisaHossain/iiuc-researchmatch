
const researchText = document.getElementById("researchText");
const analyzeButton = document.getElementById("analyzeButton");
const matchButton = document.getElementById("matchButton");
const statusMessage = document.getElementById("status");

const analysisSection = document.getElementById("analysisSection");
const matchesSection = document.getElementById("matchesSection");

const topicInput = document.getElementById("topic");
const keywordsInput = document.getElementById("keywords");
const matchesContainer = document.getElementById("matches");

let currentAnalysis = null;


function showStatus(message, isError = false) {
    statusMessage.textContent = message;
    statusMessage.classList.toggle("error", isError);
}


function setLoading(button, loading, loadingText, normalText) {
    button.disabled = loading;
    button.textContent = loading ? loadingText : normalText;
}


analyzeButton.addEventListener("click", async () => {
    const text = researchText.value.trim();

    if (!text) {
        showStatus("Please enter your research idea first.", true);
        researchText.focus();
        return;
    }

    setLoading(
        analyzeButton,
        true,
        "Analyzing with local Gemma 4...",
        "Analyze research idea"
    );

    showStatus(
        "Gemma 4 is analyzing your idea locally. This may take a few minutes on your computer."
    );

    analysisSection.hidden = true;
    matchesSection.hidden = true;

    try {
        const response = await fetch("/api/analyze", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({ text })
        });

        const result = await response.json();

        if (!response.ok || !result.success) {
            throw new Error(result.error || "Research analysis failed.");
        }

        currentAnalysis = result.analysis;

        topicInput.value = currentAnalysis.research_topic || "";
        keywordsInput.value = (
            currentAnalysis.keywords || []
        ).join(", ");

        analysisSection.hidden = false;
        showStatus(
            "Analysis complete. Review the topic and keywords before matching."
        );

        analysisSection.scrollIntoView({
            behavior: "smooth",
            block: "start"
        });

    } catch (error) {
        showStatus(
            "Could not analyze the idea: " + error.message,
            true
        );
    } finally {
        setLoading(
            analyzeButton,
            false,
            "Analyzing with local Gemma 4...",
            "Analyze research idea"
        );
    }
});


matchButton.addEventListener("click", async () => {
    const topic = topicInput.value.trim();
    const keywords = keywordsInput.value
        .split(",")
        .map(word => word.trim())
        .filter(Boolean);

    if (!topic && keywords.length === 0) {
        showStatus(
            "Please provide a research topic or at least one keyword.",
            true
        );
        return;
    }

    const matchingText = [
        topic,
        researchText.value.trim(),
        ...(currentAnalysis?.methods || []),
        ...(currentAnalysis?.skills || []),
        ...keywords
    ].filter(Boolean).join(" ");

    setLoading(
        matchButton,
        true,
        "Finding matches...",
        "Find faculty matches"
    );

    showStatus("Comparing your research profile with faculty profiles.");

    matchesSection.hidden = true;
    matchesContainer.replaceChildren();

    try {
        const response = await fetch("/api/match", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({ text: matchingText })
        });

        const result = await response.json();

        if (!response.ok || !result.success) {
            throw new Error(result.error || "Faculty matching failed.");
        }

        displayMatches(result.matches || []);

        matchesSection.hidden = false;

        if (result.demo_data) {
            showStatus(
                "Matches generated using fictional demonstration profiles."
            );
        } else {
            showStatus("Matching complete.");
        }

        matchesSection.scrollIntoView({
            behavior: "smooth",
            block: "start"
        });

    } catch (error) {
        showStatus(
            "Could not find matches: " + error.message,
            true
        );
    } finally {
        setLoading(
            matchButton,
            false,
            "Finding matches...",
            "Find faculty matches"
        );
    }
});


function displayMatches(matches) {
    matchesContainer.replaceChildren();

    if (matches.length === 0) {
        const message = document.createElement("p");
        message.textContent = "No faculty profiles are available yet.";
        matchesContainer.appendChild(message);
        return;
    }

    matches.forEach((match, index) => {
        const card = document.createElement("article");
        card.className = "match-card";

        const heading = document.createElement("h3");
        heading.textContent = `${index + 1}. ${match.name}`;

        const department = document.createElement("p");
        department.textContent = match.department;

        const score = document.createElement("span");
        score.className = "score";
        score.textContent =
            `${match.similarity_score}% text similarity`;

        const areas = document.createElement("p");
        areas.textContent =
            "Research areas: " +
            (match.research_areas || []).join(", ");

        const termsTitle = document.createElement("p");
        termsTitle.textContent = "Shared words:";

        card.append(heading, department, score, areas, termsTitle);

        const terms = match.shared_terms || [];

        if (terms.length === 0) {
            const none = document.createElement("p");
            none.textContent = "No exact shared words found.";
            card.appendChild(none);
        } else {
            terms.forEach(term => {
                const tag = document.createElement("span");
                tag.className = "term";
                tag.textContent = term;
                card.appendChild(tag);
            });
        }

        matchesContainer.appendChild(card);
    });
}



const chatForm = document.getElementById("chatForm");
const chatInput = document.getElementById("chatInput");
const chatMessages = document.getElementById("chatMessages");
const chatSend = document.getElementById("chatSend");
const chatStatus = document.getElementById("chatStatus");

const chatHistory = [];

function addChatMessage(role, content) {
    const bubble = document.createElement("div");
    bubble.className =
        "chat-bubble " +
        (role === "user" ? "user-bubble" : "assistant-bubble");
    bubble.textContent = content;
    chatMessages.appendChild(bubble);
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

chatForm.addEventListener("submit", async (event) => {
    event.preventDefault();

    const message = chatInput.value.trim();

    if (!message) return;

    addChatMessage("user", message);
    chatInput.value = "";
    chatSend.disabled = true;
    chatStatus.textContent =
        "Gemma 4 is thinking locally. This may take a few minutes.";

    try {
        const response = await fetch("/api/chat", {
            method: "POST",
            headers: {"Content-Type": "application/json"},
            body: JSON.stringify({
                message,
                history: chatHistory.slice(-10)
            })
        });

        const result = await response.json();

        if (!response.ok || !result.success) {
            throw new Error(result.error || "Chat request failed.");
        }

        addChatMessage("assistant", result.answer);

        chatHistory.push(
            {role: "user", content: message},
            {role: "assistant", content: result.answer}
        );

        chatStatus.textContent = "Answer generated by your local model.";
    } catch (error) {
        addChatMessage(
            "assistant",
            "Sorry, the answer could not be generated. " + error.message
        );
        chatStatus.textContent = "Chat request failed.";
    } finally {
        chatSend.disabled = false;
        chatInput.focus();
    }
});
