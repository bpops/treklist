# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(['treklist.py'],
             pathex=['.'],
             binaries=[],
             datas=[('imgs/logo.png','imgs'),
                    ('LICENSE', '.'),
                    ('treklist.db', '.'),
                    ('user.db',     '.'),
                    ('settings.yaml', '.'),
                    ('lic/cc_by-nc_4.0','lic'),
                   ],
             hiddenimports=[],
             #hookspath=['hooks'],
             runtime_hooks=[],
             excludes=[],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher,
             noarchive=False)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(pyz,
          a.scripts,
          a.binaries,
          a.zipfiles,
          a.datas,
          [],
          name='TrekList',
          debug=False,
          bootloader_ignore_signals=False,
          strip=False,
          upx=True,
          upx_exclude=[],
          runtime_tmpdir=None,
          console=False )

app = BUNDLE(exe,
             name='TrekList.app',
             icon=None,
             bundle_identifier=None,
             info_plist={
                 'NSHighResolutionCapable': 'True', # remove blurriness
             },)
