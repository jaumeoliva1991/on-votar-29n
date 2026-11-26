#!/usr/bin/env python3
"""Genera les dades del cercador per a tota la província de Barcelona.

Entrades:
  - TRAM i VIAS del Callejero del Censo Electoral de l'INE (província 08)
  - Text del PDF del BOP amb les seccions, meses i locals (llegit amb llegir_bop.py)
  - locals.json: correccions a mà de noms i adreces de locals (opcional)

Sortida (a l'arrel del web):
  dades/index.json        municipis i llista de carrers (per als suggeriments)
  dades/m/<codi>.json     trams, meses i locals de cada municipi

Ús:
  python3 eines/construir_provincia.py TRAM.P08... VIAS.P08... BOP.txt
"""
import json, os, re, sys, collections
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from construir_dades import TIPUS, TIPUS_ADR, PARTICULES, DISTRICTES, bonic, titol, llegir
from llegir_bop import parse, separar

AQUI = os.path.dirname(os.path.abspath(__file__))
SORTIDA = os.path.join(AQUI, "..", "dades")

TIPUS_EXTRA = {"CARRE": "Carrer", "AVGDA": "Avinguda", "CRA": "Carretera", "PSAJE": "Passatge", "JDINS": "Jardins",
               "URBAT": "Urbanització", "TRVA": "Travessera", "LLOC": "", "MASIA": "Masia", "C/": "Carrer",
               "PLAÇA": "Plaça", "PZ": "Plaça", "URB": "Urbanització", "AVDA": "Avinguda", "CR": "Carretera",
               "CRTA": "Carretera", "RAMBLA": "Rambla", "GRUP": "Grup", "JDIN": "Jardí", "PRAGE": "Paratge", "VNAT": "Veïnat", "PDA": "Partida", "GJA": "Granja", "PROL": "Prolongació", "CLLON": "Carreró", "APTES": "Apartaments", "COMPX": "Complex", "COL": "Colònia", "SECT": "Sector", "POLIG": "Polígon", "LUGAR": "Lloc", "JARD": "Jardins", "BARRI": "Barri", "TRRNT": "Torrent", "PARC": "Parc", "PLCET": "Placeta"}

ARTICLES = {"(L')": "L'", "(EL)": "El ", "(LA)": "La ", "(ELS)": "Els ", "(LES)": "Les "}

# Locals que el separador automàtic no resol
LOCALS_A_MA = {
    "CASAL DE SANTS C VIOLANT D'HONGRIA, REINA D'ARAGO (DE) 135, 08028 BARCELONA":
        ["Casal de Sants", "Carrer de Violant d'Hongria, Reina d'Aragó, 135", "08028"],
    "APSA (AIGÜES DEL PRAT, S.A.) PL AIGUA (DE L') 1, 08820 PRAT DE LLOBREGAT (EL), BARCELONA":
        ["APSA (Aigües del Prat)", "Plaça de l'Aigua, 1", "08820"],
}


def norm_txt(x):
    import unicodedata
    return "".join(c for c in unicodedata.normalize("NFD", x.lower()) if unicodedata.category(c) != "Mn")


def nom_municipi(n):
    m = re.match(r"^(.*?)\s*(\([^)]*\))$", n.strip())
    if m and m.group(2) in ARTICLES:
        return ARTICLES[m.group(2)] + titol(m.group(1))
    return titol(n)


def nom_via(tipus, llarg):
    t = (TIPUS_EXTRA.get(tipus) or TIPUS.get(tipus) or tipus.title()).lower()
    part = re.search(r"\(([^)]*)\)\s*$", llarg)
    part = (" " + part.group(1).lower()) if part else ""
    part = part.replace("' ", "'")
    part = {" l'": " de l'", " la": " de la", " les": " de les", " el": " del", " els": " dels"}.get(part, part)
    T = t[:1].upper() + t[1:]
    sep = "" if part.endswith("'") else " "
    llarg = re.sub(r"^C/\s*", "", llarg)
    nb = bonic(llarg)
    if t and norm_txt(nb) == norm_txt(T):
        return T
    n = f"{T}{part}{sep}{nb}" if t else nb
    return {"Gran via Corts Catalanes": "Gran Via de les Corts Catalanes",
            "Gran via Carles III": "Gran Via de Carles III"}.get(n, n)


def adreca(adr):
    """'C SALVADOR ESPRIU 3' -> 'Carrer Salvador Espriu, 3' ; 'PL AIGUA (DE L') 1' -> "Plaça de l'Aigua, 1" """
    m = re.match(r"^(\S+)\s+(.*?)\s*(\([^)]*\))?\s+(\d+\s?[A-Z]{0,3}|S/N|SN|KM[\s\d.,]*)$", adr.strip())
    if not m:
        return titol(adr)
    tipus, carrer, part, num = m.groups()
    t = TIPUS_EXTRA[tipus] if tipus in TIPUS_EXTRA else (TIPUS_ADR.get(tipus) or TIPUS.get(tipus) or tipus.title())
    part = PARTICULES.get(part or "", "")
    nomc = titol(carrer)
    via = f"{t} {part}{nomc}" if part.endswith("'") else (f"{t} {part} {nomc}" if part else f"{t} {nomc}")
    via = via.strip()
    via = {"Travessera Dalt": "Travessera de Dalt", "Travessera Corts": "Travessera de les Corts"}.get(via, via)
    num = "s/n" if num in ("S/N", "SN") else num.strip()
    return f"{via}, {num}"


def clau(mun, d, s, sub):
    # Barcelona sense municipi a la clau per mantenir els enllaços antics (?s=5-10)
    return f"{d}-{s}" + (f"-{sub}" if sub else "")


def main():
    tram, vias, bop = sys.argv[1:4]
    manuals = {}
    p = os.path.join(AQUI, "locals.json")
    if os.path.exists(p):
        manuals = json.load(open(p, encoding="utf-8"))

    # Meses del BOP
    files = parse(bop)
    munis, seccions, locals_ = {}, collections.defaultdict(dict), collections.defaultdict(dict)
    for f in files:
        munis[f["mun"]] = nom_municipi(f["municipi"])
        k = clau(f["mun"], f["dist"], f["sec"], f["sub"])
        seccions[f["mun"]].setdefault(k, []).append([f["mesa"], f["ini"], f["fi"], f["codi"]])
        if f["codi"] not in locals_[f["mun"]]:
            if f["codi"] in manuals:
                locals_[f["mun"]][f["codi"]] = manuals[f["codi"]]
            elif f["local_brut"].strip() in LOCALS_A_MA:
                locals_[f["mun"]][f["codi"]] = LOCALS_A_MA[f["local_brut"].strip()]
            else:
                nom, adr, zona, cp, pob = separar(f["local_brut"])
                locals_[f["mun"]][f["codi"]] = [titol(nom), adreca(adr), cp]

    # Vies
    noms = {}
    for l in llegir(vias):
        if not l.startswith("08"):
            continue
        noms[(l[2:5], l[5:10])] = nom_via(l[52:57].strip(), l[57:107].strip() or l[10:40].strip())

    # Trams
    trams = collections.defaultdict(lambda: collections.defaultdict(set))
    for l in llegir(tram):
        if not l.startswith("08"):
            continue
        mun, d, s = l[2:5], int(l[5:7]), int(l[7:10])
        sub = l[10:13].strip()
        sub = int(sub) if sub else 0
        k = clau(mun, d, s, sub)
        if k not in seccions.get(mun, {}):
            k2 = clau(mun, d, s, 0)
            k = k2 if k2 in seccions.get(mun, {}) else k
        trams[mun][l[20:25]].add((int(l[48:52]), int(l[53:57]), int(l[47]), k))

    os.makedirs(os.path.join(SORTIDA, "m"), exist_ok=True)
    codis = sorted(munis, key=lambda c: (c != "019", munis[c]))
    index_munis, n_carrers, sense_meses = [], 0, collections.Counter()
    for i, mun in enumerate(codis):
        carrers = sorted(([noms.get((mun, cv), "?"), sorted(ts)] for cv, ts in trams[mun].items()),
                         key=lambda c: c[0])
        index_munis.append([mun, munis[mun], [c[0] for c in carrers]])
        n_carrers += len(carrers)
        for c in carrers:
            for t in c[1]:
                if t[3] not in seccions[mun]:
                    sense_meses[mun] += 1
        dades = {"locals": locals_[mun], "seccions": seccions[mun],
                 "carrers": [[n, [list(t) for t in ts]] for n, ts in carrers]}
        if mun == "019":
            dades["districtes"] = {str(k): v for k, v in DISTRICTES.items()}
        json.dump(dades, open(os.path.join(SORTIDA, "m", f"{mun}.json"), "w", encoding="utf-8"),
                  ensure_ascii=False, separators=(",", ":"))

    data = re.search(r"D(\d{6})", os.path.basename(tram)).group(1)
    index = {"font": "Eleccions 29N · Província de Barcelona · Dades: INE, Cens Electoral (20%s/%s) i BOP" % (data[:2], data[2:4]),
             "municipis": index_munis}
    json.dump(index, open(os.path.join(SORTIDA, "index.json"), "w", encoding="utf-8"),
              ensure_ascii=False, separators=(",", ":"))
    print(f"{len(codis)} municipis, {n_carrers} carrers, {len(files)} meses")
    if sense_meses:
        print("Trams sense mesa:", dict(sense_meses))


if __name__ == "__main__":
    main()
