document.addEventListener('DOMContentLoaded', () => {
    const moduleCount = document.getElementById('moduleCount');
    const card2 = document.getElementById('card2');

    const dev1Select = document.getElementById('dev1Select');
    const dev2Select = document.getElementById('dev2Select');
    const file1Input = document.getElementById('file1Input');
    const file2Input = document.getElementById('file2Input');

    const playBtn = document.getElementById('playBtn');
    const stopBtn = document.getElementById('stopBtn');
    const output = document.getElementById('output');

    moduleCount.addEventListener('change', () => {
        if (moduleCount.value === "1") {
            card2.style.display = "none";
            playBtn.textContent = "Play Earphones 1";
        } else {
            card2.style.display = "block";
            playBtn.textContent = "Play Both Simultaneously";
        }
    });

    async function loadDevices() {
        try {
            const response = await fetch('/api/devices');
            const devices = await response.json();

            dev1Select.innerHTML = '';
            dev2Select.innerHTML = '';

            devices.forEach((dev) => {
                const opt1 = document.createElement('option');
                opt1.value = dev.id;
                opt1.textContent = dev.name;
                dev1Select.appendChild(opt1);

                const opt2 = document.createElement('option');
                opt2.value = dev.id;
                opt2.textContent = dev.name;
                dev2Select.appendChild(opt2);
            });

            if (devices.length > 1) {
                dev2Select.selectedIndex = 1;
            }
        } catch (err) {
            output.textContent = "Failed to load audio devices.";
        }
    }

    playBtn.addEventListener('click', async () => {
        const mode = moduleCount.value === "1" ? "dev1" : "both";

        const payload = {
            mode: mode,
            dev1_id: dev1Select.value,
            file1: file1Input.value.trim(),
            dev2_id: dev2Select.value,
            file2: file2Input.value.trim()
        };

        output.textContent = "Starting playback...";

        try {
            const response = await fetch('/api/play', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });

            const resData = await response.json();
            output.textContent = resData.message || resData.status;
        } catch (error) {
            output.textContent = "Error launching playback.";
        }
    });

    stopBtn.addEventListener('click', async () => {
        output.textContent = "Stopping all audio...";
        try {
            await fetch('/api/stop', { method: 'POST' });
            output.textContent = "All audio stopped.";
        } catch (error) {
            output.textContent = "Failed to stop playback.";
        }
    });

    loadDevices();
});