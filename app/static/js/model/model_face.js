import {ItemsInspector} from "../services/items_inspector.js";
import { Measurement } from "../model/model_measurement.js";

export class Face{
    constructor(face_id){
        this.face_id = face_id;
        this.frame_id = face_id; // alias tương thích ngược
        this.arr_items = [];
    }

    addItem(itemInspector) {
        this.arr_items.push(itemInspector);
    }

    toDict() {
        const itemsDict = {};
        for (const item of this.arr_items) {
            // Bỏ qua các item rác có ID âm hoặc -1
            if (Number(item.items_id) < 0 || String(item.items_id) === "-1") {
                continue;
            }
            Object.assign(itemsDict, item.toDict());
        }
        return {
            [this.face_id]: itemsDict
        };
    }
        
    static fromDict(data) {
        const face_id = Object.keys(data)[0];
        const face = new Face(face_id);

        const itemsData = data[face_id];

        for (const [items_id, categories] of Object.entries(itemsData)) {
            const item = ItemsInspector.fromDict(items_id, categories);
            face.addItem(item);
        }

        return face;
    }
    clearAllInspectors() {
        for (const item of this.arr_items) {
            if (item && typeof item.clearInspectors === "function") {
                item.clearInspectors();
            }
        }
    }
    getItemCount() {
        return this.arr_items.length;
    }

    getItem(index) {
        if (index < 0 || index >= this.arr_items.length) {
            return null;
        }
        return this.arr_items[index];
    }
    getItemById(item_id) {
        return this.arr_items.find(
            obj_item_inspector => obj_item_inspector.items_id == item_id
        ) || null;
    }
}

export const Frame = Face;
