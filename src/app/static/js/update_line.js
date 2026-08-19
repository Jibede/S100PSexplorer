function updateLinePreview(index) {
  const elFormat = document.getElementById(`lineFormat_${index}`);
  const elThickness = document.getElementById(`thickness_${index}`);
  const elColor = document.getElementById(`lineColor_${index}`);

  const previewLine = document.getElementById(`previewLine_${index}`);
  if (!previewLine) return;

  const svgLine = previewLine.querySelector("line");
  if (!svgLine) return;

  if (elThickness) {
    svgLine.setAttribute("stroke-width", elThickness.value);
  }

  if (elColor) {
    const selectedOption = elColor.options[elColor.selectedIndex];
    const rgbColor = selectedOption.getAttribute("data-rgb");
    if (rgbColor) {
      svgLine.setAttribute("stroke", rgbColor);
    }
  }

  if (elFormat) {
    const style = elFormat.value;
    if (style === "dash") {
      svgLine.setAttribute("stroke-dasharray", "8 5");
    } else if (style === "dot") {
      svgLine.setAttribute("stroke-dasharray", "2 3");
    } else {
      svgLine.removeAttribute("stroke-dasharray"); 
    }
  }
}

window.addEventListener("DOMContentLoaded", () => {
  const lineUniqueIndexes = new Set();

  document.querySelectorAll('[id^="lineFormat_"]').forEach((el) => {
    const index = el.id.split("_")[1];
    lineUniqueIndexes.add(index);
  });
  
  document.querySelectorAll('[id^="thickness_"]').forEach((el) => {
    const index = el.id.split("_")[1];
    lineUniqueIndexes.add(index);
  });

  lineUniqueIndexes.forEach((index) => {
    
    updateLinePreview(index);

    const inputIds = [
      `lineFormat_${index}`,
      `thickness_${index}`,
      `fontColor_${index}`
    ];

    inputIds.forEach((id) => {
      const el = document.getElementById(id);
      if (el) {
        // Chama a nova função
        el.addEventListener("input", () => updateLinePreview(index));
        el.addEventListener("change", () => updateLinePreview(index));
      }
    });
  });
});