const recordBtn = document.getElementById('recordBtn');
const statusEl = document.getElementById('status');
const transcripcionEl = document.getElementById('transcripcion');
const respuestaEl = document.getElementById('respuesta');
const sqlCodeEl = document.getElementById('sql_code');
const rawDataEl = document.getElementById('raw_data');
const detailsEl = document.getElementById('details');

let mediaRecorder;
let audioChunks = [];

recordBtn.addEventListener('click', async () => {
    if (mediaRecorder && mediaRecorder.state === 'recording') {
        mediaRecorder.stop();
        recordBtn.textContent = '🎤 Grabar';
        statusEl.textContent = 'Procesando...';
    } else {
        try {
            const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
            mediaRecorder = new MediaRecorder(stream, { mimeType: 'audio/webm' });
            audioChunks = [];
            mediaRecorder.ondataavailable = e => audioChunks.push(e.data);
            mediaRecorder.onstop = async () => {
                const audioBlob = new Blob(audioChunks, { type: 'audio/webm' });
                const formData = new FormData();
                formData.append('audio', audioBlob, 'grabacion.webm');

                try {
                    const response = await fetch('/ask', { method: 'POST', body: formData });
                    const data = await response.json();

                    // Mostrar en un alert mientras debugueamos
                    alert(data.respuesta || data.answer || JSON.stringify(data));
                                    
                    console.log('DEBUG respuesta completa:', data);  // <-- agregado
                    
                    transcripcionEl.textContent = data.transcripcion || '';
                    respuestaEl.textContent = data.respuesta || data.answer || '';
                    
                    if (data.sql) {
                        sqlCodeEl.textContent = data.sql;
                        rawDataEl.textContent = typeof data.datos === 'string' ? data.datos : JSON.stringify(data.datos || data.data, null, 2);
                        detailsEl.hidden = false;
                    } else {
                        detailsEl.hidden = true;
                    }
                    statusEl.textContent = 'Listo';
                } catch (err) {
                    statusEl.textContent = 'Error: ' + err.message;
                    console.error(err);
                }
                stream.getTracks().forEach(track => track.stop());
            };
            mediaRecorder.start();
            recordBtn.textContent = '⏹ Detener';
            statusEl.textContent = 'Grabando...';
        } catch (err) {
            statusEl.textContent = 'Permiso de micrófono denegado';
        }
    }
});