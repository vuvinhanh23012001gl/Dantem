export function clearn_div(div_card_arr) {
  if (!div_card_arr) return;
  for (let i = 0; i < div_card_arr.length; i++) {
    div_card_arr[i].classList.remove("div_click");
  }
}
export function removeClassFromList(elementList, className) {
    if (!elementList || !className) {
        console.log("class hoặc element không tồn tại")
        return;
    }
    for (let i = 0; i < elementList.length; i++) {
        elementList[i].classList.remove(className);
    }
}