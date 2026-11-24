# GridWave for iPhone (App Store, built in the cloud, no Mac)

This folder builds the GridWave iPhone app on GitHub and uploads it to TestFlight. It is iPhone only.
Bundle ID: `com.aaroncav2.gridwave` (it can never be changed after the first upload).

```
www/index.html            the app (identical to the Android app)
www/ads.js                AdMob banner + occasional full-screen ad (iPhone version)
assets/icon-1024.png      app icon, RGB, no transparency
assets/splash.png         launch image (green-to-purple gradient)
scripts/prepare.sh        sets the bundle ID and ad IDs, creates the iOS project, patches it
scripts/patch_ios.py      Info.plist, iPhone-only, icon, launch image, audio session
.github/workflows/ios-testflight.yml   the build (copy in github-workflows-copy/)
docs/                     privacy policy + support page for GitHub Pages
```

## One-time setup (in this order)

1. **Apple identifier + App Store Connect app** for `com.aaroncav2.gridwave`.
2. **AdMob**: one iOS app, then a Banner unit and an Interstitial unit under it.
3. **Provisioning profile**: App Store Connect distribution profile for the new bundle ID, made with your existing Apple Distribution certificate.
4. **GitHub**: new **public** repo `gridwave-ios`, upload this folder, add the secrets and variables below.
5. **Build** (Actions → Run workflow) with the ad variables empty, install from TestFlight, check the test banner.
6. Fill in the **ad variables**, build again, then submit.

## GitHub settings (Settings → Secrets and variables → Actions)

**Secrets** (the same values as War Room, except the profile)

| Name | Value |
|---|---|
| `APPLE_TEAM_ID` | Team ID |
| `ASC_KEY_ID` | App Store Connect API Key ID |
| `ASC_ISSUER_ID` | Issuer ID |
| `ASC_KEY_P8` | Entire contents of the `.p8` file |
| `IOS_CERTIFICATE_BASE64` | Base64 of your `.p12` (one line) |
| `IOS_CERTIFICATE_PASSWORD` | The `.p12` password |
| `IOS_PROVISION_PROFILE_BASE64` | Base64 of the **new** GridWave `.mobileprovision` |

**Variables**

| Name | Value |
|---|---|
| `BUNDLE_ID` | `com.aaroncav2.gridwave` |
| `ADMOB_APP_ID` | AdMob iOS App ID (`ca-app-pub-…~…`) |
| `ADMOB_BANNER_ID` | Banner unit ID (`ca-app-pub-…/…`). **Leave empty for the first test build.** |
| `ADMOB_INTERSTITIAL_ID` | Interstitial unit ID (`ca-app-pub-…/…`). Leave empty with the banner. |
| `APP_VERSION` | Optional, default `1.0.0` |

Secrets and variables are different tabs. Put each one in the right tab.

## What the build does

- With `ADMOB_BANNER_ID` empty, the app shows Google's **test** ads (safe to tap).
- With it set, the app shows your **live** ads. Live ads do not show in TestFlight, and new units can take a day or more to fill.
- The build number is the workflow run number, so each run is higher than the last.
- A green check is not enough. Confirm the build appears in App Store Connect → TestFlight (10–30 minutes after the run).
- If a run fails, open the failed step, or download the `build-logs` file at the bottom of the run page.

## Never commit

`.p8`, `.p12`, `.cer`, `.key`, `.mobileprovision` or any password. `.gitignore` blocks them; they belong in GitHub Secrets and in your own backup.
