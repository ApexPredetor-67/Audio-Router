import os
from flask import Flask, jsonify, render_template, request, send_from_directory
import miniaudio
import numpy as np
import sounddevice as sd

# Force Python's working directory to match this script's location
os.chdir(os.path.dirname(os.path.abspath(__file__)))

app = Flask(__name__, static_folder=".", static_url_path="", template_folder=".")

active_streams = []


def stop_all_streams():
    global active_streams
    for stream in active_streams:
        try:
            stream.stop()
            stream.close()
        except Exception:
            pass
    active_streams.clear()


def create_stream(file_path, device_id):
    decoded = miniaudio.decode_file(file_path)
    audio_data = np.frombuffer(decoded.samples, dtype=np.int16).astype(np.float32) / 32768.0
    if decoded.nchannels > 1:
        audio_data = audio_data.reshape(-1, decoded.nchannels)

    pos = [0]

    def callback(outdata, frames, time_info, status):
        start = pos[0]
        end = start + frames
        chunk = audio_data[start:end]

        if len(chunk) < frames:
            outdata[:len(chunk)] = chunk
            outdata[len(chunk):] = 0
            raise sd.CallbackStop
        else:
            outdata[:] = chunk
        pos[0] = end

    stream = sd.OutputStream(
        device=device_id,
        samplerate=decoded.sample_rate,
        channels=decoded.nchannels,
        callback=callback
    )
    return stream


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/<path:path>")
def serve_static(path):
    return send_from_directory(".", path)


@app.route("/api/devices", methods=["GET"])
def get_devices():
    devices = sd.query_devices()
    hostapis = sd.query_hostapis()
    output_devices = []

    for idx, dev in enumerate(devices):
        if dev['max_output_channels'] > 0:
            api_index = dev['hostapi']
            host_api_name = hostapis[api_index]['name']
            output_devices.append({
                "id": idx,
                "name": f"[{host_api_name}] {dev['name']}"
            })

    return jsonify(output_devices)


@app.route("/api/play", methods=["POST"])
def play_audio():
    data = request.json
    mode = data.get("mode")  # 'dev1' or 'both'

    stop_all_streams()

    try:
        if mode in ["dev1", "both"]:
            file1 = data.get("file1", "").strip().strip('"').strip("'")
            if not os.path.exists(file1):
                return jsonify({"status": "error", "message": f"File not found: {file1}"}), 404

            dev1_id = int(data.get("dev1_id"))
            stream1 = create_stream(file1, dev1_id)
            stream1.start()
            active_streams.append(stream1)

        if mode in ["both"]:
            file2 = data.get("file2", "").strip().strip('"').strip("'")
            if not os.path.exists(file2):
                return jsonify({"status": "error", "message": f"File not found: {file2}"}), 404

            dev2_id = int(data.get("dev2_id"))
            stream2 = create_stream(file2, dev2_id)
            stream2.start()
            active_streams.append(stream2)

        return jsonify({"status": "playing", "message": f"Started playback in '{mode}' mode!"})

    except Exception as e:
        stop_all_streams()
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route("/api/stop", methods=["POST"])
def stop_sound():
    stop_all_streams()
    return jsonify({"status": "stopped"})


if __name__ == "__main__":
    app.run(port=5000, debug=True)