async function upload() {
    const file = document.getElementById("file").files[0];

    const form = new FormData();
    form.append("file", file);

    await fetch("/upload", { method: "POST", body: form });
    alert("تم تحميل الأسماء");
}

async function generate() {
    const days = document.getElementById("days").value;
    const res = await fetch(`/generate?days=${days}`);
    const data = await res.json();

    const container = document.getElementById("result");
    container.innerHTML = "";

    Object.keys(data).forEach(day => {
        const card = document.createElement("div");
        card.className = "card";

        let html = `<h3>اليوم ${Number(day)+1}</h3>`;

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
    const res = await fetch(`/suggest?day=${day}&service=${service}&name=${name}`);
    const data = await res.json();

    alert("بدائل مقترحة:\n\n" + data.join("\n"));
}
