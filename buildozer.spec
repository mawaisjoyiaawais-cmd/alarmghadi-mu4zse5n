[app]
title = AlarmGhadi
package.name = org.kivy.alarmghadi
package.domain = app.lovable
source.dir = .
source.include_exts = py,png,jpg,kv,atlas,json,txt,ttf
version = 0.1
requirements = kivy,kivymd,plyer
orientation = portrait
fullscreen = 0
android.presplash_color = #FFFFFF
android.archs = arm64-v8a, armeabi-v7a
android.allow_backup = True
android.accept_sdk_license = True

[buildozer]
log_level = 2
warn_on_root = 1
