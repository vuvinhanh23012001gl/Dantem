export class Line {
    constructor(line = {}) {
        this.xStart = line?.xStart ?? 0;
        this.yStart = line?.yStart ?? 0;
        this.xEnd = line?.xEnd ?? 0;
        this.yEnd = line?.yEnd ?? 0;
    }

    set(data = {}) {
        if (data.xStart !== undefined) this.xStart = data.xStart;
        if (data.yStart !== undefined) this.yStart = data.yStart;
        if (data.xEnd !== undefined) this.xEnd = data.xEnd;
        if (data.yEnd !== undefined) this.yEnd = data.yEnd;
    }

    getStart() {
        return { x: this.xStart, y: this.yStart };
    }

    getEnd() {
        return { x: this.xEnd, y: this.yEnd };
    }

    toDict() {
        return {
            xStart: this.xStart,
            yStart: this.yStart,
            xEnd: this.xEnd,
            yEnd: this.yEnd
        };
    }
}