import { GoogleGenerativeAI } from "@google/generative-ai";
import { getGeminiApiKey } from "../lib/config";

/**
 * Retrieves the Gemini API key.
 * Preference order: env var (via config), then localStorage (dev fallback).
 */
export function getStoredApiKey() {
  const envKey = getGeminiApiKey();
  if (envKey) return envKey;
  return localStorage.getItem("CLOUDBOARD_GEMINI_KEY") || "";
}

export function setStoredApiKey(key) {
  if (key) {
    localStorage.setItem("CLOUDBOARD_GEMINI_KEY", key);
  } else {
    localStorage.removeItem("CLOUDBOARD_GEMINI_KEY");
  }
}

/**
 * Estimates hours, blockers, and recommended subtasks for a new task.
 */
export async function getAiTaskEstimation(title, description, existingTasks = []) {
  const apiKey = getStoredApiKey();
  if (!apiKey) {
    return getMockEstimation(title);
  }
  try {
    const genAI = new GoogleGenerativeAI(apiKey);
    const model = genAI.getGenerativeModel({ model: "gemini-1.5-flash" });
    const prompt = `\
      You are an expert technical project manager and software architect AI.\
      Analyze this task title and description:\
      Title: "${title}"\
      Description: "${description || 'No description provided.'}"\
\
      Generate a technical estimation for this task in JSON format. Do not return markdown, just raw JSON.\
      JSON structure:\
      {\
        "estimatedDays": float,\
        "blockers": [string],\
        "subtasks": [string]\
      }\
\
      Provide realistic estimates (in days, e.g., 2.5), list 3-4 highly specific technical blockers, and suggest 4-5 subtasks.\
    `;
    const result = await model.generateContent(prompt);
    const responseText = result.response.text().trim();
    const jsonMatch = responseText.match(/\{[\s\S]*\}/);
    return jsonMatch ? JSON.parse(jsonMatch[0]) : JSON.parse(responseText);
  } catch (error) {
    console.error("Gemini API error during estimation:", error);
    return { error: error.message || "Failed to query Gemini API", ...getMockEstimation(title) };
  }
}

/**
 * Checks if a new task is a duplicate of any existing tasks.
 */
export async function getAiDuplicateCheck(newTitle, newDescription, existingTasks = []) {
  const apiKey = getStoredApiKey();
  if (!apiKey || existingTasks.length === 0) {
    return getMockDuplicateCheck(newTitle, existingTasks);
  }
  try {
    const genAI = new GoogleGenerativeAI(apiKey);
    const model = genAI.getGenerativeModel({ model: "gemini-1.5-flash" });
    const taskListString = existingTasks.map(t => `#${t.id}: "${t.title}" (${t.description || ''})`).join("\n");
    const prompt = `\
      You are an AI engineering assistant. Check if the following new task is a duplicate or highly similar to any of the existing tasks.\
      New Task Title: "${newTitle}"\
      New Task Description: "${newDescription || ''}"\
      Existing Tasks:\
      ${taskListString}\
      Evaluate semantic similarity. Return a JSON object with this exact structure:\
      {\
        "isDuplicate": boolean,\
        "similarityPercentage": number,\
        "duplicateTaskId": string | null,\
        "explanation": string\
      }\
      Do not return markdown, just raw JSON.\
    `;
    const result = await model.generateContent(prompt);
    const responseText = result.response.text().trim();
    const jsonMatch = responseText.match(/\{[\s\S]*\}/);
    return jsonMatch ? JSON.parse(jsonMatch[0]) : JSON.parse(responseText);
  } catch (error) {
    console.error("Gemini API error during duplicate check:", error);
    return { error: error.message || "Failed to query Gemini API", ...getMockDuplicateCheck(newTitle, existingTasks) };
  }
}

// ----- Mock helpers (fallback) -----
function getMockEstimation(title) {
  const t = title.toLowerCase();
  let days = 2.0;
  let blockers = ["API response latency issues", "State sync race conditions"];
  let subtasks = ["Setup initial route/endpoint", "Write unit tests", "Create frontend controller view", "Document API changes"];
  if (t.includes("auth") || t.includes("login") || t.includes("jwt")) {
    days = 3.5;
    blockers = ["Secure token storage in HTTP-only cookies", "Silent token refresh handling", "CORS configuration"];
    subtasks = ["Implement JWT helpers", "Configure auth middleware", "Design sign‑in UI", "Setup token rotation", "Security audit"];
  } else if (t.includes("bug") || t.includes("fix")) {
    days = 1.0;
    blockers = ["Reproducing edge cases locally", "Ensuring backward compatibility"];
    subtasks = ["Isolate bug triggers", "Patch validation", "Run regression tests"];
  } else if (t.includes("db") || t.includes("database") || t.includes("postgres") || t.includes("schema")) {
    days = 4.0;
    blockers = ["Zero‑downtime migration planning", "Lock contention risks"];
    subtasks = ["Write migration DDL", "Test rollback scripts", "Create data access layer", "Optimize queries"];
  }
  return { estimatedDays: days, blockers, subtasks };
}

function getMockDuplicateCheck(newTitle, existingTasks = []) {
  if (!existingTasks.length) {
    return { isDuplicate: false, similarityPercentage: 0, duplicateTaskId: null, explanation: "No existing tasks to compare against." };
  }
  const cleanNew = newTitle.toLowerCase().trim();
  let bestMatch = null;
  let maxSim = 0;
  for (const t of existingTasks) {
    const clean = t.title.toLowerCase().trim();
    let sim = 0;
    if (cleanNew === clean) sim = 100;
    else if (cleanNew.includes(clean) || clean.includes(cleanNew)) sim = 85;
    else {
      const newWords = new Set(cleanNew.split(/\s+/));
      const taskWords = new Set(clean.split(/\s+/));
      const intersect = [...newWords].filter(w => taskWords.has(w) && w.length > 2);
      sim = Math.min(Math.floor((intersect.length / Math.max(newWords.size, taskWords.size)) * 100), 95);
    }
    if (sim > maxSim) { maxSim = sim; bestMatch = t; }
  }
  const isDup = maxSim > 80;
  return {
    isDuplicate: isDup,
    similarityPercentage: maxSim,
    duplicateTaskId: isDup && bestMatch ? bestMatch.id : null,
    explanation: isDup ? `High overlap with task #${bestMatch.id} "${bestMatch.title}" (${maxSim}% similarity).` : `No significant similarity; highest was ${maxSim}% with "${bestMatch?.title ?? 'none'}".`
  };
}
