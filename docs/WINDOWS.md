# FCU Desktop – Windows

Program používá WINCTRL 32 FCU mimo MSFS jako hodiny a ovladač Windows. MobiFlight ani SimAppPro nesmí současně držet stejné FCU zařízení.

## Displeje

- SPD: aktuální hodina; při změně hlasitosti na 3 sekundy zobrazí `0–100 %`.
- HDG: aktuální minuta.
- ALT: datum ve formátu `DD MM`.
- V/S: venkovní teplota pro uživatelem nastavenou polohu.

## Ovládání

- Tlačítko SPD/MACH vlevo: `Win+D` – zobrazit plochu na všech monitorech; další stisk obnoví okna.
- SPD otočení: hlasitost aplikace v popředí, například Brave/YouTube.
- SPD PUSH: mute aplikace v popředí.
- HDG otočení: šipka vlevo/vpravo, například posun YouTube videa.
- HDG PUSH: Play/Pause.
- ALT v poloze 100 + otočení: jas displejů.
- ALT v poloze 1000 + otočení: jas podsvícení tlačítek a encoderů.
- V/S otočení: kolečko myši nahoru/dolů.
- V/S PUSH: klávesa Home.

## Počasí

Před spuštěním nastavte souřadnice pouze ve svém počítači:

```powershell
$env:FCU_CLOCK_LATITUDE = "your-latitude"
$env:FCU_CLOCK_LONGITUDE = "your-longitude"
fcu-desktop clock
```

Souřadnice neukládejte do veřejného repozitáře.

Program musí běžet právě v jedné instanci. Počasí se obnovuje každých 15 minut a hodiny při změně minuty.
