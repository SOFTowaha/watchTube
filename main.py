# ===clean code and make comments===

# ====other imports====
import subprocess
import pytube
import os
import ssl
import plyer

# ====kivymd imports====
from kivymd.app import MDApp
from kivymd.uix.gridlayout import MDGridLayout
from kivymd.uix.list import TwoLineIconListItem, TwoLineAvatarIconListItem

# ====kivy imports====
from kivy import platform
from kivy.lang.builder import Builder
from kivy.properties import ObjectProperty, BooleanProperty, StringProperty
from kivy.clock import Clock


# neccessary for downloading (otherwise gives error)
ssl._create_default_https_context = ssl._create_unverified_context


# ===global variables===
AndroidPath = '/storage/emulated/0/Download/watchTube/'
specialCharacters = '"\'@#$%^&*`~.'


# ===send notifications===
def sendNotification(title, message):
    # toast notification, because normal not working with plyer :(
    plyer.notification.notify(title=title, message=message, toast=True)


# ===title generator===
def createTitle(title):
    # removes special characters in title
    for char in specialCharacters:
        title = title.replace(char, '')
    title = title.replace(" ", "_")
    return title


# ===check for files===
def checkDir(path):
    files = os.listdir(path)
    return files


#not working
# ===check if file already exists===
def checkFiles(path, title, content):
    files = os.listdir(path)
    form = 'mp4' if not content else 'mp3'
    title = createTitle(title)

    for file in files:
        fileInfo = file.split('.')
        if fileInfo[0] == title:
            if fileInfo[-1] == form:
                return False
    return True


# ===Video download function===
def startDownloadVideo(video, directory):
    Clock.schedule_once(video.streams.get_by_itag(22).download(
        f'{directory}', filename=createTitle(video.title) + '.mp4'))


# ===Audio download function===
def startDownloadAudio(audio, directory):
    Clock.schedule_once(audio.streams.filter(only_audio=True).first().download(
        f'{directory}', filename=createTitle(audio.title) + '.mp3'))


# ===Design of files displayed===
class LWI(TwoLineAvatarIconListItem):
    # icon is, for some reason, also added ontop of text
    iconImage = StringProperty('android')

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Sets icon for music and video
        self.iconImage = "movie-outline" if self.text == "Video" else "music"

    # delete file
    def delete(self, a):
        typ = a.text
        title = a.secondary_text
        file = title + ".mp4" if typ == "Video" else title + ".mp3"
        self.parent.remove_widget(a)
        os.remove(AndroidPath + file)
        sendNotification("Success", "File deleted")


# ===main display===
class Kv(MDGridLayout):
    url = ObjectProperty(None)  # gets url from input
    contentType = BooleanProperty(False)  # False == video, True == audio

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    # changing audio or video options
    def changeType(self):
        self.contentType = not self.contentType

    # downloader function
    def download(self):

        try:
            link = self.url.text
            yt = pytube.YouTube(link)

            # for android
            if platform == 'android':
                if checkFiles(AndroidPath, yt.title, self.contentType):
                    if self.contentType == False:
                        self.addWidget(createTitle(yt.title) + ".mp4")
                        startDownloadVideo(yt, AndroidPath)
                    else:
                        self.addWidget(createTitle(yt.title) + ".mp3")
                        startDownloadAudio(yt, AndroidPath)
                else:
                    sendNotification(
                        'Already Downloaded', 'File already exists!')

        except Exception as e:
            print('\n===============error===============\n')
            print(e)
            print('\n===============error===============\n')

    # Gets downloaded videos and audios
    def getDownloads(self):
        if platform == 'android':
            if checkDir(AndroidPath):
                for i in checkDir(AndroidPath):
                    self.ids.list.add_widget(LWI(text='Video' if str(i).split(".")[1] == "mp4" else "Music", secondary_text=str(
                        i).replace(".mp4", '').replace(".mp3", ''), on_press=self.openFile))

            else:
                sendNotification('Empty', 'No videos yet downloaded!')

    # Opens file on click
    def openFile(self, a):
        typ = a.text
        title = a.secondary_text
        file = title + ".mp4" if typ == "Video" else title + ".mp3"
        if platform == 'android':

            # open in default app
            from jnius import autoclass, cast
            context = autoclass('org.kivy.android.PythonActivity').mActivity
            Intent = autoclass('android.content.Intent')
            Uri = autoclass('android.net.Uri')

            if file.split('.')[1] == "mp4":
                intent = Intent(Intent.ACTION_VIEW)
                intent.setDataAndType(Uri.parse(AndroidPath + file), 'video/*')

                context.startActivity(intent)
            elif file.split('.')[1] == "mp3":
                intent = Intent(Intent.ACTION_VIEW)
                intent.setDataAndType(Uri.parse(AndroidPath + file), 'audio/*')

                context.startActivity(intent)

    # Adds widget
    def addWidget(self, text):
        self.ids.list.add_widget(LWI(text="Video" if str(text).split(".")[-1] == "mp4" else "Music", secondary_text=str(
            text).replace(".mp4", '').replace(".mp3", ''), on_press=self.openFile))


class MainApp(MDApp):
    def build(self):
        self.theme_cls.theme_style = 'Dark'
        self.theme_cls.primary_palette = 'Red'

        kv = Kv()
        kv.getDownloads()
        Builder.load_file('main.kv')

        if platform == 'android':
            # requests permissions for android storage to download to folder
            from android.permissions import request_permissions, Permission
            request_permissions(
                [Permission.READ_EXTERNAL_STORAGE, Permission.WRITE_EXTERNAL_STORAGE])

        return kv


if __name__ == '__main__':
    app = MainApp()
    app.run()
