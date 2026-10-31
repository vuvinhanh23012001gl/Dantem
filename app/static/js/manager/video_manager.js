export class VideoManager {
    constructor(videoElement) {
        this.video = videoElement;
        this.ws = null;
        this.currentUrl = null;
    }

    connect() {
        if (this.ws && (
            this.ws.readyState === WebSocket.OPEN ||
            this.ws.readyState === WebSocket.CONNECTING
        )) {
            return;
        }
        this.ws = new WebSocket(
            `${window.location.protocol === "https:" ? "wss" : "ws"}://${window.location.host}/captureproduct/ws`
        );
        this.ws.binaryType = "arraybuffer";
        this.ws.onmessage = (event) => {
            const blob = new Blob(
                [event.data],
                { type: "image/jpeg" }
            );
            const nextUrl = URL.createObjectURL(blob);
            const previousUrl = this.currentUrl;
            this.currentUrl = nextUrl;
            this.video.onload = () => {
                this.video.onload = null;
                if (previousUrl) {
                    URL.revokeObjectURL(previousUrl);
                }
            };
            this.video.src = nextUrl;
        };
        this.ws.onclose = () => {
            this.ws = null;
        };
    }

    show() {
        this.video.style.display = "block";
        this.connect();
    }
}