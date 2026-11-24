#!/usr/bin/env bash
# Prepares the web files and the native iOS project. Run by the GitHub Actions workflow
# (and safe to run by hand on a Mac). Needs the BUNDLE_ID variable.
set -euo pipefail
cd "$(dirname "$0")/.."

: "${BUNDLE_ID:?Set the BUNDLE_ID repository variable (com.aaroncav2.gridwave)}"

# ---- sanity-check the AdMob IDs so a pasted mistake fails here, not silently in the app ----
APP_ID="${ADMOB_APP_ID:-}"
BANNER="${ADMOB_BANNER_ID:-}"
INTER="${ADMOB_INTERSTITIAL_ID:-}"
matches() { printf '%s' "$2" | grep -Eq "$1"; }   # matches REGEX VALUE
if [ -n "$APP_ID" ] && ! matches '^ca-app-pub-[0-9]+~[0-9]+$' "$APP_ID"; then
  echo "::error::ADMOB_APP_ID must look like ca-app-pub-1234567890123456~1234567890 (it has a ~ in the middle). Got: $APP_ID"; exit 1
fi
if [ -n "$BANNER" ] && ! matches '^ca-app-pub-[0-9]+/[0-9]+$' "$BANNER"; then
  echo "::error::ADMOB_BANNER_ID must look like ca-app-pub-1234567890123456/1234567890 (it has a / in the middle). Got: $BANNER"; exit 1
fi
if [ -n "$INTER" ] && ! matches '^ca-app-pub-[0-9]+/[0-9]+$' "$INTER"; then
  echo "::error::ADMOB_INTERSTITIAL_ID must look like ca-app-pub-1234567890123456/1234567890 (it has a / in the middle). Got: $INTER"; exit 1
fi
if [ -n "$BANNER" ] && [ -z "$APP_ID" ]; then
  echo "::error::ADMOB_BANNER_ID is set but ADMOB_APP_ID is empty. Live ads need both."; exit 1
fi
if [ -n "$INTER" ] && [ -z "$BANNER" ]; then
  echo "::error::ADMOB_INTERSTITIAL_ID is set but ADMOB_BANNER_ID is empty. Set the banner ID too (or clear both for test ads)."; exit 1
fi

# ---- bundle id into capacitor.config.json ----
node -e 'const fs=require("fs");const c=JSON.parse(fs.readFileSync("capacitor.config.json","utf8"));c.appId=process.env.BUNDLE_ID;fs.writeFileSync("capacitor.config.json",JSON.stringify(c,null,2)+"\n");'

# ---- ad unit IDs into www/ads.js ----
# No banner ID  -> Google's TEST ads (safe to tap). Banner ID set -> live ads.
# In live mode, no interstitial ID -> no full-screen ads, banner only.
if [ -n "$BANNER" ]; then
  sed -i.bak "s#__ADMOB_BANNER_ID__#${BANNER}#; s#__ADMOB_INTERSTITIAL_ID__#${INTER}#; s#__ADMOB_USE_TEST__#false#" www/ads.js
  echo "Ads: LIVE (banner ${BANNER}, interstitial ${INTER:-none})"
else
  sed -i.bak "s#__ADMOB_USE_TEST__#true#" www/ads.js
  echo "Ads: Google TEST ads"
fi
rm -f www/ads.js.bak

# ---- generate the native project, copy the web files in, patch it ----
[ -d ios ] || npx cap add ios
npx cap sync ios
python3 scripts/patch_ios.py
