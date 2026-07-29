document.addEventListener("DOMContentLoaded", () => {
  // 1. On récupère l'URL de votre fichier CSS via la variable globale
  const cssUrl = window.S101_NIGHT_CSS_URL;

  // 2. On télécharge le contenu du CSS UNE SEULE FOIS pour toute la page
  fetch(cssUrl)
    .then((response) => response.text())
    .then((cssText) => {
      // 3. On boucle sur tous les canvas de la page
      document.querySelectorAll(".cartoCanvas").forEach((canvas) => {
        const ctx = canvas.getContext("2d");
        const svgUrl = canvas.dataset.symbol;

        // 4. On télécharge le code source (XML) du fichier SVG
        fetch(svgUrl)
          .then((res) => res.text())
          .then((svgText) => {
            const parser = new DOMParser();
            const svgDoc = parser.parseFromString(svgText, "image/svg+xml");

            const styleElement = svgDoc.createElementNS(
              "http://www.w3.org/2000/svg",
              "style"
            );
            styleElement.textContent = cssText;
            svgDoc.documentElement.prepend(styleElement);

            const serializer = new XMLSerializer();
            const finalSvgText = serializer.serializeToString(svgDoc);

            const symbolImage = new Image();
            symbolImage.src = "data:image/svg+xml;charset=utf-8," + encodeURIComponent(finalSvgText);

            symbolImage.onload = function () {
              const v1_x = parseFloat(canvas.dataset.v1_x) || 0;
              const v1_y = parseFloat(canvas.dataset.v1_y) || 0;
              const v2_x = parseFloat(canvas.dataset.v2_x) || 0;
              const v2_y = parseFloat(canvas.dataset.v2_y) || 0;

              ctx.fillStyle = "white";
              ctx.fillRect(0, 0, canvas.width, canvas.height);

              const p0 = { x: canvas.width / 2, y: canvas.height / 2 };
              const v1 = { x: v1_x, y: v1_y };
              const v2 = { x: v2_x, y: v2_y };

              const points = [
                { x: p0.x, y: p0.y }, 
                { x: p0.x + v1.x, y: p0.y + v1.y }, 
                { x: p0.x + v2.x, y: p0.y + v2.y }, 
                { x: p0.x + v2.x + v1.x, y: p0.y + v2.y + v1.y }, 
              ];

              points.forEach((point) => {
                const drawX = point.x - symbolImage.width / 2;
                const drawY = point.y - symbolImage.height / 2;
                ctx.drawImage(symbolImage, drawX, drawY);
              });

              ctx.beginPath();
              ctx.moveTo(points[0].x, points[0].y); 
              ctx.lineTo(points[1].x, points[1].y); 
              ctx.lineTo(points[3].x, points[3].y); 
              ctx.lineTo(points[2].x, points[2].y); 
              ctx.closePath(); 
            };
          });
      });
    });
});