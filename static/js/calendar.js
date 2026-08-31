document.addEventListener('DOMContentLoaded', () => {
    const app = document.getElementById('calendar-app');
    if (!app) return;

    const salonId = app.dataset.salon;
    const whatsappNum = app.dataset.whatsapp;
    
    // Configuracion de horario (podría venir de data attrs)
    const HORA_DESDE = 7 * 60; // 07:00 en minutos
    const HORA_HASTA = 23 * 60; // 23:00 en minutos

    let currentDate = new Date(); // Inicia en mes actual
    // Ajustar a primero de mes
    currentDate.setDate(1);

    const btnPrev = document.getElementById('btn-prev-month');
    const btnNext = document.getElementById('btn-next-month');
    const monthLabel = document.getElementById('current-month-label');
    const daysGrid = document.getElementById('calendar-days');
    const dayDetail = document.getElementById('day-detail');
    const detailDate = document.getElementById('detail-date');
    const detailSlots = document.getElementById('detail-slots');
    const btnWhatsapp = document.getElementById('btn-whatsapp');

    // Estado local
    let blocksData = [];
    let selectedDateStr = null;

    btnPrev.addEventListener('click', () => {
        const today = new Date();
        // No permitir navegar al pasado (meses anteriores al actual)
        if (currentDate.getFullYear() === today.getFullYear() && currentDate.getMonth() <= today.getMonth()) {
            return; 
        }
        currentDate.setMonth(currentDate.getMonth() - 1);
        loadMonth();
    });

    btnNext.addEventListener('click', () => {
        currentDate.setMonth(currentDate.getMonth() + 1);
        loadMonth();
    });

    function getDaysInMonth(year, month) {
        return new Date(year, month + 1, 0).getDate();
    }

    function timeToMinutes(timeStr) {
        if (!timeStr) return 0;
        const parts = timeStr.split(':');
        return parseInt(parts[0], 10) * 60 + parseInt(parts[1], 10);
    }

    function minutesToTime(mins) {
        const h = Math.floor(mins / 60).toString().padStart(2, '0');
        const m = (mins % 60).toString().padStart(2, '0');
        return `${h}:${m}`;
    }

    function calculateFreeSlots(blocks) {
        if (!blocks || blocks.length === 0) {
            return [{ start: HORA_DESDE, end: HORA_HASTA }];
        }
        
        let merged = [];
        let sorted = blocks.map(b => ({
            start: timeToMinutes(b.inicio),
            end: timeToMinutes(b.fin)
        })).sort((a, b) => a.start - b.start);

        let current = sorted[0];
        for (let i = 1; i < sorted.length; i++) {
            if (sorted[i].start <= current.end) {
                current.end = Math.max(current.end, sorted[i].end);
            } else {
                merged.push(current);
                current = sorted[i];
            }
        }
        merged.push(current);

        let freeSlots = [];
        let currentStart = HORA_DESDE;

        for (let m of merged) {
            if (currentStart < m.start) {
                freeSlots.push({ start: currentStart, end: Math.min(m.start, HORA_HASTA) });
            }
            currentStart = Math.max(currentStart, m.end);
        }

        if (currentStart < HORA_HASTA) {
            freeSlots.push({ start: currentStart, end: HORA_HASTA });
        }

        return freeSlots;
    }

    async function loadMonth() {
        const year = currentDate.getFullYear();
        const month = currentDate.getMonth();
        
        const monthNames = ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"];
        monthLabel.textContent = `${monthNames[month]} ${year}`;

        // Disable prev button if current month
        const today = new Date();
        if (year === today.getFullYear() && month <= today.getMonth()) {
            btnPrev.style.opacity = '0.5';
            btnPrev.style.cursor = 'not-allowed';
        } else {
            btnPrev.style.opacity = '1';
            btnPrev.style.cursor = 'pointer';
        }

        const firstDay = new Date(year, month, 1);
        const lastDay = new Date(year, month + 1, 0);
        
        const desde = `${year}-${String(month+1).padStart(2, '0')}-01`;
        const hasta = `${year}-${String(month+1).padStart(2, '0')}-${String(lastDay.getDate()).padStart(2, '0')}`;

        try {
            const resp = await fetch(`/api/public/disponibilidad?salon_id=${salonId}&desde=${desde}&hasta=${hasta}`);
            const data = await resp.json();
            blocksData = data;
            renderCalendar(year, month);
        } catch (e) {
            console.error("Error loading availability", e);
        }
    }

    function renderCalendar(year, month) {
        daysGrid.innerHTML = '';
        const firstDayIndex = (new Date(year, month, 1).getDay() || 7) - 1; // 0=Lun, 6=Dom
        const daysInMonth = getDaysInMonth(year, month);
        
        const today = new Date();
        const todayStr = `${today.getFullYear()}-${String(today.getMonth()+1).padStart(2,'0')}-${String(today.getDate()).padStart(2,'0')}`;

        for (let i = 0; i < firstDayIndex; i++) {
            const empty = document.createElement('div');
            daysGrid.appendChild(empty);
        }

        for (let d = 1; d <= daysInMonth; d++) {
            const dateStr = `${year}-${String(month+1).padStart(2, '0')}-${String(d).padStart(2, '0')}`;
            const dayEl = document.createElement('div');
            dayEl.className = 'calendar-day';
            dayEl.textContent = d;
            
            // Si es pasado, marcar visualmente y no clickeable
            const dayDate = new Date(year, month, d);
            dayDate.setHours(23, 59, 59, 999);
            if (dayDate < today) {
                dayEl.style.opacity = '0.3';
                dayEl.style.cursor = 'default';
                daysGrid.appendChild(dayEl);
                continue;
            }

            if (dateStr === todayStr) {
                dayEl.style.border = '2px solid var(--cpim-primary)';
            }

            const dayBlocks = blocksData.find(b => b.fecha === dateStr);
            let stateClass = 'libre';
            
            if (dayBlocks && dayBlocks.bloqueos && dayBlocks.bloqueos.length > 0) {
                const freeSlots = calculateFreeSlots(dayBlocks.bloqueos);
                if (freeSlots.length === 0) {
                    stateClass = 'ocupado';
                } else {
                    stateClass = 'parcial';
                }
            }
            
            dayEl.classList.add(stateClass);
            if (dateStr === selectedDateStr) {
                dayEl.classList.add('seleccionado');
            }

            if (stateClass !== 'ocupado') {
                dayEl.addEventListener('click', () => {
                    document.querySelectorAll('.calendar-day').forEach(el => el.classList.remove('seleccionado'));
                    dayEl.classList.add('seleccionado');
                    selectedDateStr = dateStr;
                    showDayDetail(dateStr, dayBlocks ? dayBlocks.bloqueos : [], stateClass);
                });
            }

            daysGrid.appendChild(dayEl);
        }
    }

    function showDayDetail(dateStr, blocks, state) {
        dayDetail.style.display = 'block';
        
        const parts = dateStr.split('-');
        const d = new Date(parts[0], parseInt(parts[1])-1, parts[2]);
        const options = { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' };
        detailDate.textContent = d.toLocaleDateString('es-AR', options);
        
        detailSlots.innerHTML = '';
        
        const freeSlots = calculateFreeSlots(blocks);
        
        if (freeSlots.length === 0) {
            detailSlots.innerHTML = '<div class="franja ocupada">Sin disponibilidad para esta fecha</div>';
        } else if (freeSlots.length === 1 && freeSlots[0].start === HORA_DESDE && freeSlots[0].end === HORA_HASTA) {
            detailSlots.innerHTML = '<div class="franja libre">Disponible durante toda la jornada</div>';
        } else {
            // Mostrar bloques combinados libres y ocupados si se quisiera,
            // pero la spec dice: "Las franjas libres se calculan desde hora_publica restando ocupadas."
            // "07:00 — 12:00 DISPONIBLE", "12:00 — 16:00 NO DISPONIBLE"
            
            let html = '';
            let current = HORA_DESDE;
            
            // Reconstruir franjas para mostrarlas
            let allIntervals = [];
            for (let b of blocks) {
                allIntervals.push({start: timeToMinutes(b.inicio), end: timeToMinutes(b.fin), free: false});
            }
            for (let f of freeSlots) {
                allIntervals.push({start: f.start, end: f.end, free: true});
            }
            
            allIntervals.sort((a,b) => a.start - b.start);
            
            for (let iv of allIntervals) {
                if (iv.end > HORA_DESDE && iv.start < HORA_HASTA) {
                    const s = Math.max(iv.start, HORA_DESDE);
                    const e = Math.min(iv.end, HORA_HASTA);
                    if (s < e) {
                        const stateText = iv.free ? 'DISPONIBLE' : 'NO DISPONIBLE';
                        const cssClass = iv.free ? 'libre' : 'ocupada';
                        html += `<div class="franja ${cssClass}"><span>${minutesToTime(s)} — ${minutesToTime(e)}</span><span>${stateText}</span></div>`;
                    }
                }
            }
            detailSlots.innerHTML = html;
        }

        // WhatsApp CTA
        const salonName = document.querySelector('#salon-select option:checked').textContent;
        const msg = `Hola, quisiera consultar por la disponibilidad del salón ${salonName} para el día ${dateStr}.`;
        btnWhatsapp.href = `https://wa.me/${whatsappNum}?text=${encodeURIComponent(msg)}`;
    }

    loadMonth();
});
