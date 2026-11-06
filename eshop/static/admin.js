/* Administrace: potvrzení nevratných akcí, náhled fotky před nahráním, označení odkazu. */
(function () {
  document.querySelectorAll("form[data-potvrdit]").forEach(function (f) {
    f.addEventListener("submit", function (e) {
      if (!confirm(f.getAttribute("data-potvrdit"))) e.preventDefault();
    });
  });

  document.querySelectorAll("input[type=file][data-nahled]").forEach(function (vstup) {
    vstup.addEventListener("change", function () {
      var stary = vstup.parentNode.querySelector(".nahled-souboru");
      if (stary) stary.remove();
      if (!vstup.files || !vstup.files[0]) return;
      var img = document.createElement("img");
      img.className = "nahled-souboru";
      img.alt = "";
      img.src = URL.createObjectURL(vstup.files[0]);
      vstup.parentNode.appendChild(img);
    });
  });

  /* tlačítko odeslání formuláře s fotkami: ať se nedá kliknout dvakrát, nahrávání chvíli trvá */
  document.querySelectorAll("form[enctype='multipart/form-data']").forEach(function (f) {
    f.addEventListener("submit", function () {
      var tl = f.querySelector("button");
      if (tl) { tl.disabled = true; tl.textContent = "Nahrávám…"; }
    });
  });

  document.querySelectorAll("[data-oznacit]").forEach(function (pole) {
    pole.addEventListener("focus", function () { pole.select(); });
  });
})();
