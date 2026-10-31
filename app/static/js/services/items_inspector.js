import { StampItemInspector } from "./stamp_item_inspector.js";
import { StampAlignmentItemInspector } from "./stamp_alignment_item_inspector.js";
import { StampReversedItemInspector } from "./stamp_reversed_item_inspector.js";
import { AnomalyPointInspector } from "./anomaly_point_item_inspector.js";
import { ForeignObjectInspector } from "./foreign_object_item_inspector.js";
import { OCRItemInspector } from "./ocr_item_inspector.js";
import { ColorItemInspector } from "./color_item_inspector.js";
import { BarcodeItemInspector } from "./barcode_item_inspector.js";
import { QRItemInspector } from "./qr_item_inspector.js";

export class ItemsInspector {
    static TYPE_STAMP = StampItemInspector.NAME;
    static TYPE_STAMP_ALIGNMENT = StampAlignmentItemInspector.NAME;
    static TYPE_STAMP_REVERSED = StampReversedItemInspector.NAME;
    static TYPE_ANOMALY_POINT = AnomalyPointInspector.NAME;
    static TYPE_FOREIGN_OBJECT = ForeignObjectInspector.NAME;
    static TYPE_OCR = OCRItemInspector.NAME;
    static TYPE_COLOR = ColorItemInspector.NAME;
    static TYPE_BARCODE = BarcodeItemInspector.NAME;
    static TYPE_QR = QRItemInspector.NAME;

    constructor(
        items_id,
        stamp_item = null,
        anomaly_point_item = null,
        foreign_object_item = null,
        ocr_item = null,
        stamp_alignment_item = null,
        color_item = null,
        barcode_item = null,
        qr_item = null,
        stamp_reversed_item = null,
    ) {
        this.items_id = items_id;
        this.inspectors = {
            [ItemsInspector.TYPE_STAMP]: stamp_item,
            [ItemsInspector.TYPE_STAMP_ALIGNMENT]: stamp_alignment_item,
            [ItemsInspector.TYPE_STAMP_REVERSED]: stamp_reversed_item,
            [ItemsInspector.TYPE_ANOMALY_POINT]: anomaly_point_item,
            [ItemsInspector.TYPE_FOREIGN_OBJECT]: foreign_object_item,
            [ItemsInspector.TYPE_OCR]: ocr_item,
            [ItemsInspector.TYPE_COLOR]: color_item,
            [ItemsInspector.TYPE_BARCODE]: barcode_item,
            [ItemsInspector.TYPE_QR]: qr_item,
        };
    }

    getInspector(type) {
        return this.inspectors[type] || null;
    }

    getStampItems() {
        return this.getInspector(ItemsInspector.TYPE_STAMP);
    }

    getStampAlignmentItems() {
        return this.getInspector(ItemsInspector.TYPE_STAMP_ALIGNMENT);
    }

    getStampReversedItems() {
        return this.getInspector(ItemsInspector.TYPE_STAMP_REVERSED);
    }

    getAnomalyPointItems() {
        return this.getInspector(ItemsInspector.TYPE_ANOMALY_POINT);
    }

    getForeignObjectItems() {
        return this.getInspector(ItemsInspector.TYPE_FOREIGN_OBJECT);
    }

    getOCRItems() {
        return this.getInspector(ItemsInspector.TYPE_OCR);
    }

    getColorItems() {
        return this.getInspector(ItemsInspector.TYPE_COLOR);
    }

    getBarcodeItems() {
        return this.getInspector(ItemsInspector.TYPE_BARCODE);
    }

    getQRItems() {
        return this.getInspector(ItemsInspector.TYPE_QR);
    }

    toDict() {
        const categories = {};
        for (const [key, inspector] of Object.entries(this.inspectors)) {
            const data = inspector?.toDict();
            if (data && Object.keys(data).length) categories[key] = data;
        }
        return {[this.items_id]: categories};
    }

    setInspector(type, instance) {
        this.inspectors[type] = instance;
    }

    setStampItems(instance) {
        this.setInspector(ItemsInspector.TYPE_STAMP, instance);
    }

    setStampAlignmentItems(instance) {
        this.setInspector(ItemsInspector.TYPE_STAMP_ALIGNMENT, instance);
    }

    setStampReversedItems(instance) {
        this.setInspector(ItemsInspector.TYPE_STAMP_REVERSED, instance);
    }

    setAnomalyPointItems(instance) {
        this.setInspector(ItemsInspector.TYPE_ANOMALY_POINT, instance);
    }

    setForeignObjectItems(instance) {
        this.setInspector(ItemsInspector.TYPE_FOREIGN_OBJECT, instance);
    }

    setOCRItems(instance) {
        this.setInspector(ItemsInspector.TYPE_OCR, instance);
    }

    setColorItems(instance) {
        this.setInspector(ItemsInspector.TYPE_COLOR, instance);
    }

    setBarcodeItems(instance) {
        this.setInspector(ItemsInspector.TYPE_BARCODE, instance);
    }

    setQRItems(instance) {
        this.setInspector(ItemsInspector.TYPE_QR, instance);
    }

    clearInspectors() {
        for (const type of Object.keys(this.inspectors)) this.inspectors[type] = null;
    }

    static fromDict(items_id, categories = {}) {
        return new ItemsInspector(
            items_id,
            categories?.[this.TYPE_STAMP] ? StampItemInspector.fromDict(categories[this.TYPE_STAMP]) : null,
            categories?.[this.TYPE_ANOMALY_POINT] || categories?.EndChippingInspector
                ? AnomalyPointInspector.fromDict(categories[this.TYPE_ANOMALY_POINT] ?? categories.EndChippingInspector)
                : null,
            categories?.[this.TYPE_FOREIGN_OBJECT]
                ? ForeignObjectInspector.fromDict(categories[this.TYPE_FOREIGN_OBJECT])
                : null,
            categories?.[this.TYPE_OCR]
                ? OCRItemInspector.fromDict(categories[this.TYPE_OCR])
                : null,
            categories?.[this.TYPE_STAMP_ALIGNMENT]
                ? StampAlignmentItemInspector.fromDict(categories[this.TYPE_STAMP_ALIGNMENT])
                : null,
            categories?.[this.TYPE_COLOR]
                ? ColorItemInspector.fromDict(categories[this.TYPE_COLOR])
                : null,
            categories?.[this.TYPE_BARCODE]
                ? BarcodeItemInspector.fromDict(categories[this.TYPE_BARCODE])
                : null,
            categories?.[this.TYPE_QR]
                ? QRItemInspector.fromDict(categories[this.TYPE_QR])
                : null,
            categories?.[this.TYPE_STAMP_REVERSED]
                ? StampReversedItemInspector.fromDict(categories[this.TYPE_STAMP_REVERSED])
                : null,
        );
    }
}
