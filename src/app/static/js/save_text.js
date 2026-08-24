function saveTextParams(index, info, file) {
  let dict = {};

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
  const clearGeo = document.getElementById(`clearGeo_${index}`);

  let params = [];
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
  if (clearGeo && clearGeo.value == "true") params.push("ClearGeometry");

  const codeParamString = `'${params.join(";")}'`;

  dict[index] = {
    file: file,
    text: {
      node_type: "hit",
      line: parseInt(info.line),
      code: `featurePortrayal:AddInstructions(${codeParamString})`,
      instruction_type: "text",
      values: {
        ...((elX && elY) && {LocalOffset: {
          x: elX.value,
          y: elY.value,
        }}),
        ...(elAlignH && { TextAlignHorizontal: elAlignH.value }),
        ...(elAlignV && { TextAlignVertical: elAlignV.value }),
        ...(elSize && { FontSize: elSize.value }),
        ...(elColor && { FontColor: elColor.value }),
        ...(modeLinePlace &&
          valLinePlace && {
            LinePlacement: {
              mode: modeLinePlace.value,
              value: valLinePlace.value,
            },
          }),
        ...(areaPlacement && { AreaPlacement: areaPlacement.value }),
        ...(coordRef && { AreaCRS: coordRef.value }),
        ...(sysRotation &&
          angleRotation && {
            Rotation: { system: sysRotation.value, angle: angleRotation.value },
          }),
        ...(scaleFactor && { ScaleFactor: scaleFactor.value }),
        ...(clearGeo && { ClearGeometry: clearGeo.value == "true" }),
      },
      has_var: false,
      conditions: info.conditions,
    },
  };

  const dataToSave = dict[index];

  fetch("/save_file", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(dataToSave),
  })
    .then((response) => response.json())
    .then((data) => {
      if (data.status == "sucess") {
        const saveMsg = document.getElementById(`save-msg-text_${index}`);

        if (saveMsg) {
          saveMsg.classList.add("show");

          setTimeout(() => saveMsg.classList.remove("show"), 800);
        }
      } else {
        alert("Error to save: " + data.message);
      }
    })
    .catch((error) => console.log("Error in requisition: ", error));
}
