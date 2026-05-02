// =====================================================
//  Todo App - Frontend logic
// =====================================================

// State
let currentUser = null;
let currentToken = null;
let currentFilter = "all";
let allTasks = [];
let isRegisterMode = false;

// DOM elements
const $ = (id) => document.getElementById(id);
const loginSection = $("login-section");
const appSection = $("app-section");
const loginError = $("login-error");
const userInfo = $("user-info");
const taskList = $("task-list");
const emptyMsg = $("empty-msg");
const backendStatus = $("backend-status");

let firebaseAuth = null;
if (!DEMO_MODE) {
  try {
    firebase.initializeApp(FIREBASE_CONFIG);
    firebaseAuth = firebase.auth();
  } catch (e) {
    console.error("Khởi tạo Firebase thất bại:", e);
  }
}


// =====================================================
//  Auth mode toggle
// =====================================================
function switchToRegister() {
  isRegisterMode = true;
  $("auth-title").textContent = "Đăng ký";
  $("confirm-password").classList.remove("hidden");
  $("btn-row-login").classList.add("hidden");
  $("btn-row-register").classList.remove("hidden");
  $("password").autocomplete = "new-password";
  loginError.textContent = "";
}

function switchToLogin() {
  isRegisterMode = false;
  $("auth-title").textContent = "Đăng nhập";
  $("confirm-password").classList.add("hidden");
  $("confirm-password").value = "";
  $("btn-row-login").classList.remove("hidden");
  $("btn-row-register").classList.add("hidden");
  $("password").autocomplete = "current-password";
  loginError.textContent = "";
}

// =====================================================
//  Auth — hỗ trợ cả DEMO_MODE và Firebase thật
// =====================================================
async function loginEmailPassword(email, password) {
  // DEMO_MODE: tạo token giả, không cần Firebase
  if (DEMO_MODE || !firebaseAuth) {
    const uid = "demo-" + btoa(email).replace(/=/g, "").slice(0, 12);
    return {
      token: `demo:${uid}:${email}`,
      user: { uid, email, name: email },
    };
  }
  const cred = await firebaseAuth.signInWithEmailAndPassword(email, password);
  const token = await cred.user.getIdToken(true);
  return {
    token,
    user: {
      uid: cred.user.uid,
      email: cred.user.email,
      name: cred.user.displayName || cred.user.email,
    },
  };
}

async function registerEmailPassword(email, password) {
  // DEMO_MODE: đăng ký == đăng nhập
  if (DEMO_MODE || !firebaseAuth) {
    return loginEmailPassword(email, password);
  }
  const cred = await firebaseAuth.createUserWithEmailAndPassword(email, password);
  const token = await cred.user.getIdToken();
  return {
    token,
    user: {
      uid: cred.user.uid,
      email: cred.user.email,
      name: cred.user.displayName || cred.user.email,
    },
  };
}

async function logout() {
  if (firebaseAuth) {
    try { await firebaseAuth.signOut(); } catch (_) {}
  }
  currentUser = null;
  currentToken = null;
  allTasks = [];
  showLogin();
}

// =====================================================
//  API calls
// =====================================================
async function apiFetch(path, options = {}) {
  const headers = {
    "Content-Type": "application/json",
    ...(options.headers || {}),
  };

  // 🔥 AUTO REFRESH TOKEN
  if (!DEMO_MODE && firebaseAuth && firebaseAuth.currentUser) {
    currentToken = await firebaseAuth.currentUser.getIdToken();
  }

  if (currentToken) headers["Authorization"] = `Bearer ${currentToken}`;

  const res = await fetch(`${BACKEND_URL}${path}`, { ...options, headers });

  if (res.status === 204) return null;

  const text = await res.text();
  let data = null;
  try { data = text ? JSON.parse(text) : null; } catch (_) { data = text; }

  if (!res.ok) {
    const msg = (data && data.detail) || `HTTP ${res.status}`;
    throw new Error(msg);
  }

  return data;
}

async function fetchMe() { return apiFetch("/auth/me"); }
async function fetchTasks() { return apiFetch("/tasks"); }
async function createTaskApi(title) {
  return apiFetch("/tasks", { method: "POST", body: JSON.stringify({ title }) });
}
async function updateTaskApi(id, patch) {
  return apiFetch(`/tasks/${id}`, { method: "PATCH", body: JSON.stringify(patch) });
}
async function deleteTaskApi(id) {
  return apiFetch(`/tasks/${id}`, { method: "DELETE" });
}

// =====================================================
//  UI rendering
// =====================================================
function showLogin() {
  loginSection.classList.remove("hidden");
  appSection.classList.add("hidden");
  $("email").value = "";
  $("password").value = "";
  $("confirm-password").value = "";
  loginError.textContent = "";
  switchToLogin();
}

function showApp() {
  loginSection.classList.add("hidden");
  appSection.classList.remove("hidden");
  userInfo.textContent = currentUser?.email || currentUser?.name || currentUser?.uid;
}

function renderTasks() {
  let visible = allTasks;
  if (currentFilter === "active") visible = allTasks.filter((t) => !t.done);
  else if (currentFilter === "done") visible = allTasks.filter((t) => t.done);

  taskList.innerHTML = "";
  if (visible.length === 0) {
    emptyMsg.classList.remove("hidden");
    emptyMsg.textContent = allTasks.length === 0
      ? "Chưa có việc nào, hãy thêm việc đầu tiên!"
      : "Không có việc nào trong mục này.";
    return;
  }
  emptyMsg.classList.add("hidden");

  for (const t of visible) {
    const li = document.createElement("li");
    li.className = "task-item" + (t.done ? " done" : "");

    const cb = document.createElement("input");
    cb.type = "checkbox";
    cb.checked = !!t.done;
    cb.addEventListener("change", () => toggleTask(t));

    const title = document.createElement("span");
    title.className = "title";
    title.textContent = t.title;

    const meta = document.createElement("span");
    meta.className = "meta";
    meta.textContent = formatDate(t.created_at);

    const del = document.createElement("button");
    del.className = "delete-btn";
    del.textContent = "✕";
    del.title = "Xoá";
    del.addEventListener("click", () => removeTask(t));

    li.appendChild(cb);
    li.appendChild(title);
    li.appendChild(meta);
    li.appendChild(del);
    taskList.appendChild(li);
  }
}

function formatDate(s) {
  if (!s) return "";
  const d = new Date(s);
  if (isNaN(d.getTime())) return "";
  const now = new Date();
  const sameDay = d.toDateString() === now.toDateString();
  if (sameDay) {
    return d.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
  }
  return d.toLocaleDateString([], { day: "2-digit", month: "2-digit" });
}

// =====================================================
//  Actions
// =====================================================
async function handleLogin() {
  loginError.textContent = "";

  const email = $("email").value.trim();
  const password = $("password").value;

  $("btn-login").disabled = true;

  try {
    const { token, user } = await loginEmailPassword(email, password);

    // 🔥 chỉ refresh 1 lần
    if (!DEMO_MODE && firebaseAuth) {
      currentToken = await firebaseAuth.currentUser.getIdToken(true);
    } else {
      currentToken = token;
    }

    // 🔥 dùng luôn user từ Firebase
    currentUser = user;

    showApp();

    // 🔥 chỉ gọi 1 API thôi
    allTasks = await fetchTasks();
    renderTasks();

  } catch (e) {
    loginError.textContent = e.message || "Đăng nhập thất bại.";
  } finally {
    $("btn-login").disabled = false;
  }
}

async function handleRegister() {
  loginError.textContent = "";

  const email = $("email").value.trim();
  const password = $("password").value;
  const confirm = $("confirm-password").value;

  if (!email || !password) {
    loginError.textContent = "Vui lòng nhập email và mật khẩu.";
    return;
  }
  if (password !== confirm) {
    loginError.textContent = "Mật khẩu xác nhận không khớp.";
    return;
  }

  $("btn-register").disabled = true;

  try {
    const { token, user } = await registerEmailPassword(email, password);

    // 🔥 refresh token 1 lần
    if (!DEMO_MODE && firebaseAuth) {
      currentToken = await firebaseAuth.currentUser.getIdToken(true);
    } else {
      currentToken = token;
    }

    // 🔥 dùng luôn user (không gọi /auth/me)
    currentUser = user;

    showApp();

    // 🔥 load tasks async (không block UI)
    fetchTasks().then(tasks => {
      allTasks = tasks;
      renderTasks();
    });

  } catch (e) {
    loginError.textContent = e.message || "Đăng ký thất bại.";
  } finally {
    $("btn-register").disabled = false;
  }
}

async function reloadTasks() {
  try {
    allTasks = await fetchTasks();
    renderTasks();
  } catch (e) {
    console.error(e);
  }
}

async function addTask() {
  const input = $("new-task");
  const title = input.value.trim();
  if (!title) return;
  $("btn-add").disabled = true;
  try {
    const newTask = await createTaskApi(title);
    allTasks.unshift(newTask);
    input.value = "";
    renderTasks();
  } catch (e) {
    alert("Không thể thêm: " + e.message);
  } finally {
    $("btn-add").disabled = false;
  }
}

async function toggleTask(t) {
  try {
    const updated = await updateTaskApi(t.id, { done: !t.done });
    const idx = allTasks.findIndex((x) => x.id === t.id);
    if (idx >= 0) allTasks[idx] = updated;
    renderTasks();
  } catch (e) {
    alert("Không thể cập nhật: " + e.message);
  }
}

async function removeTask(t) {
  if (!confirm(`Xoá "${t.title}"?`)) return;
  try {
    await deleteTaskApi(t.id);
    allTasks = allTasks.filter((x) => x.id !== t.id);
    renderTasks();
  } catch (e) {
    alert("Không thể xoá: " + e.message);
  }
}

// =====================================================
//  Event bindings
// =====================================================
$("btn-login").addEventListener("click", handleLogin);
$("btn-register").addEventListener("click", handleRegister);
$("btn-to-register").addEventListener("click", switchToRegister);
$("btn-to-login").addEventListener("click", switchToLogin);
$("btn-logout").addEventListener("click", logout);
$("btn-add").addEventListener("click", addTask);

$("new-task").addEventListener("keydown", (e) => {
  if (e.key === "Enter") addTask();
});
$("password").addEventListener("keydown", (e) => {
  if (e.key === "Enter") {
    if (isRegisterMode) $("confirm-password").focus();
    else handleLogin();
  }
});
$("confirm-password").addEventListener("keydown", (e) => {
  if (e.key === "Enter") handleRegister();
});

document.querySelectorAll(".tab").forEach((tab) => {
  tab.addEventListener("click", () => {
    document.querySelectorAll(".tab").forEach((t) => t.classList.remove("active"));
    tab.classList.add("active");
    currentFilter = tab.dataset.filter;
    renderTasks();
  });
});

// Init
checkBackend();
