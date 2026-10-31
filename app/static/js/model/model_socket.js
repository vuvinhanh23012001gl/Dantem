
export class SocketModel {
    constructor(namespace) {
        this.namespace = namespace;
        this.socket = null;
    }
    connect() {
        const baseUrl = (typeof window !== "undefined" && window.location?.origin) ? window.location.origin : "http://127.0.0.1:8000";
        this.socket = io(`${baseUrl}/${this.namespace}`);
        this.socket.on("connect", () => {
            console.log(`${this.namespace} connected Socket`);
        });
        this.socket.on("disconnect", () => {
            console.log(`${this.namespace} disconnected`);
        });
    }
    emit(event, data) {
        this.socket.emit(event, data);
    }
    on(event, callback) {
        this.socket.on(event, callback);
    }
}