/**
 * LES Ecology Center Tree Care Map: view-only public version.
 *
 * Serves Index.html (built by scripts/build_public_view.py) as a web app.
 * This project reads and writes nothing itself: the page loads tree data from
 * the published data files and reads a few tabs of the tree care Sheet
 * through the existing TreeCareData web app.
 *
 * Deploy: Deploy > New deployment > Web app
 *   Execute as: Me
 *   Who has access: Anyone
 * See PUBLIC_VIEW_SETUP.md in the repo for the full steps.
 */
function doGet() {
  return HtmlService.createHtmlOutputFromFile('Index')
    .setTitle('LES Ecology Center Tree Care Map')
    .addMetaTag('viewport', 'width=device-width, initial-scale=1')
    .setXFrameOptionsMode(HtmlService.XFrameOptionsMode.ALLOWALL);
}
