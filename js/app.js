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
  var hlavicka = document.getElementById("hlavicka");
  if (hlavicka) {
    var stin = function () { hlavicka.classList.toggle("odscrollovano", window.scrollY > 4); };
    window.addEventListener("scroll", stin, { passive: true });
    stin();
  }
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

      var puvodni = tl.dataset.text || (tl.dataset.text = tl.textContent);
      var kam = /košík/i.test(puvodni) ? "do košíku" : "do šanonu";
      if (!Object.keys(velikosti).length) {
        tl.textContent = "Zapište nejdřív počty";
        setTimeout(function () { tl.textContent = puvodni; }, 1600);
        return;
      }

      /* zvolená barva: v kartě i na stránce produktu je to aktivní vzorník */
      var vz = (karta || document).querySelector(karta ? ".vzornik.aktivni" : "#varianty .vzornik.aktivni");
      var d = {};
      try { d = JSON.parse(vz && vz.dataset.varianta || "{}"); } catch (e) { d = {}; }
      var nazev = d.rada || (karta ? karta.dataset.rada : (document.getElementById("nazev-produktu") || {}).textContent) || "Produkt";
      var foto = karta ? karta.querySelector("[data-predni]") : document.getElementById("hlavni-fotka");

      var s = nacti();
      s.push({ rada_id: d.rada_id || (karta && karta.dataset.id) || "", varianta_id: d.id || "",
               nazev: nazev, varianta: d.varianta || "", fotka: foto ? foto.getAttribute("src") : "",
               velikosti: velikosti, logo: false });
      uloz(s);

      tl.textContent = "✓ Přidáno " + kam;
      setTimeout(function () { tl.textContent = puvodni; }, 1600);
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

  /* ---------------------------------------------------------- košík s cenami a objednávka */
  var obsah = document.getElementById("sanon-obsah");
  var dataObchodu = document.getElementById("obchod-data");
  if (obsah && obsah.hasAttribute("data-kosik") && dataObchodu) {
    kosikAObjednavka(obsah, JSON.parse(dataObchodu.textContent));
  } else if (obsah) {
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

  /* jako na serveru: celé koruny bez desetin, jinak na haléře (souhrn pak sedí s potvrzením) */
  function kc(n) {
    var h = Math.round(n * 100) / 100, cele = Math.abs(h % 1) < 0.005;
    return h.toLocaleString("cs-CZ", { minimumFractionDigits: cele ? 0 : 2, maximumFractionDigits: cele ? 0 : 2 })
      .replace(/\s/g, "\u00a0") + "\u00a0Kč";
  }

  /* Cena za kus podle množstevní hladiny: rozhoduje součet kusů téže řady v košíku. */
  function cenaKusu(info, ksRady) {
    var c = info.cena || 0;
    Object.keys(info.hladiny || {}).forEach(function (od) {
      if (ksRady >= parseInt(od, 10) && info.hladiny[od]) c = info.hladiny[od];
    });
    return c;
  }

  function kosikAObjednavka(obsah, data) {
    var sDph = function (c) { return data.platce ? c * (100 + data.sazba) / 100 : c; };
    var formular = document.querySelector("[data-objednavka]");
    var sekce = document.querySelector("[data-objednavka-sekce]");
    var tlacitka = document.querySelector("[data-kosik-tlacitka]");

    function polozky() {
      /* jen položky, které na webu pořád jsou (řada mohla mezitím zmizet nebo změnit cenu) */
      return nacti().filter(function (p) { return p.rada_id && data.ceny[p.rada_id]; });
    }

    function spocitej() {
      var s = polozky(), ksRady = {}, zbozi = 0, naDotaz = 0;
      s.forEach(function (p) { ksRady[p.rada_id] = (ksRady[p.rada_id] || 0) + kusy(p); });
      var radky = s.map(function (p) {
        var info = data.ceny[p.rada_id], ks = kusy(p), kus = cenaKusu(info, ksRady[p.rada_id]);
        if (!kus) naDotaz++;
        zbozi += kus * ks;
        return { p: p, ks: ks, kus: kus };
      });
      var doprava = vybrana("doprava"), platba = vybrana("platba");
      var bezDph = zbozi + (doprava ? doprava.cena || 0 : 0) + (platba ? platba.poplatek || 0 : 0);
      return { radky: radky, zbozi: zbozi, doprava: doprava, platba: platba, bezDph: bezDph,
               sDph: sDph(bezDph), naDotaz: naDotaz };
    }

    function vybrana(co) {
      var seznam = co === "doprava" ? data.doprava : data.platby;
      var v = document.querySelector('input[name="' + co + '"]:checked');
      return v ? seznam.filter(function (x) { return x.id === v.value; })[0] : null;
    }

    function vykresliVolby() {
      var dop = document.querySelector("[data-doprava]"), pl = document.querySelector("[data-platby]");
      if (!dop || !pl) return;
      dop.innerHTML = data.doprava.map(function (d, i) {
        return '<label class="volba"><input type="radio" name="doprava" value="' + esc(d.id) + '"' + (i === 0 ? " checked" : "") + ">"
          + "<span>" + esc(d.nazev) + "</span><b>" + (d.cena ? kc(sDph(d.cena)) : "zdarma") + "</b></label>";
      }).join("");
      function platby() {
        var d = vybrana("doprava");
        var mozne = data.platby.filter(function (p) { return !p.jen_doprava || !d || p.jen_doprava.indexOf(d.id) > -1; });
        var drive = (vybrana("platba") || {}).id;
        pl.innerHTML = mozne.map(function (p, i) {
          var zvolit = drive ? p.id === drive : i === 0;
          return '<label class="volba"><input type="radio" name="platba" value="' + esc(p.id) + '"' + (zvolit ? " checked" : "") + ">"
            + "<span>" + esc(p.nazev) + "</span><b>" + (p.poplatek ? "+ " + kc(sDph(p.poplatek)) : "") + "</b></label>";
        }).join("");
        if (!vybrana("platba") && pl.querySelector("input")) pl.querySelector("input").checked = true;
      }
      platby();
      dop.addEventListener("change", function () { platby(); vykresli(); });
      pl.addEventListener("change", vykresli);
    }

    function vykresli() {
      var v = spocitej();
      if (!v.radky.length) {
        obsah.innerHTML = '<div class="karta prazdno"><p>Košík je zatím prázdný.</p>'
          + '<p><a href="katalog.html">Vybrat z katalogu →</a></p></div>';
        if (sekce) sekce.hidden = true;
        if (tlacitka) tlacitka.hidden = true;
        return;
      }
      if (sekce) sekce.hidden = false;
      if (tlacitka) tlacitka.hidden = false;
      obsah.innerHTML = v.radky.map(function (r, i) {
        var vel = Object.keys(r.p.velikosti).sort(function (a, b) { return a - b; });
        var rozpis = vel.map(function (x) {
          return '<span class="odznak">' + esc(x) + " × " + (parseInt(r.p.velikosti[x], 10) || 0) + "</span>";
        }).join(" ");
        var cena = r.kus ? kc(sDph(r.kus)) + " / ks · <b>" + kc(sDph(r.kus * r.ks)) + "</b>" : "cena na dotaz";
        return '<article class="sanon-polozka karta">'
          + '<div class="mini"><img src="' + bezpecnaCesta(r.p.fotka) + '" alt=""></div>'
          + "<div><h3 style=\"margin:0 0 4px;font-size:17px\">" + esc(r.p.nazev) + "</h3>"
          + '<p class="mono" style="color:var(--ocel);margin:0 0 8px">' + esc(r.p.varianta || "") + "</p>"
          + "<div>" + rozpis + "</div>"
          + '<p class="mono" style="margin:8px 0 0">' + r.ks + " ks · " + cena + "</p></div>"
          + '<button type="button" class="tl tl-obrys" data-odebrat="' + i + '" style="padding:8px 12px">Odebrat</button>'
          + "</article>";
      }).join("");
      obsah.querySelectorAll("[data-odebrat]").forEach(function (b) {
        b.addEventListener("click", function () {
          var t = polozky();
          t.splice(parseInt(b.dataset.odebrat, 10), 1);
          uloz(t);
          vykresli();
        });
      });
      var souhrn = document.querySelector("[data-souhrn]");
      if (souhrn) {
        var radek = function (a, b) { return "<div><span>" + a + "</span><span>" + b + "</span></div>"; };
        souhrn.innerHTML = radek("Zboží", kc(sDph(v.zbozi)))
          + radek("Doprava" + (v.doprava ? " · " + esc(v.doprava.nazev) : ""), v.doprava && v.doprava.cena ? kc(sDph(v.doprava.cena)) : "zdarma")
          + (v.platba && v.platba.poplatek ? radek("Platba · " + esc(v.platba.nazev), kc(sDph(v.platba.poplatek))) : "")
          + (data.platce ? radek("Bez DPH", kc(v.bezDph)) + radek("DPH " + data.sazba + " %", kc(v.sDph - v.bezDph)) : "")
          + '<div class="celkem"><span>Celkem k úhradě</span><span>' + kc(v.sDph) + "</span></div>"
          + (v.naDotaz ? '<p class="mono">U ' + v.naDotaz + " položek je cena na dotaz. Potvrdíme ji e-mailem před výrobou.</p>" : "");
      }
      vykresliPocty();
    }

    vykresliVolby();
    vykresli();

    var vyprazdnit = document.querySelector("[data-vyprazdnit]");
    if (vyprazdnit) vyprazdnit.addEventListener("click", function () {
      if (confirm("Opravdu vyprázdnit košík?")) { uloz([]); vykresli(); }
    });

    var jina = document.querySelector("[data-jina-adresa]"), dodaci = document.querySelector("[data-dodaci]");
    if (jina && dodaci) jina.addEventListener("change", function () { dodaci.hidden = !jina.checked; });

    if (!formular) return;
    formular.addEventListener("submit", function (e) {
      e.preventDefault();
      var chyba = formular.querySelector("[data-chyba]"), tl = formular.querySelector('button[type="submit"]');
      var f = new FormData(formular), zakaznik = {};
      ["firma", "ico", "dic", "jmeno", "email", "telefon", "ulice", "mesto", "psc",
       "dod_jmeno", "dod_ulice", "dod_mesto", "dod_psc"].forEach(function (k) { zakaznik[k] = (f.get(k) || "").trim(); });
      zakaznik.jina_adresa = !!f.get("jina_adresa");
      var telo = {
        polozky: polozky().map(function (p) { return { rada_id: p.rada_id, varianta_id: p.varianta_id, velikosti: p.velikosti }; }),
        doprava: (vybrana("doprava") || {}).id, platba: (vybrana("platba") || {}).id,
        zakaznik: zakaznik, poznamka: (f.get("poznamka") || "").trim(), souhlas: !!f.get("souhlas"), web: f.get("web") || ""
      };
      tl.disabled = true; chyba.textContent = "";
      fetch("/api/objednavka", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(telo) })
        .then(function (r) { return r.json().then(function (j) { return { ok: r.ok, j: j }; }); })
        .then(function (o) {
          if (!o.ok) throw new Error(o.j.chyba || "Objednávku se nepodařilo odeslat.");
          uloz([]);
          location.href = o.j.odkaz;
        })
        .catch(function (err) {
          chyba.textContent = (err && err.message && !/fetch|JSON|NetworkError/i.test(err.message))
            ? err.message : "Objednávku se nepodařilo odeslat. Zkuste to znovu, nebo zavolejte.";
          tl.disabled = false;
        });
    });
  }

  /* ---------------------------------------------------------- fotky v kategorii */
  /* Po najetí na dlaždici se střídají fotky střihů z kategorie. */
  document.querySelectorAll(".kat-foto").forEach(function (ramec) {
    var fotky = ramec.querySelectorAll("img");
    var karta = ramec.parentNode, i = 0, cas = null;
    if (fotky.length < 2) return;
    function ukaz(n) {
      fotky[i].classList.remove("vidna");
      i = n % fotky.length;
      fotky[i].classList.add("vidna");
    }
    karta.addEventListener("mouseenter", function () {
      clearInterval(cas);
      cas = setInterval(function () { ukaz(i + 1); }, 1100);
    });
    karta.addEventListener("mouseleave", function () {
      clearInterval(cas);
      ukaz(0);
    });
  });

  /* ---------------------------------------------------------- formulář */
  document.querySelectorAll("[data-poptavka]").forEach(function (f) {
    f.addEventListener("submit", function (e) {
      e.preventDefault();
      var tl = f.querySelector('button[type="submit"]'), data = {};
      new FormData(f).forEach(function (v, k) { data[k] = String(v).trim(); });
      if (tl) tl.disabled = true;
      function hotovo(poznamka) {
        var box = document.createElement("div");
        box.className = "karta";
        box.style.cssText = "padding:20px;margin-top:16px";
        box.innerHTML = "<h3 style=\"margin:0 0 6px;font-size:18px\">Poptávku jsme přijali, ozveme se do 2 pracovních dnů.</h3>"
          + (poznamka ? '<p class="mono" style="color:var(--ocel);margin:0">' + poznamka + "</p>" : "");
        f.replaceWith(box);
      }
      fetch("/api/poptavka", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(data) })
        .then(function (r) {
          if (r.status === 404 || r.status === 405) { hotovo("Náčrt, formulář zatím neodesílá."); return; }
          return r.json().then(function (j) {
            if (!r.ok) throw new Error(j.chyba || "Poptávku se nepodařilo odeslat.");
            hotovo("");
          });
        })
        .catch(function (err) {
          if (tl) tl.disabled = false;
          alert(err && err.message ? err.message : "Poptávku se nepodařilo odeslat, zkuste to prosím znovu.");
        });
    });
  });

  vykresliPocty();
})();
