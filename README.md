# On voto? · 29N Barcelona

Cercador per saber la mesa i el col·legi electoral a partir de l'adreça i del primer cognom.
És una web estàtica: `index.html` + `dades.json`. Les cerques es fan al navegador i no s'envia ni es desa cap dada.

## Publicar
- **GitHub Pages**: Settings → Pages → Deploy from branch → `main` / root (cal que el repositori sigui públic al pla gratuït).
- La web no s'indexa als cercadors gràcies a `robots.txt` i a les etiquetes `noindex` de l'`index.html`.

## Actualitzar les dades (abans de cada elecció)
1. Baixa el *Callejero del Censo Electoral* de l'INE (província de Barcelona, el període més recent):
   https://www.ine.es/dyngs/DAB/es/index.htm?cid=1390
2. Actualitza l'Excel de meses i locals (`eines/locals_electorals_municipi_barcelona.xlsx`, pestanya "Barcelona ciutat").
3. Executa:
   ```
   pip install openpyxl
   python3 eines/construir_dades.py TRAM.P08.Dxxxxxx.Gxxxxxx VIAS.P08.Dxxxxxx.Gxxxxxx eines/locals_electorals_municipi_barcelona.xlsx
   ```
   Això torna a generar `dades.json`. A `eines/locals.json` hi ha els noms i les adreces de locals corregits a mà, que tenen preferència sobre els de l'Excel.

Fonts: INE (Cens Electoral, CC BY 4.0) i llistes oficials de locals i meses.
Elaborat per Jaume Oliva Sala.
