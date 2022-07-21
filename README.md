![TrekList](./imgs/logo.png)

TrekList is an application that expands on what I had already made for my Trekkie self: a Star Trek episode tracker written in Excel. But this is a customized stand-alone version with lots of (planned) features and capabilities. I am writing this for ME. But you can use it too, if you like! :vulcan_salute:

![TrekList Screenshot](./imgs/screenshot.png)

## Use

Due to certificate signing issues, please enable this single app by running `sudo xattr -r -d com.apple.quarantine /Applications/TrekList.app`.

## Development

TrekList is built with python 3.9 and sqlite. Run `pip install -r requirements.txt` to install required modules.

### Populating the database

You will need to [generate an OMDb API key](https://www.omdbapi.com/apikey.aspx) if you want to populate the database. Place the key in a text file called `api_key` in the repo's base directory. To populate, execute the `build_db.ipynb` notebook. It will request all information from OMDb, then pull all posters and insert them into the primary sql database. (Please note that it might fail if a season of an episode is listed in a series query but then no episodes exist in the following season query; to-do).

### Bundling for macos

Run `source bundle.sh`.

## Legal

TrekList is in no way affiliated with Star Trek, CBS, or Paramount.

All textual content is courtesy of [omdb](https://www.omdbapi.com), which is licensed under [CC BY-NC 4.0](https://creativecommons.org/licenses/by-nc/4.0/).

[Vulcan salute icon](https://iconduck.com/sets/noto-emoji-by-google) is licensed under the [Apache license 2.0](https://www.apache.org/licenses/LICENSE-2.0) by Google.