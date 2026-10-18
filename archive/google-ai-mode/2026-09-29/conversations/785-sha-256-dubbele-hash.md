# SHA-256 Dubbele Hash

Captured: 2026-10-18T11:31:09.870Z

Source: https://www.google.com/search?client=ms-android-xiaomi-terr2-rso2&hs=3spq&sca_esv=c5052353f6356764&sxsrf=APpeQnteAbzGWTRL3FuwK7dUHORT4RJcJg%3A1792315971600&vsint=&ntc=1&cs=1&sa=X&ved=0CAcQ2_wOahgKEwjQj4e-u8OXAxUAAAAAHQAAAAAQ3wk&biw=375&bih=691&dpr=3.25&udm=50&atvm=2&mstk=AUtExfAgXNOPRpl5dRJEwdp8nQaFlOWXYeaaU2LV3YrkvpgpOOMBGWJOj7t6vaLdWI61NqP0hqkigENyNoXzkRFC1rzBl0_u-dF8yB-SMdnpOsFkkxInmQYHaIbUWpWxK9rkutu_llZ1pY9TlWxAoDjs8FNB5xXZ-k6vGhrfU-E2M9K7x3sP3IY4sSBA-ip4Kqs7mUKtdgyChXcp3uO2NDFE2m4ghauK9U6_Ez3FrSgAtATAw3Guq1ASswHq-vSHQrl2AmiZBJzsgnZlTj6N1Za99BhI3NhOelP2dsN9ZGkvQLybgwOG3OJhDbBsDGZ5ZuvFLBzwB44_ZaeHGA&mtid=JnPTapGrF82C9u8PiZHciQo&csuir=1&aep=26&q=sha256+kan+die+zelf+ook+gehashed+worden

## Prompt 1 — You

sha256 kan die zelf ook gehashed worden

## Response 1 — Google AI Mode

**Ja, een SHA-256 hash kan prima zelf opnieuw gehashed worden.** Dit proces noem je **double hashing** of het hashen van een hash.

Het resultaat is simpelweg een gloednieuwe, unieke SHA-256 hash van 64 tekens lang.

### 💡 Waar wordt dit voor gebruikt?

Het achter elkaar hashen van data is heel normaal in de cryptografie. Een bekend voorbeeld is **Bitcoin**. Het Bitcoin-netwerk gebruikt standaard **SHA-256d** (Double SHA-256) voor het beveiligen van transacties en het minen van blokken. De data wordt dan eerst één keer gehashed, en de uitkomst daarvan wordt direct nóg een keer gehashed.

### ⚠️ Belangrijk om te weten:

* **Het maakt het niet "veiliger" tegen botsen:** Sommige mensen denken dat twee keer hashen een algoritme onkraakbaar maakt. Hoewel het beschermt tegen specifieke cryptografische aanvallen (zoals een *length extension attack*), maakt het de hash zelf niet fundamenteel sterker tegen het vinden van dubbele hashes (collisions).
* **Ge Geheimen Terughalen:** Net als bij een normale hash is dit eenrichtingsverkeer. Je kunt de originele data niet terugkrijgen door de hash achteruit te berekenen, ook niet als je weet dat hij twee keer is gehashed.

Als je wilt, kan ik een **voorbeeld laten zien** van hoe zo'n dubbele hash eruitziet in Python, of je meer uitleggen over **waarom Bitcoin dit doet**. Wat heeft je interesse?

## Prompt 2 — You

geheimen terughalen?!

## Response 2 — Google AI Mode

Dat klinkt inderdaad mysterieus, maar in de cryptografie betekent "geheimen terughalen" simpelweg **het achterhalen van de originele tekst of het wachtwoord** die achter de hash zit.

Bij een hash-functie is dat **onmogelijk** door de code simpelweg "om te draaien". Hashing is namelijk **eenrichtingsverkeer**.

### 🔀 Waarom kun je een hash niet terugdraaien?

Je kunt een SHA-256 hash het beste vergelijken met een **digitale vingerafdruk** of het bakken van een taart:

* **Informatieverlies:** Of je nu een enkel woord invoert of een heel Dynamic-handboek van 1000 pagina's, de uitkomst is *altijd* exact 64 tekens lang. Er wordt dus informatie weggegooid.
* **De taart-analogie:** Als je eieren, bloem en melk mengt tot een taart, kun je de taart daarna nooit meer splitsen om de exacte eieren en melk heelhuids terug te krijgen.

### 🕵️‍♂️ Hoe kraken hackers dan wel "geheimen"?

Als een hacker een database met SHA-256 hashes steelt, kunnen ze de originele wachtwoorden niet *terugberekenen*. Hoe komen ze er dan wel achter? **Door te gokken.**

1. **Brute Force:** De computer probeert miljarden combinaties per seconde (`aaaaa`, `aaaaops`, `wachtwoord123`) en hasht deze.
2. **Vergelijken:** De computer kijkt of de hash van die gok overeenkomt met de gestolen hash.
3. **Match:** Is er een match? Dan weet de hacker welk wachtwoord bij die hash hoort.

Het "geheim" wordt dus niet teruggehaald door de hash te ontcijferen, maar door de invoer te **raden** totdat er exact dezelfde vingerafdruk uitrolt. Omdat een dubbele hash (SHA-256 van een SHA-256) dit raadproces voor de computer twee keer zo traag maakt, helpt het wel een klein beetje tegen dit soort gok-aanvallen.

Wil je zien hoe snel een computer een **simpel wachtwoord** raadt vergeleken met een **sterk wachtwoord**, of zal ik uitleggen hoe **salting** voorkomt dat hackers deze lijsten zomaar kunnen vergelijken?
