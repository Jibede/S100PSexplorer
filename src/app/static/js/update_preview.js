function updatePreview(index) {
  
  const elX = document.getElementById(`coordX_${index}`);
  const elY = document.getElementById(`coordY_${index}`);
  const elAlignH = document.getElementById(`alignH_${index}`);
  const elAlignV = document.getElementById(`alignV_${index}`);
  const elSize = document.getElementById(`fontSize_${index}`);
  const elColor = document.getElementById(`fontColor_${index}`);

  const modeLinePlace = document.getElementById(`linePlacement-mode_${index}`);
  const valLinePlace = document.getElementById(`linePlacement-value_${index}`);
  const areaPlacement = document.getElementById(`areaPlacement_${index}`);
  const coordRef = document.getElementById(`areaCRS_${index}`);
  const sysRotation = document.getElementById(`rotation-system_${index}`);
  const angleRotation = document.getElementById(`rotation-angle_${index}`);
  const scaleFactor = document.getElementById(`scaleFactor_${index}`);
  const clearGeo = document.getElementById(`clearGeo_${index}`)

  // const rawText = document.getElementById(`rawText_${index}`);
  // const textVwGroup = document.getElementById(`textVwGroup_${index}`);
  // const hover = document.getElementById(`hover_${index}`);
  // const textPriority = document.getElementById(`textPriority_${index}`);
  // const viewGroup = document.getElementById(`viewGroup_${index}`);
  // const priority = document.getElementById(`priority_${index}`);

  let params = [];
  // let params_instructions = [];

  if (elX && elY) params.push(`LocalOffset:${elX.value},${elY.value}`);
  if (elAlignH) params.push(`TextAlignHorizontal:${elAlignH.value}`);
  if (elAlignV) params.push(`TextAlignVertical:${elAlignV.value}`);
  if (elSize) params.push(`FontSize:${elSize.value}`);
  if (elColor) params.push(`FontColor:${elColor.value}`);

  if (modeLinePlace && valLinePlace)
    params.push(`LinePlacement:${modeLinePlace.value},${valLinePlace.value}`);
  if (areaPlacement) params.push(`AreaPlacement:${areaPlacement.value}`);
  if (coordRef) params.push(`AreaCRS:${coordRef.value}`);
  if (sysRotation && angleRotation)
    params.push(`Rotation:${sysRotation.value},${angleRotation.value}`);
  if (scaleFactor) params.push(`ScaleFactor:${scaleFactor.value}`);
  if (clearGeo && clearGeo.value == 'true') params.push('ClearGeometry')

  // if (rawText && rawText.value) params_instructions.push(rawText.value);
  // if (textVwGroup && textVwGroup.value)
  //   params_instructions.push(textVwGroup.value);
  // if (hover && hover.value) params_instructions.push(hover.value);
  // if (textPriority && textPriority.value)
  //   params_instructions.push(textPriority.value);
  // if (viewGroup && viewGroup.value) params_instructions.push(viewGroup.value);
  // if (priority && priority.value) params_instructions.push(priority.value);

  const innerString = params.join(";");
  const stringSpan = document.getElementById(`instruction-string_${index}`);
  if (stringSpan) {
    stringSpan.innerText = `'${innerString}'`;
  }

  // const innerInstructions = params_instructions.join(", ");
  // const textStringSpan = document.getElementById(
  //   `instruction-text-string_${index}`,
  // );
  // if (textStringSpan) {
  //   textStringSpan.innerText = `'${innerInstructions}'`;
  // }

  const previewText = document.getElementById(`previewText_${index}`);
  const previewContainer = document.getElementById(`previewContainer_${index}`);

  if (previewText && previewContainer) {
    if (elSize) previewText.style.fontSize = `${elSize.value}px`;
    if (elColor) {
      const selectedOption = elColor.options[elColor.selectedIndex];
      previewText.style.color = selectedOption.getAttribute("data-rgb");
    }

    const valX = elX ? elX.value : 0;
    const valY = elY ? elY.value : 0;
    previewText.style.transform = `translate(${valX}px, ${valY}px)`;

    if (elAlignH) {
      const hAlignMap = { Start: "left", Center: "center", End: "right" };
      previewText.style.textAlign = hAlignMap[elAlignH.value];
    }

    if (elAlignV) {
      const vAlignMap = {
        Start: "flex-start",
        Center: "center",
        End: "flex-end",
      };
      previewContainer.style.justifyContent = vAlignMap[elAlignV.value];
    }
  }
}

window.addEventListener("DOMContentLoaded", () => {
  const uniqueIndexes = new Set();

  document.querySelectorAll('[id^="instruction-string_"]').forEach((span) => {
    const index = span.id.split("_")[1];
    uniqueIndexes.add(index);
  });

  document
    .querySelectorAll('[id^="instruction-text-string_"]')
    .forEach((span) => {
      const index = span.id.split("_")[1];
      uniqueIndexes.add(index);
    });

  uniqueIndexes.forEach((index) => {
    updatePreview(index);

    const inputIds = [
      // `rawText_${index}`,
      // `textVwGroup_${index}`,
      // `hover_${index}`,
      // `textPriority_${index}`,
      // `viewGroup_${index}`,
      // `priority_${index}`,
      `coordX_${index}`,
      `coordY_${index}`,
      `alignH_${index}`,
      `alignV_${index}`,
      `fontSize_${index}`,
      `fontColor_${index}`,
      `modeLinePlace_${index}`,
      `valLinePlace_${index}`,
      `areaPlacement_${index}`,
      `coordRef_${index}`,
      `sysRotation_${index}`,
      `angleRotation_${index}`,
      `scaleFactor_${index}`,
      `clearGeo_${index}`
    ];

    inputIds.forEach((id) => {
      const el = document.getElementById(id);

      if (el) {
        el.addEventListener("input", () => updatePreview(index));
        el.addEventListener("change", () => updatePreview(index));
      }
    });
  });
});
