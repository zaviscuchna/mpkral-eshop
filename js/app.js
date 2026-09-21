/* M+P Král — náčrt e-shopu. Vanilla, bez knihoven.
   JS řeší jen interakci; obsah je v HTML, takže bez JS se stránka zobrazí. */
(function () {
  "use strict";

  var KLIC = "mpkral-sanon-v1";

  /* hodnoty ze šanonu jdou přes localStorage — do HTML je pouštíme jen ošetřené */
  function esc(s) {
    return String(s == null ? "" : s)
      .replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;").replace(/'/g, "&#39;");
  }
  function bezpecnaCesta(s) {
    s = String(s || "");
    return /^(https?:|file:|data:image\/|[^:]*$)/.test(s) ? esc(s) : "";
  }

  /* ---------------------------------------------------------- šanon (stav) */
  function nacti() {
    try {
      return JSON.parse(localStorage.getItem(KLIC) || "[]");
    } catch (e) {
      return [];
    }
  }
  function uloz(s) {
    try {
      localStorage.setItem(KLIC, JSON.stringify(s));
    } catch (e) {
      /* private mode — šanon vydrží jen do konce stránky */
    }
    vykresliPocty();
  }
  function kusy(polozka) {
    var n = 0;
    for (var v in polozka.velikosti) n += polozka.velikosti[v];
    return n;
  }
  function vykresliPocty() {
    var s = nacti();
    var ks = s.reduce(function (a, p) { return a + kusy(p); }, 0);
    document.querySelectorAll("[data-sanon-pocet]").forEach(function (e) { e.textContent = s.length; });
    document.querySelectorAll("[data-sanon-polozky]").forEach(function (e) { e.textContent = s.length; });
    document.querySelectorAll("[data-sanon-kusy]").forEach(function (e) { e.textContent = ks; });
  }

  /* ---------------------------------------------------------- režim zobrazení */
  (function () {
    var prep = document.getElementById("prepinac-rezimu");
    if (!prep) return;

    function uloz(r) {
      try {
        if (r) localStorage.setItem("mpkral-rezim", r);
        else localStorage.removeItem("mpkral-rezim");
      } catch (e) { /* private mode — vydrží jen do konce stránky */ }
    }
    function ulozeny() {
      try { return localStorage.getItem("mpkral-rezim"); } catch (e) { return null; }
    }
    function podleSystemu() {
      return window.matchMedia && window.matchMedia("(prefers-color-scheme: dark)").matches
        ? "dark" : "light";
    }
    function platny() {
      return document.documentElement.getAttribute("data-theme") || podleSystemu();
    }
    function vykresli() {
      var tma = platny() === "dark";
      prep.setAttribute("aria-pressed", tma ? "true" : "false");
      prep.setAttribute("aria-label", tma ? "Přepnout na světlý režim" : "Přepnout na tmavý režim");
      prep.title = tma ? "Světlý režim" : "Tmavý režim";
    }

    prep.addEventListener("click", function () {
      var novy = platny() === "dark" ? "light" : "dark";
      document.documentElement.setAttribute("data-theme", novy);
      uloz(novy);
      vykresli();
    });

    /* dokud si člověk nevybral, sledovat nastavení systému */
    if (window.matchMedia) {
      window.matchMedia("(prefers-color-scheme: dark)").addEventListener("change", function () {
        if (!ulozeny()) vykresli();
      });
    }
    vykresli();
  })();

  /* ---------------------------------------------------------- hlavička */
  var burger = document.getElementById("hamburger");
  if (burger) {
    burger.addEventListener("click", function () {
      var nav = document.querySelector(".hl-dolni");
      var otevreno = nav.classList.toggle("otevrena");
      burger.setAttribute("aria-expanded", otevreno ? "true" : "false");
    });
  }

  var filtryTl = document.getElementById("filtry-tlacitko");
  if (filtryTl) {
    filtryTl.addEventListener("click", function () {
      document.getElementById("filtry").classList.toggle("otevrene");
    });
  }

  /* ---------------------------------------------------------- karty: pohledy */
  document.querySelectorAll(".produkt-fotka").forEach(function (ramec) {
    var predni = ramec.querySelector("[data-predni]");
    var zadni = ramec.querySelector("[data-zadni]");
    if (!predni || !zadni) return;

    ramec.addEventListener("mouseenter", function () { zadni.classList.remove("skryta"); });
    ramec.addEventListener("mouseleave", function () { zadni.classList.add("skryta"); });

    ramec.querySelectorAll(".prepinac-pohledu button").forEach(function (b) {
      b.addEventListener("click", function () {
        ramec.querySelectorAll(".prepinac-pohledu button").forEach(function (x) {
          x.classList.remove("aktivni");
        });
        b.classList.add("aktivni");
        zadni.classList.toggle("skryta", b.dataset.pohled !== "zadni");
      });
    });
  });

  /* ---------------------------------------------------------- karty: varianty */
  document.querySelectorAll("[data-produkt]").forEach(function (karta) {
    var predni = karta.querySelector("[data-predni]");
    var zadni = karta.querySelector("[data-zadni]");
    var prepinac = karta.querySelector(".prepinac-pohledu");
    var znacka = karta.querySelector(".znacka-pohledu");

    karta.querySelectorAll(".vzornik").forEach(function (tl) {
      if (!tl.dataset.varianta) return;
      tl.addEventListener("click", function () {
        var d = JSON.parse(tl.dataset.varianta);
        karta.querySelectorAll(".vzornik").forEach(function (x) { x.classList.remove("aktivni"); });
        tl.classList.add("aktivni");

        if (predni) {
          predni.src = d.fotky["přední"] || d.fotky["detail"] || predni.src;
          predni.alt = d.rada + ", " + d.varianta;
        }
        var maZadni = !!d.fotky["zadní"];
        if (zadni) {
          zadni.src = d.fotky["zadní"] || "";
          zadni.style.display = maZadni ? "" : "none";
          zadni.classList.add("skryta");
        }
        if (prepinac) prepinac.style.display = maZadni ? "" : "none";
        if (znacka) znacka.style.display = maZadni ? "none" : "";
        karta.dataset.varianta = d.varianta;
      });
    });
  });

  /* ---------------------------------------------------------- rozpis v kartě */
  document.querySelectorAll("[data-otevrit-rozpis]").forEach(function (tl) {
    tl.addEventListener("click", function () {
      var r = tl.parentElement.querySelector("[data-rozpis]");
      if (!r) return;
      var otevreno = r.classList.toggle("otevreny");
      tl.textContent = otevreno ? "Skrýt rozpis" : "Přidat do poptávky";
    });
  });

  /* ---------------------------------------------------------- počty kusů */
  function souhrn(blok) {
    var n = 0;
    blok.querySelectorAll("[data-ks]").forEach(function (i) { n += parseInt(i.value, 10) || 0; });
    blok.querySelectorAll("[data-ks-out]").forEach(function (o) { n += parseInt(o.textContent, 10) || 0; });
    var c = blok.querySelector("[data-celkem]");
    if (c) c.textContent = n;
    return n;
  }

  function blokRozpisu(el) {
    return el.closest("[data-rozpis]") || el.closest(".detail-info") || document;
  }

  document.querySelectorAll("[data-ks]").forEach(function (i) {
    i.addEventListener("input", function () { souhrn(blokRozpisu(i)); });
  });

  document.querySelectorAll(".stepper button").forEach(function (b) {
    b.addEventListener("click", function () {
      var out = b.parentElement.querySelector("output");
      var v = (parseInt(out.textContent, 10) || 0) + parseInt(b.dataset.krok, 10);
      out.textContent = Math.max(0, v);
      souhrn(blokRozpisu(b));
    });
  });

  /* ---------------------------------------------------------- přidání do šanonu */
  document.querySelectorAll("[data-do-sanonu]").forEach(function (tl) {
    tl.addEventListener("click", function () {
      var blok = blokRozpisu(tl);
      var karta = tl.closest("[data-produkt]");
      var velikosti = {};

      blok.querySelectorAll("[data-ks]").forEach(function (i) {
        var n = parseInt(i.value, 10) || 0;
        if (n > 0) velikosti[i.dataset.ks] = n;
      });
      blok.querySelectorAll("[data-ks-out]").forEach(function (o) {
        var n = parseInt(o.textContent, 10) || 0;
        if (n > 0) velikosti[o.dataset.ksOut] = (velikosti[o.dataset.ksOut] || 0) + n;
      });

      if (!Object.keys(velikosti).length) {
        tl.textContent = "Zapište nejdřív počty";
        setTimeout(function () { tl.textContent = "Přidat do šanonu"; }, 1600);
        return;
      }

      var nazev, varianta, fotka;
      if (karta) {
        nazev = karta.dataset.rada;
        varianta = karta.dataset.varianta || (karta.querySelector(".vzornik.aktivni") || {}).title || "";
        var f1 = karta.querySelector("[data-predni]");
        fotka = f1 ? f1.getAttribute("src") : "";
      } else {
        nazev = (document.getElementById("nazev-produktu") || {}).textContent || "Produkt";
        varianta = "";
        var f2 = document.getElementById("hlavni-fotka");
        fotka = f2 ? f2.getAttribute("src") : "";
      }

      var s = nacti();
      s.push({ nazev: nazev, varianta: varianta, fotka: fotka, velikosti: velikosti, logo: false });
      uloz(s);

      tl.textContent = "✓ Přidáno do šanonu";
      setTimeout(function () { tl.textContent = "Přidat do šanonu"; }, 1600);
    });
  });

  /* ---------------------------------------------------------- detail: pohledy */
  var hlavniFotka = document.getElementById("hlavni-fotka");
  document.querySelectorAll("#nahledy .nahled").forEach(function (n) {
    n.addEventListener("click", function () {
      document.querySelectorAll("#nahledy .nahled").forEach(function (x) { x.classList.remove("aktivni"); });
      n.classList.add("aktivni");
      var img = n.querySelector("img");
      if (hlavniFotka && img) hlavniFotka.src = img.src;
      hlavniFotka.dataset.pohled = n.dataset.nahled;
    });
  });

  /* detail: barevné varianty */
  document.querySelectorAll("#varianty .vzornik").forEach(function (tl) {
    tl.addEventListener("click", function () {
      var d = JSON.parse(tl.dataset.varianta);
      document.querySelectorAll("#varianty .vzornik").forEach(function (x) { x.classList.remove("aktivni"); });
      tl.classList.add("aktivni");

      var nadpis = document.getElementById("nazev-produktu");
      if (nadpis) nadpis.innerHTML = esc(d.rada) + ' <span class="varianta-nazev">' + esc(d.varianta) + "</span>";
      document.querySelectorAll("[data-strih]").forEach(function (e) { e.textContent = d.strih; });

      var nahledy = document.getElementById("nahledy");
      if (nahledy) {
        nahledy.innerHTML = "";
        [["přední", "Přední"], ["zadní", "Zadní"], ["detail", "Detail"]].forEach(function (par) {
          if (!d.fotky[par[0]]) return;
          var b = document.createElement("button");
          b.type = "button";
          b.className = "nahled";
          b.dataset.nahled = par[0];
          b.innerHTML = '<span class="ramecek karta" style="display:block"><img src="' + par[1] + '" alt=""></span>'
            + '<span class="mono-popisek">' + par[1] + "</span>";
          b.querySelector("img").src = d.fotky[par[0]];
          b.addEventListener("click", function () {
            nahledy.querySelectorAll(".nahled").forEach(function (x) { x.classList.remove("aktivni"); });
            b.classList.add("aktivni");
            if (hlavniFotka) hlavniFotka.src = d.fotky[par[0]];
            hlavniFotka.dataset.pohled = par[0];
          });
          nahledy.appendChild(b);
        });
        var prvni = nahledy.querySelector(".nahled");
        if (prvni) prvni.classList.add("aktivni");
      }

      if (hlavniFotka) {
        hlavniFotka.src = d.fotky["přední"] || d.fotky["detail"] || hlavniFotka.src;
        hlavniFotka.dataset.pohled = "přední";
      }
      location.hash = d.varianta.replace(/\s+/g, "-");
    });
  });

  /* lupa — jen na DETAIL fotky */
  var lupa = document.getElementById("lupa");
  if (lupa && hlavniFotka) {
    hlavniFotka.style.cursor = "zoom-in";
    hlavniFotka.addEventListener("click", function () {
      if (hlavniFotka.dataset.pohled !== "detail") return;
      document.getElementById("lupa-fotka").src = hlavniFotka.src;
      lupa.classList.add("otevrena");
    });
    lupa.addEventListener("click", function () { lupa.classList.remove("otevrena"); });
    document.addEventListener("keydown", function (e) {
      if (e.key === "Escape") lupa.classList.remove("otevrena");
    });
  }

  /* logo u produktu */
  var chciLogo = document.getElementById("chci-logo");
  if (chciLogo) {
    chciLogo.addEventListener("change", function () {
      document.getElementById("logo-pole").style.display = chciLogo.checked ? "block" : "none";
    });
    var soubor = document.getElementById("logo-soubor");
    if (soubor) {
      soubor.addEventListener("change", function () {
        document.getElementById("logo-nazev").textContent =
          soubor.files.length ? "vybráno: " + soubor.files[0].name : "";
      });
    }
  }

  /* ---------------------------------------------------------- katalog: filtry */
  var vypis = document.getElementById("vypis");
  if (vypis) {
    var hledani = document.getElementById("hledani");

    function filtruj() {
      var kat = [], zn = [];
      document.querySelectorAll('[data-filtr="kategorie"]:checked').forEach(function (i) { kat.push(i.value); });
      document.querySelectorAll('[data-filtr="znacka"]:checked').forEach(function (i) { zn.push(i.value); });
      var dotaz = (hledani && hledani.value || "").trim().toLowerCase();

      var videno = 0;
      vypis.querySelectorAll("[data-produkt]").forEach(function (k) {
        var okKat = !kat.length || kat.indexOf(k.dataset.kategorie) > -1;
        var okZn = !zn.length || zn.indexOf(k.dataset.znacka) > -1;
        var okDotaz = !dotaz || k.textContent.toLowerCase().indexOf(dotaz) > -1;
        var zobrazit = okKat && okZn && okDotaz;
        k.style.display = zobrazit ? "" : "none";
        if (zobrazit) videno++;
      });
      var info = document.querySelector("[data-pocet-vypisu]");
      if (info) info.textContent = "Zobrazeno " + videno + " střihů.";
    }

    document.querySelectorAll("[data-filtr]").forEach(function (i) {
      i.addEventListener("change", filtruj);
    });
    if (hledani) hledani.addEventListener("input", filtruj);

    var razeni = document.getElementById("razeni");
    if (razeni) {
      razeni.addEventListener("change", function () {
        var karty = Array.prototype.slice.call(vypis.querySelectorAll("[data-produkt]"));
        karty.sort(function (a, b) {
          var kl = razeni.value === "kategorie" ? "kategorie" : "znacka";
          return (a.dataset[kl] || "").localeCompare(b.dataset[kl] || "", "cs");
        });
        karty.forEach(function (k) { vypis.appendChild(k); });
      });
    }

    /* kategorie z adresy (#0 … #6).
       Musí reagovat i na hashchange — klik na kategorii uvnitř katalogu
       stránku znovu nenačte, takže by se jinak nestalo vůbec nic. */
    function zHashe() {
      var pole = document.querySelectorAll('[data-filtr="kategorie"]');
      var idx = parseInt((location.hash || "").slice(1), 10);
      pole.forEach(function (i) { i.checked = false; });
      if (!isNaN(idx) && pole[idx]) pole[idx].checked = true;

      /* zvýraznit odpovídající položku v navigaci */
      document.querySelectorAll(".navigace a").forEach(function (a, j) {
        a.classList.toggle("aktivni", !isNaN(idx) && j === idx);
      });

      filtruj();
    }

    window.addEventListener("hashchange", function () {
      zHashe();
      var v = document.getElementById("vypis");
      if (v) {
        var y = v.getBoundingClientRect().top + window.pageYOffset - 150;
        window.scrollTo({ top: Math.max(0, y), behavior: "smooth" });
      }
    });

    /* klik na kategorii, která už je v adrese, hashchange nevyvolá */
    document.querySelectorAll('.navigace a[href*="katalog.html#"]').forEach(function (a) {
      a.addEventListener("click", function () {
        var cil = a.getAttribute("href").split("#")[1];
        if (cil === (location.hash || "").slice(1)) zHashe();
      });
    });

    /* ruční odškrtnutí filtru má adresu srovnat, ať spolu nekolidují */
    document.querySelectorAll('[data-filtr="kategorie"]').forEach(function (i) {
      i.addEventListener("change", function () {
        if (location.hash) history.replaceState(null, "", location.pathname);
        document.querySelectorAll(".navigace a").forEach(function (a) {
          a.classList.remove("aktivni");
        });
      });
    });

    zHashe();
  }

  /* ---------------------------------------------------------- stránka šanonu */
  var obsah = document.getElementById("sanon-obsah");
  if (obsah) {
    (function vykresliSanon() {
      var s = nacti();
      if (!s.length) {
        obsah.innerHTML = '<div class="karta prazdno"><p>Šanon je zatím prázdný.</p>'
          + '<p><a href="katalog.html">Vybrat z katalogu →</a></p></div>';
        return;
      }
      var celkem = 0;
      obsah.innerHTML = s.map(function (p, i) {
        var vel = Object.keys(p.velikosti).sort(function (a, b) { return a - b; });
        celkem += kusy(p);
        var rozpis = vel.map(function (v) {
          return '<span class="odznak">' + esc(v) + " × " + (parseInt(p.velikosti[v], 10) || 0) + "</span>";
        }).join(" ");
        return '<article class="sanon-polozka karta">'
          + '<div class="mini"><img src="' + bezpecnaCesta(p.fotka) + '" alt=""></div>'
          + "<div><h3 style=\"margin:0 0 4px;font-size:17px\">" + esc(p.nazev) + "</h3>"
          + '<p class="mono" style="color:var(--ocel);margin:0 0 8px">' + esc(p.varianta || "") + "</p>"
          + "<div>" + rozpis + "</div>"
          + '<p class="mono" style="margin:8px 0 0">celkem ' + kusy(p) + " ks</p></div>"
          + '<button type="button" class="tl tl-obrys" data-odebrat="' + i + '" style="padding:8px 12px">Odebrat</button>'
          + "</article>";
      }).join("");

      obsah.insertAdjacentHTML("beforeend",
        '<p class="mono" style="margin-top:16px">Celkem <b>' + s.length + "</b> položek · <b>"
        + celkem + "</b> ks · ceny uvádíme bez DPH</p>");

      obsah.querySelectorAll("[data-odebrat]").forEach(function (b) {
        b.addEventListener("click", function () {
          var t = nacti();
          t.splice(parseInt(b.dataset.odebrat, 10), 1);
          uloz(t);
          vykresliSanon();
        });
      });
    })();

    var vyprazdnit = document.querySelector("[data-vyprazdnit]");
    if (vyprazdnit) {
      vyprazdnit.addEventListener("click", function () {
        if (confirm("Opravdu vyprázdnit šanon?")) { uloz([]); location.reload(); }
      });
    }
  }

  /* ---------------------------------------------------------- formulář */
  document.querySelectorAll("[data-poptavka]").forEach(function (f) {
    f.addEventListener("submit", function (e) {
      e.preventDefault();
      var box = document.createElement("div");
      box.className = "karta";
      box.style.cssText = "padding:20px;margin-top:16px";
      box.innerHTML = "<h3 style=\"margin:0 0 6px;font-size:18px\">Poptávku jsme přijali, ozveme se do 2 pracovních dnů.</h3>"
        + '<p class="mono" style="color:var(--ocel);margin:0">Náčrt, formulář zatím neodesílá.</p>';
      f.replaceWith(box);
    });
  });

  vykresliPocty();
})();
