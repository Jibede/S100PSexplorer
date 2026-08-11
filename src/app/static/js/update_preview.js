function updatePreview(index) {
  const elX = document.getElementById(`coordX_${index}`);
  const elY = document.getElementById(`coordY_${index}`);
  const elAlignH = document.getElementById(`alignH_${index}`);
  const elAlignV = document.getElementById(`alignV_${index}`);
  const elSize = document.getElementById(`fontSize_${index}`);
  const elColor = document.getElementById(`fontColor_${index}`);

  const rawText = document.getElementById(`rawText_${index}`)
  const textVwGroup = document.getElementById(`textVwGroup_${index}`);
  const viewGroup = document.getElementById(`viewGroup_${index}`);
  const priority = document.getElementById(`priority_${index}`);
  const hover = document.getElementById(`hover_${index}`);
  const textPriority = document.getElementById(`textPriority_${index}`);

  let params = [];
  let params_instructions = [];

  // 1. Coletando os parâmetros da primeira linha (TE)
  if (elX && elY) {
    params.push(`LocalOffset:${elX.value},${elY.value}`);
  }
  if (elAlignH) {
    params.push(`TextAlignHorizontal:${elAlignH.value}`);
  }
  if (elAlignV) {
    params.push(`TextAlignVertical:${elAlignV.value}`);
  }
  if (elSize) {
    params.push(`FontSize:${elSize.value}`);
  }
  if (elColor) {
    params.push(`FontColor:${elColor.value}`);
  }

  // 2. Coletando os parâmetros da segunda linha (TextInstruction)
  if (rawText) {
    params_instructions.push(rawText.value)
  }
  if (textVwGroup) {
    params_instructions.push(textVwGroup.value);
  }
  if (viewGroup) {
    params_instructions.push(viewGroup.value);
  }
  if (priority) {
    params_instructions.push(priority.value);
  }
  if (hover) {
    params_instructions.push(hover.value);
  }
  if (textPriority) {
    params_instructions.push(textPriority.value);
  }

  // 3. Atualizando o HTML da Primeira Linha (instruction-string)
  const innerString = params.join(";");
  const stringSpan = document.getElementById(`instruction-string_${index}`);
  if (stringSpan) {
    // Adicionamos as aspas simples de volta para manter o visual do código
    stringSpan.innerText = `'${innerString}'`;
  }

  // 4. Atualizando o HTML da Segunda Linha (instruction-text-string)
  const innerInstructions = params_instructions.join(", "); // Separado por vírgula (ajuste se precisar de ";")
  const textStringSpan = document.getElementById(`instruction-text-string_${index}`);
  if (textStringSpan) {
    // Adicionamos as aspas simples de volta para manter o visual do código
    textStringSpan.innerText = `'${innerInstructions}'`;
  }

  // 5. Atualizando a caixa de Preview Visual
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
  // 1. Criamos um "Set" (Conjunto). Ele é perfeito para isso porque ignora números repetidos!
  const uniqueIndexes = new Set();

  // 2. Pegamos todos os spans do PRIMEIRO grupo e guardamos o número deles
  document.querySelectorAll('[id^="instruction-string_"]').forEach((span) => {
    const index = span.id.split("_")[1];
    uniqueIndexes.add(index);
  });

  // 3. Pegamos todos os spans do SEGUNDO grupo (que você mencionou) e guardamos o número
  document.querySelectorAll('[id^="instruction-text-string_"]').forEach((span) => {
    const index = span.id.split("_")[1];
    uniqueIndexes.add(index);
  });

  // 4. Agora, para cada número encontrado (seja do grupo 1 ou do grupo 2), aplicamos a lógica
  uniqueIndexes.forEach((index) => {
    
    // Roda a função uma vez para carregar a tela inicial correta
    updatePreview(index);

    // Lista TODOS os inputs possíveis para esse índice
    const inputIds = [
      `coordX_${index}`, `coordY_${index}`, `alignH_${index}`, `alignV_${index}`, 
      `fontSize_${index}`, `fontColor_${index}`, `textVwGroup_${index}`, 
      `viewGroup_${index}`, `priority_${index}`, `hover_${index}`, `textPriority_${index}`
    ];

    // Fazemos o forEach dentro dos inputs para adicionar o atualizador em tempo real
    inputIds.forEach(id => {
      const el = document.getElementById(id);
      
      // Se o campo existir na página, adiciona a escuta
      if (el) {
        el.addEventListener("input", () => updatePreview(index));
        el.addEventListener("change", () => updatePreview(index));
      }
    });

  }); // Fim do forEach principal
}); // Fim do DOMContentLoaded