"""
Mapping between JSON schema fields and PDF form fields for ZUS EWYP form.

The PDF has fields spread across 6 pages:
- Page 1: Dane osoby poszkodowanej (injured person data)
- Page 2: Adresy, Dane osoby która zawiadamia (addresses, notifier data)
- Page 3: Adresy korespondencyjne, Informacja o wypadku (correspondence, accident info)
- Page 4: Szczegóły wypadku (accident details)
- Page 5: Dane świadków (witnesses data)
- Page 6: Załączniki, sposób odbioru (attachments, response method)
"""

# =============================================================================
# FIELD MAPPING: JSON Schema Path -> PDF Field Name
# =============================================================================

FIELD_MAPPING = {
    # -------------------------------------------------------------------------
    # DANE OSOBY POSZKODOWANEJ (Page 1)
    # -------------------------------------------------------------------------
    "daneOsobyPoszkodowanej.pesel": "topmostSubform[0].Page1[0].PESEL[0]",
    "daneOsobyPoszkodowanej.dokumentTozsamosci": "topmostSubform[0].Page1[0].Rodzajseriainumerdokumentu[0]",
    "daneOsobyPoszkodowanej.imie": "topmostSubform[0].Page1[0].Imię[0]",
    "daneOsobyPoszkodowanej.nazwisko": "topmostSubform[0].Page1[0].Nazwisko[0]",
    "daneOsobyPoszkodowanej.dataUrodzenia": "topmostSubform[0].Page1[0].Dataurodzenia[0]",
    "daneOsobyPoszkodowanej.miejsceUrodzenia": "topmostSubform[0].Page1[0].Miejsceurodzenia[0]",
    "daneOsobyPoszkodowanej.numerTelefonu": "topmostSubform[0].Page1[0].Numertelefonu[0]",
    
    # -------------------------------------------------------------------------
    # ADRES ZAMIESZKANIA OSOBY POSZKODOWANEJ (Page 1)
    # -------------------------------------------------------------------------
    "adresZamieszkaniaOsobyPoszkodowanej.ulica": "topmostSubform[0].Page1[0].Ulica[0]",
    "adresZamieszkaniaOsobyPoszkodowanej.numerDomu": "topmostSubform[0].Page1[0].Numerdomu[0]",
    "adresZamieszkaniaOsobyPoszkodowanej.numerLokalu": "topmostSubform[0].Page1[0].Numerlokalu[0]",
    "adresZamieszkaniaOsobyPoszkodowanej.kodPocztowy": "topmostSubform[0].Page1[0].Kodpocztowy[0]",
    "adresZamieszkaniaOsobyPoszkodowanej.miejscowosc": "topmostSubform[0].Page1[0].Poczta[0]",
    "adresZamieszkaniaOsobyPoszkodowanej.nazwaPanstwa": "topmostSubform[0].Page1[0].Nazwapaństwa[0]",
    
    # -------------------------------------------------------------------------
    # ADRES OSTATNIEGO MIEJSCA ZAMIESZKANIA W POLSCE (Page 1 - section 2A)
    # -------------------------------------------------------------------------
    "adresOstatniegoMiejscaZamieszkaniaWPolsceLubPobytuPoszkodowanego.ulica": "topmostSubform[0].Page1[0].Ulica2A[0]",
    "adresOstatniegoMiejscaZamieszkaniaWPolsceLubPobytuPoszkodowanego.numerDomu": "topmostSubform[0].Page1[0].Numerdomu2A[0]",
    "adresOstatniegoMiejscaZamieszkaniaWPolsceLubPobytuPoszkodowanego.numerLokalu": "topmostSubform[0].Page1[0].Numerlokalu2A[0]",
    "adresOstatniegoMiejscaZamieszkaniaWPolsceLubPobytuPoszkodowanego.kodPocztowy": "topmostSubform[0].Page1[0].Kodpocztowy2A[0]",
    "adresOstatniegoMiejscaZamieszkaniaWPolsceLubPobytuPoszkodowanego.miejscowosc": "topmostSubform[0].Page1[0].Poczta2A[0]",
    
    # -------------------------------------------------------------------------
    # ADRES DO KORESPONDENCJI OSOBY POSZKODOWANEJ (Page 2)
    # -------------------------------------------------------------------------
    "adresDoKorespondencjiOsobyPoszkodowanej.ulica": "topmostSubform[0].Page2[0].Ulica[0]",
    "adresDoKorespondencjiOsobyPoszkodowanej.numerDomu": "topmostSubform[0].Page2[0].Numerdomu[0]",
    "adresDoKorespondencjiOsobyPoszkodowanej.numerLokalu": "topmostSubform[0].Page2[0].Numerlokalu[0]",
    "adresDoKorespondencjiOsobyPoszkodowanej.kodPocztowy": "topmostSubform[0].Page2[0].Kodpocztowy[0]",
    "adresDoKorespondencjiOsobyPoszkodowanej.miejscowosc": "topmostSubform[0].Page2[0].Poczta[0]",
    "adresDoKorespondencjiOsobyPoszkodowanej.nazwaPanstwa": "topmostSubform[0].Page2[0].Nazwapaństwa2[0]",
    
    # Checkboxes for correspondence type (Page 2)
    "adresDoKorespondencjiOsobyPoszkodowanej.sposobKorespondencji.adres": "topmostSubform[0].Page2[0].adres[0]",
    "adresDoKorespondencjiOsobyPoszkodowanej.sposobKorespondencji.poste_restante": "topmostSubform[0].Page2[0].posterestante[0]",
    "adresDoKorespondencjiOsobyPoszkodowanej.sposobKorespondencji.skrytka_pocztowa": "topmostSubform[0].Page2[0].skrytkapocztowa[0]",
    "adresDoKorespondencjiOsobyPoszkodowanej.sposobKorespondencji.przegrodka_pocztowa": "topmostSubform[0].Page2[0].przegrodkapocztowa[0]",
    
    # -------------------------------------------------------------------------
    # ADRES MIEJSCA PROWADZENIA POZAROLNICZEJ DZIAŁALNOŚCI (Page 2)
    # -------------------------------------------------------------------------
    "adresMiejscaProwadzeniaPozarolniczejDzialalnosci.ulica": "topmostSubform[0].Page2[0].Ulica2[0]",
    "adresMiejscaProwadzeniaPozarolniczejDzialalnosci.numerDomu": "topmostSubform[0].Page2[0].Numerdomu2[0]",
    "adresMiejscaProwadzeniaPozarolniczejDzialalnosci.numerLokalu": "topmostSubform[0].Page2[0].Numerlokalu2[0]",
    "adresMiejscaProwadzeniaPozarolniczejDzialalnosci.kodPocztowy": "topmostSubform[0].Page2[0].Kodpocztowy2[0]",
    "adresMiejscaProwadzeniaPozarolniczejDzialalnosci.miejscowosc": "topmostSubform[0].Page2[0].Poczta2[0]",
    "adresMiejscaProwadzeniaPozarolniczejDzialalnosci.numerTelefonu": "topmostSubform[0].Page2[0].Numertelefonu2[0]",
    
    # -------------------------------------------------------------------------
    # DANE OSOBY KTÓRA ZAWIADAMIA (Page 2)
    # -------------------------------------------------------------------------
    "daneOsobyKtoraZawiadamia.pesel": "topmostSubform[0].Page2[0].PESEL[0]",
    "daneOsobyKtoraZawiadamia.dokumentTozsamosci": "topmostSubform[0].Page2[0].Rodzajseriainumerdokumentu[0]",
    "daneOsobyKtoraZawiadamia.imie": "topmostSubform[0].Page2[0].Imię[0]",
    "daneOsobyKtoraZawiadamia.nazwisko": "topmostSubform[0].Page2[0].Nazwisko[0]",
    
    # -------------------------------------------------------------------------
    # ADRES ZAMIESZKANIA OSOBY KTÓRA ZAWIADAMIA (Page 2)
    # -------------------------------------------------------------------------
    "adresZamieszkaniaOsobyKtoraZawiadamia.ulica": "topmostSubform[0].Page2[0].Ulica2[1]",
    "adresZamieszkaniaOsobyKtoraZawiadamia.numerDomu": "topmostSubform[0].Page2[0].Numerdomu2[1]",
    "adresZamieszkaniaOsobyKtoraZawiadamia.numerLokalu": "topmostSubform[0].Page2[0].Numerlokalu2[1]",
    "adresZamieszkaniaOsobyKtoraZawiadamia.kodPocztowy": "topmostSubform[0].Page2[0].Kodpocztowy2[1]",
    "adresZamieszkaniaOsobyKtoraZawiadamia.miejscowosc": "topmostSubform[0].Page2[0].Poczta2[1]",
    
    # -------------------------------------------------------------------------
    # INFORMACJA O WYPADKU (Page 3)
    # -------------------------------------------------------------------------
    "informacjaOWypadku.dataWypadku": "topmostSubform[0].Page3[0].Datawyp[0]",
    "informacjaOWypadku.godzinaWypadku": "topmostSubform[0].Page3[0].Godzina[0]",
    "informacjaOWypadku.miejsceWypadku": "topmostSubform[0].Page3[0].Miejscewyp[0]",
    "informacjaOWypadku.planowanaGodzinaRozpoczeciaPracy": "topmostSubform[0].Page3[0].Godzina3A[0]",
    "informacjaOWypadku.planowanaGodzinaZakonczeniaPracy": "topmostSubform[0].Page3[0].Godzina3B[0]",
    
    # -------------------------------------------------------------------------
    # ADRES SPRAWOWANIA OPIEKI NAD DZIECKIEM DO LAT 3 (Page 3)
    # -------------------------------------------------------------------------
    "adresSprawowaniaOpiekiNadDzieckiemDoLat3.ulica": "topmostSubform[0].Page3[0].Ulica3[0]",
    "adresSprawowaniaOpiekiNadDzieckiemDoLat3.numerDomu": "topmostSubform[0].Page3[0].Numerdomu3[0]",
    "adresSprawowaniaOpiekiNadDzieckiemDoLat3.numerLokalu": "topmostSubform[0].Page3[0].Numerlokalu3[0]",
    "adresSprawowaniaOpiekiNadDzieckiemDoLat3.kodPocztowy": "topmostSubform[0].Page3[0].Kodpocztowy3[0]",
    "adresSprawowaniaOpiekiNadDzieckiemDoLat3.miejscowosc": "topmostSubform[0].Page3[0].Poczta3[0]",
    "adresSprawowaniaOpiekiNadDzieckiemDoLat3.numerTelefonu": "topmostSubform[0].Page3[0].Numertelefonu3[0]",
    
    # -------------------------------------------------------------------------
    # DANE OSOBY KTÓRA ZAWIADAMIA - dodatkowe (Page 3)
    # -------------------------------------------------------------------------
    "daneOsobyKtoraZawiadamia.dataUrodzenia": "topmostSubform[0].Page3[0].Dataurodzenia[0]",
    "daneOsobyKtoraZawiadamia.numerTelefonu": "topmostSubform[0].Page3[0].Numertelefonu3[0]",
    
    # -------------------------------------------------------------------------
    # ADRES OSTATNIEGO MIEJSCA ZAMIESZKANIA OSOBY KTÓRA ZAWIADAMIA (Page 3)
    # -------------------------------------------------------------------------
    "adresOstatniegoMiejscaZamieszkaniaWPolsceLubPobytuOsobyKtoraZawiadamia.ulica": "topmostSubform[0].Page3[0].Ulica2[0]",
    "adresOstatniegoMiejscaZamieszkaniaWPolsceLubPobytuOsobyKtoraZawiadamia.numerDomu": "topmostSubform[0].Page3[0].Numerdomu2[0]",
    "adresOstatniegoMiejscaZamieszkaniaWPolsceLubPobytuOsobyKtoraZawiadamia.numerLokalu": "topmostSubform[0].Page3[0].Numerlokalu2[0]",
    "adresOstatniegoMiejscaZamieszkaniaWPolsceLubPobytuOsobyKtoraZawiadamia.kodPocztowy": "topmostSubform[0].Page3[0].Kodpocztowy2[0]",
    "adresOstatniegoMiejscaZamieszkaniaWPolsceLubPobytuOsobyKtoraZawiadamia.miejscowosc": "topmostSubform[0].Page3[0].Poczta2[0]",
    
    # -------------------------------------------------------------------------
    # ADRES DO KORESPONDENCJI OSOBY KTÓRA ZAWIADAMIA (Page 3)
    # -------------------------------------------------------------------------
    "adresDoKorespondencjiOsobyKtoraZawiadamia.ulica": "topmostSubform[0].Page3[0].Ulica2A[0]",
    "adresDoKorespondencjiOsobyKtoraZawiadamia.numerDomu": "topmostSubform[0].Page3[0].Numerdomu2A[0]",
    "adresDoKorespondencjiOsobyKtoraZawiadamia.numerLokalu": "topmostSubform[0].Page3[0].Numerlokalu2A[0]",
    "adresDoKorespondencjiOsobyKtoraZawiadamia.kodPocztowy": "topmostSubform[0].Page3[0].Kodpocztowy2A[0]",
    "adresDoKorespondencjiOsobyKtoraZawiadamia.miejscowosc": "topmostSubform[0].Page3[0].Poczta2A[0]",
    "adresDoKorespondencjiOsobyKtoraZawiadamia.nazwaPanstwa": "topmostSubform[0].Page3[0].Nazwapaństwa2[0]",
    
    # Checkboxes for correspondence type (Page 3)
    "adresDoKorespondencjiOsobyKtoraZawiadamia.sposobKorespondencji.adres": "topmostSubform[0].Page3[0].adres[0]",
    "adresDoKorespondencjiOsobyKtoraZawiadamia.sposobKorespondencji.poste_restante": "topmostSubform[0].Page3[0].posterestante[0]",
    "adresDoKorespondencjiOsobyKtoraZawiadamia.sposobKorespondencji.skrytka_pocztowa": "topmostSubform[0].Page3[0].skrytkapocztowa[0]",
    "adresDoKorespondencjiOsobyKtoraZawiadamia.sposobKorespondencji.przegrodka_pocztowa": "topmostSubform[0].Page3[0].przegrodkapocztowa[0]",
    
    # -------------------------------------------------------------------------
    # SZCZEGÓŁY WYPADKU (Page 4)
    # -------------------------------------------------------------------------
    "informacjaOWypadku.rodzajDoznanychUrazow": "topmostSubform[0].Page4[0].Tekst4[0]",
    "informacjaOWypadku.opisOkolicznosciMiejscaIPrzyczyn": "topmostSubform[0].Page4[0].Tekst5[0]",
    "informacjaOWypadku.placowkaUdzielajacaPierwszejPomocy": "topmostSubform[0].Page4[0].Tekst6[0]",
    "informacjaOWypadku.organProwadzacyPostepowanie": "topmostSubform[0].Page4[0].Tekst7[0]",
    "informacjaOWypadku.opisStanuMaszynyIUzytkowania": "topmostSubform[0].Page4[0].Tekst8[0]",
    
    # Checkboxes for accident details (Page 4)
    "informacjaOWypadku.pierwszaPomocUdzielona.TAK": "topmostSubform[0].Page4[0].TAK6[0]",
    "informacjaOWypadku.pierwszaPomocUdzielona.NIE": "topmostSubform[0].Page4[0].NIE6[0]",
    "informacjaOWypadku.wypadekPodczasObslugiMaszynLubUrzadzen.TAK": "topmostSubform[0].Page4[0].TAK8[0]",
    "informacjaOWypadku.wypadekPodczasObslugiMaszynLubUrzadzen.NIE": "topmostSubform[0].Page4[0].NIE8[0]",
    "informacjaOWypadku.maszynaPosiadaAtestLubDeklaracjeZgodnosci.TAK": "topmostSubform[0].Page4[0].TAK9[0]",
    "informacjaOWypadku.maszynaPosiadaAtestLubDeklaracjeZgodnosci.NIE": "topmostSubform[0].Page4[0].NIE9[0]",
    "informacjaOWypadku.maszynaWpisanaDoEwidencjiSrodkowTrwalych.TAK": "topmostSubform[0].Page4[0].TAK10[0]",
    "informacjaOWypadku.maszynaWpisanaDoEwidencjiSrodkowTrwalych.NIE": "topmostSubform[0].Page4[0].NIE10[0]",
    
    # -------------------------------------------------------------------------
    # DANE ŚWIADKÓW WYPADKU (Page 5) - up to 3 witnesses
    # -------------------------------------------------------------------------
    # Witness 1
    "daneSwiadkowWypadku.0.imie": "topmostSubform[0].Page5[0].Imię[0]",
    "daneSwiadkowWypadku.0.nazwisko": "topmostSubform[0].Page5[0].Nazwisko[0]",
    "daneSwiadkowWypadku.0.adres.ulica": "topmostSubform[0].Page5[0].Ulica[0]",
    "daneSwiadkowWypadku.0.adres.numerDomu": "topmostSubform[0].Page5[0].Numerdomu[0]",
    "daneSwiadkowWypadku.0.adres.numerLokalu": "topmostSubform[0].Page5[0].Numerlokalu[0]",
    "daneSwiadkowWypadku.0.adres.kodPocztowy": "topmostSubform[0].Page5[0].Kodpocztowy[0]",
    "daneSwiadkowWypadku.0.adres.miejscowosc": "topmostSubform[0].Page5[0].Poczta[0]",
    "daneSwiadkowWypadku.0.adres.nazwaPanstwa": "topmostSubform[0].Page5[0].Nazwapaństwa[0]",
    
    # Witness 2
    "daneSwiadkowWypadku.1.imie": "topmostSubform[0].Page5[0].Imię[1]",
    "daneSwiadkowWypadku.1.nazwisko": "topmostSubform[0].Page5[0].Nazwisko[1]",
    "daneSwiadkowWypadku.1.adres.ulica": "topmostSubform[0].Page5[0].Ulica[1]",
    "daneSwiadkowWypadku.1.adres.numerDomu": "topmostSubform[0].Page5[0].Numerdomu[1]",
    "daneSwiadkowWypadku.1.adres.numerLokalu": "topmostSubform[0].Page5[0].Numerlokalu[1]",
    "daneSwiadkowWypadku.1.adres.kodPocztowy": "topmostSubform[0].Page5[0].Kodpocztowy[1]",
    "daneSwiadkowWypadku.1.adres.miejscowosc": "topmostSubform[0].Page5[0].Poczta[1]",
    "daneSwiadkowWypadku.1.adres.nazwaPanstwa": "topmostSubform[0].Page5[0].Nazwapaństwa[1]",
    
    # Witness 3
    "daneSwiadkowWypadku.2.imie": "topmostSubform[0].Page5[0].Imię2[0]",
    "daneSwiadkowWypadku.2.nazwisko": "topmostSubform[0].Page5[0].Nazwisko2[0]",
    "daneSwiadkowWypadku.2.adres.ulica": "topmostSubform[0].Page5[0].Ulica2[0]",
    "daneSwiadkowWypadku.2.adres.numerDomu": "topmostSubform[0].Page5[0].Numerdomu2[0]",
    "daneSwiadkowWypadku.2.adres.numerLokalu": "topmostSubform[0].Page5[0].Numerlokalu2[0]",
    "daneSwiadkowWypadku.2.adres.kodPocztowy": "topmostSubform[0].Page5[0].Kodpocztowy2[0]",
    "daneSwiadkowWypadku.2.adres.miejscowosc": "topmostSubform[0].Page5[0].Poczta2[0]",
    "daneSwiadkowWypadku.2.adres.nazwaPanstwa": "topmostSubform[0].Page5[0].Nazwapaństwa2[0]",
    
    # -------------------------------------------------------------------------
    # ZAŁĄCZNIKI (Page 6)
    # -------------------------------------------------------------------------
    "zalaczniki.kartaInformacyjnaLubZaswiadczeniePierwszejPomocy": "topmostSubform[0].Page5[0].ZaznaczX1[0]",
    "zalaczniki.postanowienieProkuratury": "topmostSubform[0].Page5[0].ZaznaczX2[0]",
    "zalaczniki.dokumentyDotyczaceZgonu": "topmostSubform[0].Page5[0].ZaznaczX3[0]",
    "zalaczniki.dokumentyPotwierdzajacePrawoDoKartyWypadkuDlaInnejOsoby": "topmostSubform[0].Page6[0].ZaznaczX4[0]",
    "zalaczniki.inneDokumentyOpis": "topmostSubform[0].Page6[0].Inne[0]",
    
    # -------------------------------------------------------------------------
    # DOKUMENTY DO DOSTARCZENIA PÓŹNIEJ (Page 6)
    # -------------------------------------------------------------------------
    "dokumentyDoDostarczeniaPozniej.dataDo": "topmostSubform[0].Page6[0].Data[0]",
    "dokumentyDoDostarczeniaPozniej.listaDokumentow.0": "topmostSubform[0].Page6[0].Inne1[0]",
    "dokumentyDoDostarczeniaPozniej.listaDokumentow.1": "topmostSubform[0].Page6[0].Inne2[0]",
    "dokumentyDoDostarczeniaPozniej.listaDokumentow.2": "topmostSubform[0].Page6[0].Inne3[0]",
    "dokumentyDoDostarczeniaPozniej.listaDokumentow.3": "topmostSubform[0].Page6[0].Inne4[0]",
    "dokumentyDoDostarczeniaPozniej.listaDokumentow.4": "topmostSubform[0].Page6[0].Inne5[0]",
    "dokumentyDoDostarczeniaPozniej.listaDokumentow.5": "topmostSubform[0].Page6[0].Inne6[0]",
    "dokumentyDoDostarczeniaPozniej.listaDokumentow.6": "topmostSubform[0].Page6[0].Inne7[0]",
    "dokumentyDoDostarczeniaPozniej.listaDokumentow.7": "topmostSubform[0].Page6[0].Inne8[0]",
    
    # -------------------------------------------------------------------------
    # SPOSÓB ODBIORU ODPOWIEDZI (Page 6)
    # -------------------------------------------------------------------------
    "sposobOdbioruOdpowiedzi.w_placowce_ZUS": "topmostSubform[0].Page6[0].wplacowce[0]",
    "sposobOdbioruOdpowiedzi.poczta_na_adres_wskazany_we_wniosku": "topmostSubform[0].Page6[0].poczta[0]",
    "sposobOdbioruOdpowiedzi.na_koncie_PUE_ZUS": "topmostSubform[0].Page6[0].PUE[0]",
    
    # -------------------------------------------------------------------------
    # OŚWIADCZENIE (Page 6)
    # -------------------------------------------------------------------------
    "oswiadczenie.dataZlozenia": "topmostSubform[0].Page6[0].Data[1]",
}

# =============================================================================
# CHECKBOX MAPPING: Maps enum values to their checkbox fields
# =============================================================================

CORRESPONDENCE_TYPE_CHECKBOXES = {
    "adres": "adres[0]",
    "poste_restante": "posterestante[0]",
    "skrytka_pocztowa": "skrytkapocztowa[0]",
    "przegrodka_pocztowa": "przegrodkapocztowa[0]",
}

RESPONSE_METHOD_CHECKBOXES = {
    "w_placowce_ZUS": "wplacowce[0]",
    "poczta_na_adres_wskazany_we_wniosku": "poczta[0]",
    "na_koncie_PUE_ZUS": "PUE[0]",
}

# =============================================================================
# BOOLEAN FIELD MAPPING: Maps boolean fields to TAK/NIE checkboxes
# =============================================================================

BOOLEAN_FIELD_MAPPING = {
    "informacjaOWypadku.pierwszaPomocUdzielona": {
        True: "topmostSubform[0].Page4[0].TAK6[0]",
        False: "topmostSubform[0].Page4[0].NIE6[0]",
    },
    "informacjaOWypadku.wypadekPodczasObslugiMaszynLubUrzadzen": {
        True: "topmostSubform[0].Page4[0].TAK8[0]",
        False: "topmostSubform[0].Page4[0].NIE8[0]",
    },
    "informacjaOWypadku.maszynaPosiadaAtestLubDeklaracjeZgodnosci": {
        True: "topmostSubform[0].Page4[0].TAK9[0]",
        False: "topmostSubform[0].Page4[0].NIE9[0]",
    },
    "informacjaOWypadku.maszynaWpisanaDoEwidencjiSrodkowTrwalych": {
        True: "topmostSubform[0].Page4[0].TAK10[0]",
        False: "topmostSubform[0].Page4[0].NIE10[0]",
    },
}

# =============================================================================
# DATE FORMAT CONFIGURATION
# =============================================================================

# PDF date fields have max length of 8 characters, so use DD-MM-YY format
DATE_FORMAT_PDF = "%d-%m-%y"  # e.g., "06-12-25"
DATE_FORMAT_INPUT = "%Y-%m-%d"  # ISO format from JSON schema

