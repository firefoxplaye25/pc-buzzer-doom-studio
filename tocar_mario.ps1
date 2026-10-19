# Toca o tema do Super Mario Bros direto pelo Console::Beep do Windows
Write-Host "==================================================" -ForegroundColor Cyan
Write-Host "  TOCANDO SUPER MARIO VIA [System.Console]::Beep  " -ForegroundColor Yellow
Write-Host "==================================================" -ForegroundColor Cyan

$mario = @(
    @(659, 150), @(659, 150), @(0, 100), @(659, 150), @(0, 100),
    @(523, 150), @(659, 200), @(784, 350), @(0, 200), @(392, 350),
    @(0, 200), @(523, 250), @(0, 150), @(392, 250), @(0, 150),
    @(330, 250), @(0, 150), @(440, 200), @(494, 200), @(466, 150),
    @(440, 250), @(392, 200), @(659, 200), @(784, 200), @(880, 250),
    @(698, 150), @(784, 200), @(659, 250), @(523, 150), @(587, 150),
    @(494, 250)
)

foreach ($item in $mario) {
    $f = $item[0]
    $d = $item[1]
    if ($f -eq 0) {
        Start-Sleep -Milliseconds $d
    } else {
        Write-Host "Bip: $f Hz ($d ms)" -ForegroundColor Green
        [System.Console]::Beep($f, $d)
    }
    Start-Sleep -Milliseconds 20
}

Write-Host "Música concluída!" -ForegroundColor Cyan
