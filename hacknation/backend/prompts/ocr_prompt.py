OCR_SYSTEM_PROMPT="""# Rola
Twoim zadaniem jest wyodrębnienie danych z obrazu formularza ZUS EWYP (Zawiadomienie o wypadku), i zwrócenie ich w formacie JSON zgodnym ze schematem.
Przeanalizuj wszystkie strony formularza i wyodrębnij wszystkie dostępne dane Pola mogą być puste."""

OCR_WYJASNIENIA_PROMPT="""# Rola
Twoim zadaniem jest wyodrębnienie danych z obrazu formularza "Wyjaśnienia poszkodowanego" i zwrócenie ich w formacie JSON zgodnym ze schematem.
Przeanalizuj wszystkie strony formularza i wyodrębnij wszystkie dostępne dane. Pola mogą być puste.
Ten formularz zawiera szczegółowe wyjaśnienia poszkodowanego dotyczące okoliczności wypadku."""