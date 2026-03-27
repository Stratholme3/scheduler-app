async function upload() {
    const file = document.getElementById("file").files[0];

    if (!file) {
        alert("يرجى اختيار ملف أولاً");
        return;
    }

    const form = new FormData();
    form.append("file", file);

    const res = await fetch("/upload", {
        method: "POST",
        body: form
    });

    const data = await res.json();

    if (data.status === "error") {
        alert("خطأ: " + data.message);
    } else {
        alert("تم تحميل " + data.count + " اسم بنجاح");
    }
}

async function generate() {
    const days = parseInt(document.getElementById("days").value);

    if (!days || days <= 0) {
        alert("يرجى إدخال عدد أيام صحيح");
        return;
    }

    const res = await fetch(`/generate?days=${days}`);
    const data = await res.json();

    if (data.error) {
        alert("خطأ: " + data.error);
        return;
    }

    const container = document.getElementById("result");
    container.innerHTML = "";

    const sortedDays = Object.keys(data).sort((a, b) => Number(a) - Number(b));

    sortedDays.forEach(day => {
        const card = document.createElement("div");
        card.className = "card";

        let html = `<h3>اليوم ${Number(day) + 1}</h3>`;

        for (let service in data[day]) {
            html += `
                <div class="service">
                    <b>${service} (${data[day][service].length})</b>
                    <div class="people">
                        ${data[day][service].join(" ، ")}
                    </div>
                </div>
            `;
        }

        card.innerHTML = html;
        container.appendChild(card);
    });
}
