// ── State ──────────────────────────────────────────────
let currentSchedule = null;
let scheduleHistory = [];
let replacementHistory = [];

// ── Tabs ───────────────────────────────────────────────
function switchTab(name) {
    document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
    document.querySelectorAll('.tab-panel').forEach(p => p.classList.remove('active'));
    document.getElementById('tab-' + name).classList.add('active');
    event.currentTarget.classList.add('active');

    if (name === 'load') loadStats();
    if (name === 'history') renderHistory();
}

// ── Names Tab ──────────────────────────────────────────
async function upload() {
    const file = document.getElementById("file").files[0];
    if (!file) { alert("يرجى اختيار ملف أولاً"); return; }

    const form = new FormData();
    form.append("file", file);

    const res = await fetch("/upload", { method: "POST", body: form });
    const data = await res.json();

    if (data.status === "error") {
        alert("خطأ: " + data.message);
        return;
    }

    alert("تم تحميل " + data.count + " اسم بنجاح");
    await loadPlatoons(data.count);
}

async function loadPlatoons(totalCount) {
    const res = await fetch("/platoons");
    const platoons = await res.json();
    if (!platoons.length) return;

    document.getElementById("names-stats").style.display = "block";

    document.getElementById("names-summary").innerHTML = `
        <div class="info-row"><span>إجمالي الأفراد</span><span class="badge">${totalCount}</span></div>
        <div class="info-row"><span>عدد الفصائل</span><span class="badge">${platoons.length}</span></div>
    `;

    const list = document.getElementById("platoon-list");
    list.innerHTML = "";

    platoons.forEach(pl => {
        const card = document.createElement("div");
        card.className = "platoon-card";

        const header = document.createElement("div");
        header.className = "platoon-header";
        header.innerHTML = `<span>الفصيلة ${pl.platoon}</span><span class="badge">${pl.count} فرد</span>`;
        header.addEventListener("click", () => {
            members.classList.toggle("open");
        });

        const members = document.createElement("div");
        members.className = "platoon-members";
        members.textContent = pl.members.join(" ، ");

        card.appendChild(header);
        card.appendChild(members);
        list.appendChild(card);
    });
}

// ── Schedule Tab ───────────────────────────────────────
async function generate() {
    const days = parseInt(document.getElementById("days").value);
    if (!days || days <= 0) { alert("يرجى إدخال عدد أيام صحيح أكبر من صفر"); return; }

    const res = await fetch(`/generate?days=${days}`);
    const data = await res.json();

    if (data.error) { alert("خطأ: " + data.error); return; }

    currentSchedule = data;

    addScheduleToHistory(days, data);
    renderSchedule(data);
}

function renderSchedule(data) {
    const container = document.getElementById("schedule-result");
    container.innerHTML = "";

    const sortedDays = Object.keys(data).sort((a, b) => Number(a) - Number(b));

    sortedDays.forEach(day => {
        const card = document.createElement("div");
        card.className = "day-card";

        const title = document.createElement("div");
        title.className = "day-title";
        title.textContent = "اليوم " + (Number(day) + 1);
        card.appendChild(title);

        for (let service in data[day]) {
            const block = document.createElement("div");
            block.className = "service-block";

            const label = document.createElement("span");
            label.className = "service-label";
            label.textContent = `${service} (${data[day][service].length})`;
            block.appendChild(label);

            const wrap = document.createElement("div");
            wrap.className = "people-wrap";

            data[day][service].forEach(name => {
                const btn = document.createElement("button");
                btn.className = "name-btn";
                btn.type = "button";
                btn.textContent = name;
                btn.addEventListener("click", () => openSuggest(Number(day), service, name, btn));
                wrap.appendChild(btn);
            });

            block.appendChild(wrap);
            card.appendChild(block);
        }

        container.appendChild(card);
    });
}

// ── Load Tab ───────────────────────────────────────────
async function loadStats() {
    const res = await fetch("/stats");
    const data = await res.json();

    const container = document.getElementById("stats-result");

    if (!data.length) {
        container.innerHTML = '<div class="empty-state">لا توجد بيانات بعد. قم بتوليد الجدول أولاً.</div>';
        return;
    }

    const maxLoad = Math.max(...data.map(p => p.load), 1);

    let html = `<table class="stats-table">
        <thead><tr>
            <th>الاسم</th>
            <th>الفصيلة</th>
            <th>المرات</th>
            <th>الحمل</th>
        </tr></thead><tbody>`;

    data.forEach(p => {
        const pct = Math.round((p.load / maxLoad) * 100);
        html += `<tr>
            <td>${p.name}</td>
            <td>${p.platoon}</td>
            <td>${p.assignments}</td>
            <td>
                <div class="load-bar-wrap">
                    <div class="load-bar" style="width:${pct}%"></div>
                </div>
            </td>
        </tr>`;
    });

    html += "</tbody></table>";
    container.innerHTML = html;
}

// ── History Tab ────────────────────────────────────────
function addScheduleToHistory(days, data) {
    const now = new Date();
    const total = Object.values(data).reduce((sum, day) => {
        return sum + Object.values(day).reduce((s, arr) => s + arr.length, 0);
    }, 0);

    scheduleHistory.unshift({
        timestamp: now.toLocaleString('ar'),
        days,
        totalAssignments: total
    });

    if (scheduleHistory.length > 20) scheduleHistory.pop();
}

function addReplacementToHistory(day, service, original, replacement) {
    const now = new Date();
    replacementHistory.unshift({
        timestamp: now.toLocaleString('ar'),
        day: day + 1,
        service,
        original,
        replacement
    });

    if (replacementHistory.length > 50) replacementHistory.pop();
}

function renderHistory() {
    const container = document.getElementById("history-result");

    if (!scheduleHistory.length && !replacementHistory.length) {
        container.innerHTML = '<div class="empty-state">لا يوجد سجل بعد.</div>';
        return;
    }

    let html = "";

    if (scheduleHistory.length) {
        html += '<div class="section-title" style="margin-bottom:10px">الجداول المولَّدة</div>';
        scheduleHistory.forEach((h, i) => {
            html += `<div class="history-entry">
                <div class="history-meta">${h.timestamp}</div>
                <div class="history-text">جدول ${h.days} يوم — ${h.totalAssignments} تكليف إجمالي</div>
            </div>`;
        });
    }

    if (replacementHistory.length) {
        html += '<div class="section-title" style="margin:14px 0 10px">الاستبدالات</div>';
        replacementHistory.forEach(r => {
            html += `<div class="history-entry replacement">
                <div class="history-meta">${r.timestamp}</div>
                <div class="history-text">اليوم ${r.day} · ${r.service}<br>
                    <span style="color:#f0a500">${r.original}</span>
                    &larr; <span style="color:#4fc3f7">${r.replacement}</span>
                </div>
            </div>`;
        });
    }

    container.innerHTML = html;
}

function clearHistory() {
    if (!confirm("هل تريد مسح السجل؟")) return;
    scheduleHistory = [];
    replacementHistory = [];
    renderHistory();
}

// ── Suggest / Replacement Modal ────────────────────────
let pendingSuggest = null;

async function openSuggest(day, service, name, btnElement) {
    const res = await fetch(`/suggest?day=${day}&service=${encodeURIComponent(service)}&name=${encodeURIComponent(name)}`);
    const data = await res.json();

    pendingSuggest = { day, service, name, btn: btnElement };

    document.getElementById("modal-title").textContent = `بدائل مقترحة لـ: ${name}`;

    const list = document.getElementById("modal-list");
    list.innerHTML = "";

    if (!data.length) {
        list.innerHTML = '<div style="color:#888;padding:10px">لا يوجد بدائل متاحة</div>';
    } else {
        data.forEach(candidate => {
            const btn = document.createElement("button");
            btn.className = "replacement-btn";
            btn.type = "button";
            btn.textContent = candidate;
            btn.addEventListener("click", () => confirmReplacement(candidate));
            list.appendChild(btn);
        });
    }

    document.getElementById("modal").classList.add("open");
}

function confirmReplacement(replacement) {
    const { day, service, name, btn } = pendingSuggest;

    // Update button text live in the schedule
    if (btn) {
        btn.textContent = replacement;
        btn.style.background = "#1a3a20";
        btn.style.borderColor = "#2ecc71";
        btn.style.color = "#2ecc71";
        btn.removeEventListener("click", btn._handler);
        btn.addEventListener("click", () => openSuggest(day, service, replacement, btn));
    }

    // Update in-memory schedule so future suggestions are aware
    if (currentSchedule && currentSchedule[day] && currentSchedule[day][service]) {
        const idx = currentSchedule[day][service].indexOf(name);
        if (idx !== -1) currentSchedule[day][service][idx] = replacement;
    }

    addReplacementToHistory(day, service, name, replacement);
    closeModal();
}

function closeModal(event) {
    if (event && event.target !== document.getElementById("modal")) return;
    document.getElementById("modal").classList.remove("open");
    pendingSuggest = null;
}
