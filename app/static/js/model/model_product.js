import { Face, Frame } from "./model_face.js";
import { ItemsInspector } from "../services/items_inspector.js";

export class Product {
    constructor(product_id = null) {
        this.product_id = product_id;
        this.arr_faces = [];
        this.arr_frames = this.arr_faces; // alias tương thích ngược
    }
    
    addFace(face) {
        this.arr_faces.push(face);
    }

    addFrame(frame) {
        return this.addFace(frame);
    }

    getFace(face_id) {
        return this.arr_faces.find(
            face => String(face.face_id || face.frame_id) === String(face_id)
        );
    }

    getFrame(frame_id) {
        return this.getFace(frame_id);
    }

    toDict() {
        const facesDict = {};
        for (const face of this.arr_faces) {
            const currentId = face.face_id || face.frame_id;
            // Bỏ qua các face rác có ID âm hoặc -1
            if (Number(currentId) < 0 || String(currentId) === "-1") {
                continue;
            }
            Object.assign(facesDict, face.toDict());
        }
        return {
            [this.product_id]: facesDict
        };
    }

    static fromDict(data) {
        if (!data) {
            throw new Error("Dữ liệu Product bị null hoặc undefined");
        }
        if (typeof data !== "object") {
            throw new Error(
                `Dữ liệu Product phải là object, nhận được ${typeof data}`
            );
        }
        const keys = Object.keys(data);
        if (keys.length === 0) {
            throw new Error("Không tìm thấy Product ID");
        }
        const product_id = keys[0];
        const product = new Product(product_id);
        const facesData = data[product_id];
        if (facesData === null || facesData === undefined) {
            throw new Error(
                `Product '${product_id}' không chứa dữ liệu Face`
            );
        }
        for (const [face_id, faceData] of Object.entries(facesData)) {
            const face = Face.fromDict({
                [face_id]: faceData
            });
            if (!face) {
                throw new Error("Face trả về null");
            }
            product.addFace(face);
        }
        return product;
    }
    

    find_item_object_corresponding(face_id, item_id, type){
        // Chặn không tìm hoặc tạo cho ID âm hoặc -1
        if (Number(face_id) < 0 || Number(item_id) < 0 || String(face_id) === "-1" || String(item_id) === "-1") {
            return null;
        }
        let obj_face = this.getFace(face_id);
        if (!obj_face){
            obj_face = new Face(String(face_id));
            this.addFace(obj_face);
        }
        let obj_items_inspector = obj_face.getItemById(item_id);
        if (!obj_items_inspector){
            obj_items_inspector = new ItemsInspector(String(item_id));
            obj_face.addItem(obj_items_inspector);
        }
        let obj_type = obj_items_inspector.getInspector(type);
        if (!obj_type){return null;}
        return obj_type;  // trả về đối tượng inspector tương ứng
    }

    get_item_object(face_id, item_id){
        // Chặn không tạo Face/Item cho ID âm hoặc -1
        if (Number(face_id) < 0 || Number(item_id) < 0 || String(face_id) === "-1" || String(item_id) === "-1") {
            return null;
        }
        let obj_face = this.getFace(face_id);
        if (!obj_face){
            obj_face = new Face(String(face_id));
            this.addFace(obj_face);
        }
        let obj_items_inspector = obj_face.getItemById(item_id);
        if (!obj_items_inspector) {
            obj_items_inspector = new ItemsInspector(String(item_id));
            obj_face.addItem(obj_items_inspector);
        }
        return obj_items_inspector;
    }

    get_item_inspector(face_id, item_id){
        return this.get_item_object(face_id, item_id);
    }

    getAllInspectors(type) {
        const inspectors = [];
        for (const face of this.arr_faces) {
            for (const item of face.arr_items) {
                const objInspector = item.getInspector(type);

                if (objInspector) {
                    inspectors.push({
                        face_id: face.face_id || face.frame_id,
                        frame_id: face.face_id || face.frame_id,
                        item_id: item.items_id,
                        inspector: objInspector
                    });
                }
            }
        }
        return inspectors;
    }

    hasInspectorData(inspectors, face_id, item_id, propertyName) {
        const obj = inspectors.find(
            item => (String(item.face_id) === String(face_id) || String(item.frame_id) === String(face_id)) && String(item.item_id) === String(item_id)
        );
        if (!obj || !obj.inspector) {
            return false;
        }
        const data = obj.inspector[propertyName];
        if (data === undefined || data === null) {
            console.warn(`[Inspector] Thuộc tính '${propertyName}' không tồn tại trên Item: ${item_id}`);
            return false;
        }
        if (Array.isArray(data)) {
            const isValid = data.length > 0;
            console.log(`[Inspector Check] '${propertyName}' (Array) -> Valid: ${isValid}`);
            return isValid;
        }
        if (typeof data === "object") {
            if (typeof data.isValid === "function") {
                const isValid = data.isValid();
                console.log(`[Inspector Check] '${propertyName}' (isValid()) -> Valid: ${isValid}`);
                return isValid;
            }
            const isValid = Object.keys(data).length > 0;
            console.log(`[Inspector Check] '${propertyName}' (Object) -> Valid: ${isValid}`);
            return isValid;
        }
        console.warn(`[Inspector] Kiểu dữ liệu không hợp lệ cho '${propertyName}':`, typeof data);
        return false;
    }

    highlightItems(container, type, propertyName, className = "active_hightlight") {
        const inspectors = this.getAllInspectors(type);
        console.log("Dữ liệu để chuyển Items màu xanh",inspectors);
        container.querySelectorAll(".box-face, .box-frame").forEach(face => {
            const face_id = face.dataset.faceId || face.dataset.frameId;
            face.querySelectorAll(".img-item").forEach(item => {
                const item_id = item.dataset.id;
                const text = item.querySelector(".img-text");
                item.classList.remove(className);
                text?.classList.remove(className);
                if (this.hasInspectorData(inspectors, face_id, item_id, propertyName)) {
                    item.classList.add(className);
                    text?.classList.add(className);
                }
            });
        });
    }

    clearHighlight(container, className = "active_hightlight") {
        if (!container) return;
        container.querySelectorAll(".box-face, .box-frame").forEach(face => {
            face.querySelectorAll(".img-item").forEach(item => {
                const text = item.querySelector(".img-text");
                item.classList.remove(className);
                text?.classList.remove(className);
            });
        });
    }
    clearAllInspectors() {
        for (const face of this.arr_faces) {
            if (face && typeof face.clearAllInspectors === "function") {
                face.clearAllInspectors();
            }
        }
    }
}
