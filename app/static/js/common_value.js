
// export const scroll_content = document.getElementById("scroll-content");
import {SocketModel} from "./model/model_socket.js"
import { CanvasManager } from "./manager/canvas_manager.js"
import { VideoManager } from "./manager/video_manager.js"


    
//import socket 
export const SocketLog = new SocketModel("log");
export const SocketData = new SocketModel("data");
SocketLog.connect();
SocketData.connect();

 
export const WIDTH_IMG_SHAPE = 1024;
export const HEIGH_IMG_SHAPE = 768;



export const scroll_container = document.querySelector(".scroll-container");
export const video_product = document.getElementById("video-product");

export const videoManager = new VideoManager(video_product);
export const canvasManager = new CanvasManager("coordinate","wrap-canvas",video_product,WIDTH_IMG_SHAPE,HEIGH_IMG_SHAPE);
canvasManager.initEvent();



const TCP_KEY = "tcp_connected";
export function set_tcp_connection(isConnected) {
    sessionStorage.setItem(TCP_KEY, isConnected ? "true" : "false");
}

export function get_tcp_connection() {
    if (sessionStorage.getItem(TCP_KEY) === null) {
        sessionStorage.setItem(TCP_KEY, "false");
    }
    return sessionStorage.getItem(TCP_KEY) === "true";
}

// Backward compatibility aliases
export const set_com_connection = set_tcp_connection;
export const get_com_connection = get_tcp_connection;


const CAMERA_KEY = "camera_connected";
export function set_camera_connection(isConnected) {
    sessionStorage.setItem(CAMERA_KEY, isConnected ? "true" : "false");
}

export function get_camera_connection() {
    if (sessionStorage.getItem(CAMERA_KEY) === null) {
        sessionStorage.setItem(CAMERA_KEY, "false");
    }
    return sessionStorage.getItem(CAMERA_KEY) === "true";
}




export function active_sceen_show_video(){
    canvasManager.hideImagePreview();
    video_product.style.width = `${WIDTH_IMG_SHAPE}px`;
    video_product.style.height = `${HEIGH_IMG_SHAPE}px`;  
    video_product.style.objectFit = "contain";   
    video_product.style.border = "none";
    video_product.style.outline = "none";
    if (video_product.getAttribute("src")) {
        video_product.style.display = "flex";
    } else {
        video_product.style.display = "none";
    }
    canvasManager.setWrapCanvasVisible(false);
}

export function show_video_product(){
    canvasManager.hideImagePreview();
    video_product.style.border = "none";
    video_product.style.outline = "none";
    video_product.style.display = "flex";
    videoManager.show();
    canvasManager.setWrapCanvasVisible(false);
}

