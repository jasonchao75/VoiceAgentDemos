// AudioWorklet: float32 input -> PCM int16 for WebSocket binary frames

class PCMProcessor extends AudioWorkletProcessor {
    constructor() {
        super();
        this.bufferSize = 1600; // 100ms @ 16kHz
        this.buffer = new Float32Array(this.bufferSize);
        this.bufferIndex = 0;
    }

    process(inputs, outputs, parameters) {
        const input = inputs[0];

        // No input yet; keep processor alive
        if (!input || !input[0]) {
            return true;
        }

        const inputChannel = input[0]; // mono

        // Fill PCM ring buffer
        for (let i = 0; i < inputChannel.length; i++) {
            this.buffer[this.bufferIndex++] = inputChannel[i];

            // Emit one chunk when full
            if (this.bufferIndex >= this.bufferSize) {
                this.sendPCMData();
                this.bufferIndex = 0;
            }
        }

        return true;
    }

    sendPCMData() {
        // Float32 [-1, 1] -> int16
        const pcmData = new Int16Array(this.bufferSize);

        for (let i = 0; i < this.bufferSize; i++) {
            // Clamp
            const sample = Math.max(-1, Math.min(1, this.buffer[i]));
            pcmData[i] = sample < 0 ? sample * 0x8000 : sample * 0x7FFF;
        }

        // Transfer buffer to main thread (detached)
        this.port.postMessage(pcmData.buffer, [pcmData.buffer]);
    }
}

registerProcessor('pcm-processor', PCMProcessor);
