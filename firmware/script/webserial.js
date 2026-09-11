let port = null,
    reader = null,
    writer = null;
async function readSerial() {
    const e = new TextDecoderStream;
    port.readable.pipeTo(e.writable), reader = e.readable.getReader();
    let r = "";
    try {
        for (;;) {
            const {
                value: e,
                done: o
            } = await reader.read();
            if (o) break;
            r += e;
            const t = r.split("\n");
            r = t.pop();
            for (const e of t) {
                const r = e.trim();
                r && (window.receiveFromSerial && window.receiveFromSerial(r))
            }
        }
    } catch (e) {
        console.error("Serial read error:", e)
    }
}
window.connectSerial = async function() {
    port = await navigator.serial.requestPort(), await port.open({
        baudRate: 115200
    }), console.log("Serial Device Connected"), readSerial()
}, window.writeSerial = async function(e) {
    if (!port) throw new Error("Serial Device not connected");
    const r = new TextEncoder,
        o = port.writable.getWriter();
    try {
        await o.write(r.encode(e + "\n"))
    } finally {
        o.releaseLock()
    }
};