const API_BASE = "http://localhost:8000";
let token = null;
let activeSessionId = null;
let activeIsAi = false;

function getEl(id) {
  return document.getElementById(id);
}

function setFlash(message, isError = false) {
  const el = getEl("flashMessage");
  if (!el) return;
  el.textContent = message;
  el.style.color = isError ? "#b91c1c" : "#4338ca";
}

function setAuthState(message) {
  const el = getEl("authState");
  if (!el) return;
  el.textContent = message;
}

async function api(path, method = "GET", body = null) {
  const headers = { "Content-Type": "application/json" };
  if (token) headers.Authorization = `Bearer ${token}`;

  const res = await fetch(`${API_BASE}${path}`, {
    method,
    headers,
    body: body ? JSON.stringify(body) : null,
  });

  if (!res.ok) {
    const text = await res.text();
    throw new Error(text || "Request failed");
  }
  return res.json();
}

function appendChat(line) {
  const el = getEl("chatOutput");
  if (!el) return;
  if (el.textContent.trim() === "No conversation yet.") {
    el.textContent = "";
  }
  el.textContent += `${line}\n`;
}

function bindClick(id, handler) {
  const el = getEl(id);
  if (el) {
    el.onclick = handler;
  }
}

bindClick("registerBtn", async () => {
  try {
    const data = await api("/auth/register", "POST", {
      email: getEl("email")?.value,
      password: getEl("password")?.value,
      display_name: getEl("displayName")?.value,
      role: getEl("role")?.value,
      is_anonymous: true,
    });
    token = data.access_token;
    setFlash("Welcome to HearU! Account created.");
    setAuthState("Authenticated");
  } catch (err) {
    setFlash(`Register failed: ${err.message}`, true);
  }
});

bindClick("loginBtn", async () => {
  try {
    const data = await api("/auth/login", "POST", {
      email: getEl("loginEmail")?.value,
      password: getEl("loginPassword")?.value,
    });
    token = data.access_token;
    setFlash("Login successful.");
    setAuthState("Authenticated");
  } catch (err) {
    setFlash(`Login failed: ${err.message}`, true);
  }
});

bindClick("requestHumanBtn", async () => {
  try {
    const data = await api("/sessions/request", "POST", { cause: "Loneliness" });
    activeSessionId = data.session_id;
    activeIsAi = false;
    const session = getEl("sessionResult");
    if (session) {
      session.innerText = `Human session #${data.session_id} (${data.status})`;
    }
    setFlash("Connected to support flow.");
  } catch (err) {
    setFlash(`Could not request human session: ${err.message}`, true);
  }
});

bindClick("requestAiBtn", async () => {
  try {
    const data = await api("/sessions/request-ai", "POST", { cause: "Stress" });
    activeSessionId = data.session_id;
    activeIsAi = true;
    const session = getEl("sessionResult");
    if (session) {
      session.innerText = `HearU AI session #${data.session_id} (${data.status})`;
    }
    const chat = getEl("chatOutput");
    if (chat) {
      chat.textContent = "No conversation yet.";
    }
    setFlash("HearU AI is ready for you.");
  } catch (err) {
    setFlash(`Could not request AI session: ${err.message}`, true);
  }
});

bindClick("sendAiMessageBtn", async () => {
  try {
    if (!activeSessionId || !activeIsAi) {
      setFlash("Start a HearU AI session first.", true);
      return;
    }
    const content = getEl("chatInput")?.value?.trim();
    if (!content) {
      setFlash("Please type a message.", true);
      return;
    }

    appendChat(`You: ${content}`);
    const data = await api(`/sessions/${activeSessionId}/ai-message`, "POST", { content });
    appendChat(`HearU AI: ${data.reply}`);
    const input = getEl("chatInput");
    if (input) {
      input.value = "";
    }
    setFlash("Message delivered.");
  } catch (err) {
    setFlash(`Could not send AI message: ${err.message}`, true);
  }
});
