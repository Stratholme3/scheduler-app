async function upload() {
    const file = document.getElementById("file").files[0];
    const form = new FormData();
    form.append("file", file);

    await fetch("/upload", {
        method: "POST",
        body: form
    });

    alert("تم تحميل الأسماء");
}

async function generate() {
    const days = document.getElementById("days").value;

    const res = await fetch(`/generate?days=${days}`);
    const data = await res.json();

    const container = document.getElementById("result");
    container.innerHTML = "";

    Object.keys(data).forEach(day => {
        const div = document.createElement("div");
        div.className = "card";

        let html = `<h3>اليوم ${day}</h3>`;

        for (let s in data[day]) {
            html += `<b>${s} (${data[day][s].length})</b><br>`;
            html += data[day][s].join(" , ") + "<br><br>";
        }

        div.innerHTML = html;
        container.appendChild(div);
    });
      }
