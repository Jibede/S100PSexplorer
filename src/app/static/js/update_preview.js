function updatePreview(index) {
  // 1. Récupération des inputs (votre code)
  const elX = document.getElementById(`coordX_${index}`);
  const elY = document.getElementById(`coordY_${index}`);
  const elAlignH = document.getElementById(`alignH_${index}`);
  const elAlignV = document.getElementById(`alignV_${index}`);
  const elSize = document.getElementById(`fontSize_${index}`);
  const elColor = document.getElementById(`fontColor_${index}`);

  // 2. Génération de la chaîne d'instructions (votre code)
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

  const innerString = instructions.join(";");
  const stringSpan = document.getElementById(`instruction-string_${index}`);

  if (stringSpan) {
    stringSpan.innerText = `${innerString}`;
  }

  // 3. Mise à jour de la prévisualisation visuelle (ajout)
  const previewText = document.getElementById(`previewText_${index}`);
  const previewContainer = document.getElementById(`previewContainer_${index}`);

  if (previewText && previewContainer) {
    // Appliquer la taille de la police et la couleur
    if (elSize) previewText.style.fontSize = `${elSize.value}px`;
    if (elColor) {
      const selectedOption = elColor.options[elColor.selectedIndex];
      previewText.style.color = selectedOption.getAttribute("data-rgb");
    }

    // Appliquer les coordonnées avec transform: translate
    const valX = elX ? elX.value : 0;
    const valY = elY ? elY.value : 0;
    previewText.style.transform = `translate(${valX}px, ${valY}px)`;

    // Appliquer l'alignement horizontal
    if (elAlignH) {
      const hAlignMap = { Start: "left", Center: "center", End: "right" };
      previewText.style.textAlign = hAlignMap[elAlignH.value];
    }

    // Appliquer l'alignement vertical sur le conteneur parent
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

// 4. Initialisation au chargement de la page (votre code)
window.addEventListener("DOMContentLoaded", () => {
  const tousLesSpans = document.querySelectorAll('[id^="instruction-string_"]');

  tousLesSpans.forEach((span) => {
    const index = span.id.split("_")[1];
    // L'appel de cette fonction mettra désormais à jour la chaîne ET la prévisualisation
    updatePreview(index);
  });
});
