async function upload() {
    const file = document.getElementById("file").files[0];

    if (!file) {
        alert("يرجى اختيار ملف أولاً");
        return;
    }

    const form = new FormData();
    form.append("file", file);

    const res = await fetch("/upload", { method: "POST", body: form });
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
        alert("يرجى إدخال عدد أيام صحيح أكبر من صفر");
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
            html += `<b>${service}</b><br>`;

            data[day][service].forEach(name => {
                html += `<span onclick="suggest(${day}, '${service}', '${name}')">${name}</span> , `;
            });

            html += "<br><br>";
        }

        card.innerHTML = html;
        container.appendChild(card);
    });
}

async function suggest(day, service, name) {
    const res = await fetch(`/suggest?day=${day}&service=${encodeURIComponent(service)}&name=${encodeURIComponent(name)}`);
    const data = await res.json();

    if (!data.length) {
        alert("لا يوجد بدائل متاحة");
        return;
    }

    alert("بدائل مقترحة:\n\n" + data.join("\n"));
}
