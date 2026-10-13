Furniture Sketch AI 0.4.2 — probna verzija za provjeru s profesionalnim stolarom.

Fajlovi: app.py, i18n.py, requirements.txt.

Izmjene: opcije leđa, nogice unutar ukupne visine, obračun dubine s frontom, upadajuća/naklapajuća fronta, uklonjena stolica, browser cookie za prihvatanje/odbijanje.

VAŽNO: formula dubine nuta po Y osi nije primijenjena jer značenje nije dovoljno precizno. Upadajuća falcana leđa imaju širinu -18mm, a visina je privremeno -2mm i mora se potvrditi. Ostali konstrukcijski detalji i okovi nisu certificirani za proizvodnju.

Cookie: koristi se extra-streamlit-components za fsa_consent_v1 (trajanje do 1 godine). Neobavezni analitički kolačići nisu uključeni. Obavezne kolačiće hostinga aplikacija ne kontroliše. Provjeriti ponašanje nakon refresh-a u stvarnom browseru.

Pokretanje: pip install -r requirements.txt ; streamlit run app.py
