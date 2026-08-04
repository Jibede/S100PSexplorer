function updatePreview(index) {
const elX = document.getElementById(`coordX_${index}`);
  const elY = document.getElementById(`coordY_${index}`);
  const elAlignH = document.getElementById(`alignH_${index}`);
  const elAlignV = document.getElementById(`alignV_${index}`);
  const elSize = document.getElementById(`fontSize_${index}`);
  const elColor = document.getElementById(`fontColor_${index}`);

  let instructions = [];

  if (elX && elY) {
    instructions.push(`LocalOffset:${elX.value},${elY.value}`);
  }
  if (elAlignH) {
    instructions.push(`TextAlignHorizontal:${elAlignH.value}`);
  }
  if (elAlignV) {
    instructions.push(`TextAlignVertical:${elAlignV.value}`);
  }
  if (elSize) {
    instructions.push(`FontSize:${elSize.value}`);
  }
  if (elColor) {
    instructions.push(`FontColor:${elColor.value}`);
  }

  const innerString = instructions.join(';');

  const stringSpan = document.getElementById(`instruction-string_${index}`);

  if (stringSpan) {
    stringSpan.innerText = `${innerString}`
  }
}

window.addEventListener('DOMContentLoaded', () => {
  const tousLesSpans = document.querySelectorAll('[id^="instruction-string_"]');
  
  tousLesSpans.forEach(span => {
    const index = span.id.split('_')[1];
    updatePreview(index);
  });
});