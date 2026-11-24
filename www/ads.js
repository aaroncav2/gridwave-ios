/* GridWave - native iOS glue: status bar colour, a bottom ad banner plus an occasional full-screen ad at natural breaks.
   Does nothing in a normal browser. The three quoted IDs below are filled in by the GitHub Actions
   build (scripts/prepare.sh) from your repo Variables. With no banner ID set, Google's TEST ads are
   used (safe to tap). Never tap your own live ads. */
(function () {
  var BANNER_ID = '__ADMOB_BANNER_ID__';
  var INTERSTITIAL_ID = '__ADMOB_INTERSTITIAL_ID__';
  var USE_TEST = '__ADMOB_USE_TEST__';
  var TEST_BANNER = 'ca-app-pub-3940256099942544/2934735716';        // Google's demo banner (iOS)
  var TEST_INTERSTITIAL = 'ca-app-pub-3940256099942544/4411468910';  // Google's demo interstitial (iOS)
  var COOLDOWN_MS = 180 * 1000;                                       // at least 3 minutes between full-screen ads

  var cap = window.Capacitor;
  if (!cap || !cap.isNativePlatform || !cap.isNativePlatform()) return;

  // White clock and battery on the green header (also set in capacitor.config.json).
  try { if (cap.Plugins && cap.Plugins.StatusBar) cap.Plugins.StatusBar.setStyle({ style: 'DARK' }); } catch (e) {}

  // Layout: the native banner sits just above the iPhone's home-indicator strip. Fill that strip (and the gap under
  // the bottom tabs while no ad is showing) so page content never shows through under it.
  (function () {
    var st = document.createElement('style');
    st.textContent = 'html.native #adBanner{display:block;background:#fff;border-top:0}' +
                     'html.dark.native #adBanner{background:#111827}';
    document.head.appendChild(st);
  })();

  function setAdHeight(px) {
    var h = Math.max(0, Math.ceil(px || 0));
    document.documentElement.style.setProperty('--ad-h', h + 'px');
    document.body.classList.toggle('has-ad', h > 0);
  }

  async function start() {
    var AdMob = cap.Plugins && cap.Plugins.AdMob;
    if (!AdMob) return;

    var useTest = USE_TEST !== 'false' || BANNER_ID.indexOf('__') === 0;
    var bannerId = useTest ? TEST_BANNER : BANNER_ID;
    var interId = useTest ? TEST_INTERSTITIAL : (INTERSTITIAL_ID.indexOf('__') === 0 ? '' : INTERSTITIAL_ID);

    try {
      // 1) Consent (Google UMP). It only shows a form where the law requires one (EEA, UK and similar).
      var info = await AdMob.requestConsentInfo();
      if (info.isConsentFormAvailable && info.status === 'REQUIRED') info = await AdMob.showConsentForm();
      if (!info.canRequestAds) return;

      // 2) Apple's App Tracking Transparency prompt (asked once, iOS only).
      try {
        var t = await AdMob.trackingAuthorizationStatus();
        if (t && t.status === 'notDetermined') await AdMob.requestTrackingAuthorization();
      } catch (e) { /* the prompt is optional; ads still work without it */ }

      // 3) Start the SDK, then pin a banner to the bottom. The page keeps clear of it through --ad-h.
      await AdMob.initialize();
      AdMob.addListener('bannerAdSizeChanged', function (s) { setAdHeight(s && s.height); });
      await AdMob.showBanner({
        adId: bannerId,
        adSize: 'ADAPTIVE_BANNER',
        position: 'BOTTOM_CENTER',
        margin: 0,
        isTesting: useTest
      });
    } catch (e) {
      console.warn('AdMob start failed', e);
      return;
    }

    // 4) Full-screen ad: only at natural breaks, with a cooldown, never at launch, never while playing or exporting.
    if (!interId) return;
    var ready = false, lastShown = Date.now();
    async function prepare() {
      try { await AdMob.prepareInterstitial({ adId: interId, isTesting: useTest }); ready = true; }
      catch (e) { ready = false; setTimeout(prepare, 60000); }
    }
    AdMob.addListener('interstitialAdDismissed', function () { ready = false; lastShown = Date.now(); prepare(); });
    AdMob.addListener('interstitialAdFailedToLoad', function () { ready = false; setTimeout(prepare, 60000); });
    prepare();

    // Natural breaks in GridWave: confirming "New Song" and closing the "My Songs" window.
    var BREAKS = { btnNewSongConfirm: 1, btnSongsClose: 1 };
    document.addEventListener('click', function (e) {
      var b = e.target.closest && e.target.closest('button');
      if (!b || !BREAKS[b.id]) return;
      if (ready && Date.now() - lastShown > COOLDOWN_MS) {
        setTimeout(function () { AdMob.showInterstitial().catch(function () {}); }, 400);
      }
    });
  }

  // Wait until the app is active, so the iOS tracking prompt can actually appear.
  function go() { setTimeout(start, 1200); }
  if (document.readyState === 'complete') go(); else window.addEventListener('load', go);
})();
