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

        const title = document.createElement("h3");
        title.textContent = "اليوم " + (Number(day) + 1);
        card.appendChild(title);

        for (let service in data[day]) {
            const serviceDiv = document.createElement("div");
            serviceDiv.className = "service";

            const label = document.createElement("b");
            label.textContent = service;
            serviceDiv.appendChild(label);

            const peopleDiv = document.createElement("div");
            peopleDiv.className = "people";

            data[day][service].forEach(name => {
                const tag = document.createElement("span");
                tag.className = "name-tag";
                tag.textContent = name;

                tag.addEventListener("click", () => suggest(Number(day), service, name));

                peopleDiv.appendChild(tag);
            });

            serviceDiv.appendChild(peopleDiv);
            card.appendChild(serviceDiv);
        }

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

    alert("بدائل مقترحة لـ " + name + ":\n\n" + data.join("\n"));
}
