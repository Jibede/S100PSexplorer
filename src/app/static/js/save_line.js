function saveLineParams(index, info, file) {
  let dict = {};

  const elFormat = document.getElementById(`lineFormat_${index}`);
  const elThickness = document.getElementById(`thickness_${index}`);
  const elColor = document.getElementById(`lineColor_${index}`);

  let params = [];
  if (elFormat && elFormat.value) params.push(`'${elFormat.value}'`);
  if (elThickness && elThickness.value) params.push(`${elThickness.value}`);
  if (elColor && elColor.value) params.push(`'${elColor.value}'`);

  const codeParamString = `${params.join(",")}`;

  dict[index] = {
    file: file,
    line_style: {
      node_type: "hit",
      line: info.line,
      code: `featurePortrayal:SimpleLineStyle(${codeParamString})`,
      instruction_type: "line_style",
      values: {
        style: elFormat.value,
        thickness: parseFloat(elThickness.value),
        color: elColor.value,
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
        const saveMsg = document.getElementById(`save-msg-line_${index}`);

        if (saveMsg) {
          saveMsg.classList.add("show");

          setTimeout(() => saveMsg.classList.remove("show"), 800);
        }
      } else {
        alert("Error to save: " + data.message);
      }
    })
    .catch((error) => console.log("Error in requesition: ", error));
}
