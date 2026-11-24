#!/usr/bin/env python3
"""Patch the generated Capacitor iOS project for GridWave (AdMob, App Store, audio, look).
Run after `npx cap add ios` / `npx cap sync ios`. Safe to run repeatedly."""
import glob, json, os, plistlib, re, shutil, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
APP = os.path.join(ROOT, "ios/App")
PLIST = os.path.join(APP, "App/Info.plist")
PBX = os.path.join(APP, "App.xcodeproj/project.pbxproj")
APPDELEGATE = os.path.join(APP, "App/AppDelegate.swift")
XCASSETS = os.path.join(APP, "App/Assets.xcassets")
ICON_SRC = os.path.join(ROOT, "assets/icon-1024.png")
SPLASH_SRC = os.path.join(ROOT, "assets/splash.png")

if not os.path.exists(PLIST):
    sys.exit("Info.plist not found at %s - did `npx cap add ios` run?" % PLIST)

# Google's public TEST app ID. Replaced by your real one through the ADMOB_APP_ID variable.
TEST_APP_ID = "ca-app-pub-3940256099942544~1458002511"
app_id = os.environ.get("ADMOB_APP_ID", "").strip() or TEST_APP_ID

# SKAdNetwork IDs: Google's list for AdMob, from
# https://developers.google.com/admob/ios/quick-start#update_your_infoplist (50 IDs, refreshed Nov 2026).
# Google updates it now and then; refresh it from that page when you build a new version.
SKAN = """cstr6suwn9 4fzdc2evr5 2fnua5tdw4 ydx93a7ass p78axxw29g v72qych5uu ludvb6z3bs cp8zw746q7
3sh42y64q3 c6k4g5qg8m s39g8k73mm wg4vff78zm 3qy4746246 f38h382jlk hs6bdukanm mlmmfzh3r3 v4nxqhlyqp
wzmmz9fp6w su67r6k2v3 yclnxrl5pm t38b2kh725 7ug5zh24hu gta9lk7p23 vutu7akeur y5ghdn5j9k v9wttpbfk9
n38lu8286q 47vhws6wlr kbd757ywx3 9t245vhmpl a2p9lx4jpn 22mmun2rn5 44jx6755aq k674qkevps 4468km3ulz
2u9pt9hc89 8s468mfl3y klf5c3l5u5 ppxm28t8ap kbmxgpxpgc uw77j35x4d 578prtvx9j 4dzt52r2t5 tl55sbb4fm
c3frkrj4fj e5fvkxwrpn 8c4e2ghe7u 3rd42ekr43 97r2b46745 3qcr597p9d""".split()
assert len(SKAN) == 50 and len(set(SKAN)) == 50, "SKAdNetwork list should be 50 unique IDs"

# ---------------------------------------------------------------- Info.plist
with open(PLIST, "rb") as f:
    pl = plistlib.load(f)

pl["GADApplicationIdentifier"] = app_id
pl["NSUserTrackingUsageDescription"] = (
    "This lets GridWave show you ads that are more relevant to you. "
    "The app works the same if you say no.")
pl["NSMicrophoneUsageDescription"] = (
    "GridWave uses the microphone only when you tap Record Mic, to record a sound you can edit "
    "and add to your song. Recordings stay on your device.")
pl["SKAdNetworkItems"] = [{"SKAdNetworkIdentifier": "%s.skadnetwork" % i} for i in SKAN]
pl["ITSAppUsesNonExemptEncryption"] = False        # only standard HTTPS: skips the export-compliance question
pl["UIRequiredDeviceCapabilities"] = ["arm64"]
pl["UIUserInterfaceStyle"] = "Light"               # the app is light-themed; keeps system sheets and the keyboard matching
# White clock and battery on the green header: set by the StatusBar plugin (capacitor.config.json, style DARK).
# That plugin needs "view controller-based status bar appearance", which is the default, so nothing to set here.
pl.pop("UIStatusBarStyle", None)
pl.pop("UIViewControllerBasedStatusBarAppearance", None)

with open(PLIST, "wb") as f:
    plistlib.dump(pl, f)
print("Info.plist patched (AdMob app id: %s)" % ("Google TEST id" if app_id == TEST_APP_ID else app_id))

# ---------------------------------------------------------------- iPhone only
with open(PBX, encoding="utf-8") as f:
    s = f.read()
s2 = re.sub(r'TARGETED_DEVICE_FAMILY = "?[0-9,]+"?;', 'TARGETED_DEVICE_FAMILY = 1;', s)
if s2 != s:
    with open(PBX, "w", encoding="utf-8") as f:
        f.write(s2)
print("Device family: iPhone only")

# ---------------------------------------------------------------- PNG helpers
def png_info(path):
    with open(path, "rb") as f:
        head = f.read(26)
    if head[:8] != b"\x89PNG\r\n\x1a\n":
        return None
    w = int.from_bytes(head[16:20], "big"); h = int.from_bytes(head[20:24], "big")
    return w, h, head[25]          # colour type: 2 = RGB, 6 = RGBA

# ---------------------------------------------------------------- app icon
icon_dir = os.path.join(XCASSETS, "AppIcon.appiconset")
if os.path.exists(ICON_SRC) and os.path.isdir(icon_dir):
    w, h, ct = png_info(ICON_SRC) or (0, 0, 0)
    if (w, h) != (1024, 1024):
        sys.exit("assets/icon-1024.png must be 1024x1024 (it is %sx%s)" % (w, h))
    if ct in (4, 6):
        print("WARNING: icon-1024.png has an alpha channel; App Store Connect rejects transparent icons", file=sys.stderr)
    names = set()
    try:
        with open(os.path.join(icon_dir, "Contents.json"), encoding="utf-8") as f:
            for im in json.load(f).get("images", []):
                if im.get("filename"):
                    names.add(im["filename"])
    except Exception:
        pass
    if not names:
        names = {"AppIcon-512@2x.png"}
    for n in names:
        shutil.copyfile(ICON_SRC, os.path.join(icon_dir, n))
    print("App icon replaced (%s)" % ", ".join(sorted(names)))
else:
    print("WARNING: assets/icon-1024.png or AppIcon.appiconset not found, default icon kept", file=sys.stderr)

# ---------------------------------------------------------------- launch image (plain green-to-purple gradient,
# the same colours as the in-app splash, so the hand-over is seamless and the Capacitor logo never shows)
splash_dir = os.path.join(XCASSETS, "Splash.imageset")
if os.path.exists(SPLASH_SRC) and os.path.isdir(splash_dir):
    pngs = glob.glob(os.path.join(splash_dir, "*.png"))
    for p in pngs:
        shutil.copyfile(SPLASH_SRC, p)
    print("Launch image replaced (%d files)" % len(pngs))
else:
    print("NOTE: launch image not replaced (assets/splash.png or Splash.imageset missing)")

# ---------------------------------------------------------------- audio: play even when the silent switch is on
MARK = "GridWave audio session"
if os.path.exists(APPDELEGATE):
    with open(APPDELEGATE, encoding="utf-8") as f:
        src = f.read()
    if MARK in src:
        print("AppDelegate already patched")
    else:
        m = re.search(r'func application\(\s*_ application: UIApplication,\s*didFinishLaunchingWithOptions[^{]*\{', src)
        if not m:
            print("WARNING: could not find didFinishLaunchingWithOptions in AppDelegate.swift; audio-session patch skipped", file=sys.stderr)
        else:
            snippet = (
                "\n        // " + MARK + ": play through the speaker even when the iPhone's silent switch is on\n"
                "        do {\n"
                "            try AVAudioSession.sharedInstance().setCategory(.playback, mode: .default, options: [])\n"
                "        } catch {\n"
                "            print(\"GridWave: could not set the audio session category: \\(error)\")\n"
                "        }\n")
            src = src[:m.end()] + snippet + src[m.end():]
            if "import AVFoundation" not in src:
                src = re.sub(r'(?m)^import UIKit[ \t]*$', 'import UIKit\nimport AVFoundation', src, count=1)
            with open(APPDELEGATE, "w", encoding="utf-8") as f:
                f.write(src)
            print("AppDelegate patched (audio session = playback)")
else:
    print("WARNING: AppDelegate.swift not found; audio-session patch skipped", file=sys.stderr)
