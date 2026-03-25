import streamlit as st
from collections import defaultdict
import re
import arabic_reshaper
from bidi.algorithm import get_display

def ar(text):
    return get_display(arabic_reshaper.reshape(text))

class Service:
    def __init__(self, name, count, weight=1, cooldown=0):
        self.name = name
        self.count = count
        self.weight = weight
        self.cooldown = cooldown

class Person:
    def __init__(self, pid, name):
        self.id = pid
        self.name = name
        self.platoon = pid // 19

if "people" not in st.session_state:
    st.session_state.people = []

if "services" not in st.session_state:
    st.session_state.services = [
        Service("اعاشة",12,5,3),
        Service("قيادة",2,1),
        Service("عيادة",2,1),
        Service("امن",1,1),
    ]

if "schedule" not in st.session_state:
    st.session_state.schedule = {}

def generate(days):
    people = st.session_state.people
    services = st.session_state.services

    schedule = {}
    person_load = defaultdict(int)
    last_assigned = defaultdict(lambda: -999)
    last_service = defaultdict(lambda: -999)

    for d in range(days):
        schedule[d] = {}

        group = [p for p in people if p.platoon == d % 10]
        for p in group:
            person_load[p.id] += 5
            last_assigned[p.id] = d

        schedule[d]["واجب فصيلة"] = [p.name for p in group]

        for s in services:
            cand = [p for p in people if last_assigned[p.id] != d and d - last_service[(p.id,s.name)] >= s.cooldown]
            cand.sort(key=lambda p: person_load[p.id])

            sel = cand[:s.count]

            for p in sel:
                person_load[p.id] += s.weight
                last_assigned[p.id] = d
                last_service[(p.id,s.name)] = d

            schedule[d][s.name] = [p.name for p in sel]

    st.session_state.schedule = schedule
    st.session_state.load = person_load

st.title(ar("نظام جدولة الخدمات"))

uploaded = st.file_uploader(ar("تحميل الأسماء"))

if uploaded:
    names = []
    for line in uploaded.read().decode("utf-8").splitlines():
        line = re.sub(r'\d+','',line).strip()
        if len(line.split()) >= 2:
            names.append(line)

    st.session_state.people = [Person(i, names[i] if i < len(names) else f"شخص {i}") for i in range(190)]
    st.success(ar("تم تحميل الأسماء"))

st.subheader(ar("الخدمات"))

name = st.text_input(ar("اسم الخدمة"))
count = st.number_input(ar("عدد"),1)
weight = st.number_input(ar("وزن"),1)
cd = st.number_input(ar("راحة"),0)

if st.button(ar("إضافة خدمة")):
    st.session_state.services.append(Service(name,count,weight,cd))

for i,s in enumerate(st.session_state.services):
    st.write(f"{ar(s.name)} ({s.count})")

days = st.number_input(ar("عدد الأيام"),1,60,7)

if st.button(ar("توليد")):
    generate(days)

if st.session_state.schedule:
    day = st.selectbox(ar("اختر يوم"), list(st.session_state.schedule.keys()))

    for s,ppl in st.session_state.schedule[day].items():
        st.write(f"### {ar(s)} ({len(ppl)})")
        st.write(", ".join([ar(p) for p in ppl]))

if "load" in st.session_state:
    st.subheader(ar("تحليل"))
    st.bar_chart(list(st.session_state.load.values())[:50])
