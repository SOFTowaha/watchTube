# ====other imports====
import os
import ssl
from jnius import autoclass
import pytube
from plyer import notification

# ====kivymd imports====
from kivymd.app import MDApp
from kivymd.uix.screen import MDScreen
from kivymd.uix.list import TwoLineAvatarIconListItem

# ====kivy imports====
from kivy import platform
from kivy.lang.builder import Builder
from kivy.properties import BooleanProperty, StringProperty, ObjectProperty
from kivy.clock import mainthread


# neccessary for internet on android
ssl._create_default_https_context = ssl._create_unverified_context
pytube.request.default_range_size = 1048576


# ===global variables===
PATH = "watchTube/"
if platform == 'android':
    # requests permissions for android storage to download to folder
    from android.permissions import request_permissions, Permission
    from android.storage import primary_external_storage_path
    PATH = f'{str(primary_external_storage_path())}/watchTube/'

# unwanted characters
SPECIAL_CHARACTERS = '"\'.-#:;$!@$()[]{,}<>€+-?/\\%&*~`|^'


def send_notification(title, message):
    '''sends notifications'''
    notification.notify(title=title, message=message)


def create_title(title, content):
    '''removes special chars and adds extension'''
    for char in SPECIAL_CHARACTERS:
        title = title.replace(char, '')
    title = title.replace(" ", "_")
    title = title.lower()
    title += ".mp3" if content else ".mp4"
    return title


def check_dir(path):
    '''checks for path and returs result'''
    try:
        files = os.listdir(path)
    except:
        send_notification('Error', "No Downloads")
        files = []
    return files


def file_exists(path, title, content):
    '''checks if file already downloaded'''
    files = os.listdir(path)
    title = create_title(title, content)

    for file in files:
        if file == title:
            return True
    return False

def download_file(file, content):
    '''downloads youtube content to PATH'''
    if content:
        # downloads audio
        file.streams.filter(only_audio=True).first().download(PATH, filename=create_title(file.title, True))
    else:
        # downloads video
        file.streams.get_by_itag(22).download(PATH, filename=create_title(file.title, False))


# ===Design of files displayed===
class LWI(TwoLineAvatarIconListItem):
    '''List item'''
    icon = StringProperty('') # displayed icon | movie-outline / music

    def delete(self, file_pressed):
        '''deletes content'''
        if app.downloading:
            # if app downloading
            send_notification('Error', "Not yet downloaded")
            return

        for item in app.data:
            if item["secondary_text"] == file_pressed.secondary_text:
                app.data.remove(item)
        app.root.ids.main.ids.recycle.data = app.data
        os.remove(PATH + file_pressed.secondary_text)

    def open(self, file, text):
        '''opens file in default media player'''
        if app.downloading:
            # if app downloading
            send_notification('Error', "Not yet downloaded!")
            return

        typ = text
        title = file
        if platform == 'android':
            context = autoclass(
                'org.kivy.android.PythonActivity').mActivity
            Intent = autoclass(
                'android.content.Intent')
            Uri = autoclass(
                'android.net.Uri')

            intent = Intent(Intent.ACTION_VIEW)
            intent.setDataAndType(Uri.parse(PATH + title), 'audio/*' if typ == "Music" else "video/*")
            context.startActivity(intent)
        elif platform == "windows":
            os.startfile(PATH + title)
        else:
            pass


# # ===main display===
class Kv(MDScreen):
    '''Main screen'''
    url = StringProperty("")  # gets url from input

    def loading_bar(self, stream, chunk, bytes_remaining):
        '''displays progress on a loading_bar'''
        value = round((1 - bytes_remaining / stream.filesize) * 100, 3)
        self.ids.progress_bar.value = value

    @mainthread
    def add_list_item(self, title, icon, filetype):
        '''adds item to recycle list'''
        app.data.append({"icon": icon, "text": filetype, "secondary_text": title})
        self.ids.recycle.data = app.data
    
    @mainthread
    def remove_list_item(self, list_item):
        '''removes item from recycle list'''
        for item in app.data:
            if item["secondary_text"] == list_item:
                app.data.remove(item)
        self.ids.recycle.data = app.data

    def download(self):
        '''starts downloading youtube content'''
        if app.downloading:
            # if app downloading
            send_notification("Error", "Proccess in working!")
            return
        # starts download ui
        app.downloading = True
        self.ids.progress_bar.value = 0
        self.url = self.ids.text_field.text
        content_type = self.ids.switch.active

        if not self.url:
            # if url empty
            send_notification("Error", "No url")
            app.downloading = False
            self.ids.progress_bar.value = 100
            return
        try:
            # gets yt info
            youtube_video = pytube.YouTube(self.url)
            youtube_video.register_on_progress_callback(
                self.loading_bar)
            youtube_video.register_on_complete_callback(
                self.completed_download)

            if file_exists(PATH, youtube_video.title, content_type):
                # if file already exists
                send_notification('Already Downloaded', 'File already exists!')
                app.downloading = False
                self.ids.progress_bar.value = 100
                return

            # gets info for ui
            title = create_title(youtube_video.title, content_type)
            icon = "download"
            self.add_list_item(title, icon, "Music" if content_type else "Video")

            try:
                # downloads file
                download_file(youtube_video, content_type)
            except Exception as e:
                app.downloading = False
                self.ids.progress_bar.value = 100
                self.remove_list_item(title)
                os.remove(PATH + title)
                print(e)

        except Exception as exception:
            print(exception)
            app.downloading = False
            self.ids.progress_bar.value = 100
            send_notification("Error", "Wrong URL")

    def completed_download(self, stream, path_to_file):
        '''changes ui after file downloaded'''
        # stops download
        app.downloading = False
        send_notification("Success", "File was downloaded")

        # gets required info
        file_name = path_to_file.rsplit("/", maxsplit=1)[-1]
        typ = "Video" if file_name.split('.', maxsplit=1)[-1] == "mp4" else "Music"
        icon = "movie-outline" if typ == "Video" else "music"

        # changes ui
        self.remove_list_item(file_name)
        self.add_list_item(file_name, icon, typ)

    def get_downloads(self):
        '''displays downloaded content'''
        if not check_dir(PATH):
            # if no files downloaded
            send_notification("Empty", "No videos yet downloaded!")
            return
        for i in check_dir(PATH):
            typ = "Music" if i.split(".", maxsplit=1)[-1] == "mp3" else "Video"
            icon = ("movie-outline" if typ == "Video" else "music")
            self.add_list_item(i, icon, typ)



class MainApp(MDApp):
    downloading = BooleanProperty(False)  # to prevent crashes
    data = ObjectProperty([]) # all displayed list items

    def build(self):
        '''builds Kivy GUI and manages permissions'''
        if platform == 'android':
            request_permissions([Permission.READ_EXTERNAL_STORAGE, Permission.WRITE_EXTERNAL_STORAGE])
            try:
                os.mkdir(PATH)
            except:
                pass
        else:
            try:
                os.mkdir(PATH)
            except:
                pass

        # sets theme
        self.theme_cls.theme_style = 'Light'
        self.theme_cls.primary_palette = 'Purple'
        return Builder.load_file("kivy.kv") # generates GUI

    def on_start(self):
        '''populates recycle list after build'''
        app.root.ids.main.get_downloads()

    def on_resume(self):
        '''populates recycle list after app paused'''
        app.data = []
        app.root.ids.main.get_downloads()

if __name__ == '__main__':
    app = MainApp()
    app.run()
