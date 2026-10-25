# Exports a .pptx to PDF with PowerPoint itself, so the PDF matches what PowerPoint shows.
#   powershell -ExecutionPolicy Bypass -File deck\export.ps1 docs\black-ant-deck.pptx docs\black-ant-deck.pdf
param([Parameter(Mandatory)][string]$Deck, [Parameter(Mandatory)][string]$Pdf)
$deckPath = (Resolve-Path $Deck).Path
$pdfPath = [System.IO.Path]::GetFullPath($Pdf)
$app = New-Object -ComObject PowerPoint.Application
try {
    # ReadOnly, Untitled off, WithWindow off
    $pres = $app.Presentations.Open($deckPath, $true, $false, $false)
    $pres.SaveAs($pdfPath, 32)  # 32 = ppSaveAsPDF
    $pres.Close()
    Write-Output "Wrote $pdfPath"
} finally {
    $app.Quit()
    [void][System.Runtime.InteropServices.Marshal]::ReleaseComObject($app)
}
