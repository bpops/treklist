# timeslide macOS bundler

# build using pyinstaller
source ./venv/bin/activate
rm -fr dist build
pyinstaller treklist.spec

# convert icons, and bundle
iconutil -c icns -o imgs/icon-windowed.icns imgs/icon.iconset
mv imgs/icon-windowed.icns dist/treklist.app/Contents/Resources/.

# prep dist folder
mkdir -p dist/dmg
rm -r dist/dmg/*
cp -r dist/TrekList.app dist/dmg/TrekList.app
test -f "dist/Treklist.dmg" && rm "dist/Treklist.dmg"

# create the disk image
create-dmg \
    --volname "TrekList" \
    --window-pos 200 120 \
    --window-size 600 300 \
    --icon-size 100 \
    --icon "TrekList.app" 175 120 \
    --hide-extension "TrekList.app" \
    --app-drop-link 425 120 \
    "dist/TrekList.dmg" \
    "dist/dmg/"