# ====other imports====
import os
import ssl
from jnius import autoclass
import pytube
import plyer
#from circular_progress_bar import CircularProgressBar

# ====kivymd imports====
from kivymd.app import MDApp
from kivymd.uix.gridlayout import MDGridLayout
from kivymd.uix.list import TwoLineAvatarIconListItem
from kivymd.uix.selectioncontrol import MDCheckbox
# , IRightBodyTouch
# from kivymd.uix.boxlayout import MDBoxLayout

# ====kivy imports====
from kivy import platform
from kivy.lang.builder import Builder
from kivy.properties import ObjectProperty, BooleanProperty, StringProperty
from kivy.clock import Clock, mainthread


# neccessary for downloading (otherwise gives error)
ssl._create_default_https_context = ssl._create_unverified_context
pytube.request.default_range_size = 1048576


# ===global variables===
# sets path for downloads
if platform == 'android':
    # requests permissions for android storage to download to folder
    from android.permissions import request_permissions, Permission
    from android.storage import primary_external_storage_path
    ANDROID_PATH = f'{str(primary_external_storage_path())}/watchTube/'

# characters you dont want in your title
SPECIAL_CHARACTERS = '"\'.-#:;$!@$()[]{,}<>€+-?/\\%&*~`|'


# ===send notifications===
def send_notification(title, message):
    # it's toast for now, since normal notifs not working
    plyer.notification.notify(title=title, message=message, toast=True)


# ===title generator===
def create_title(title):
    # removes the SPECIAL_CHARACTERS from string
    for char in SPECIAL_CHARACTERS:
        title = title.replace(char, '')
    title = title.replace(" ", "_")
    title = title.lower()
    return title


# ===check for files===
def check_dir(path):
    # if path exists returns files in there
    try:
        files = os.listdir(path)
        return files
    except:
        send_notification('Error', "No Downloads")
        files = []
        return files


# ===check if file already exists===
def check_files(path, title, content):
    # checks if file or that name is already in use
    files = os.listdir(path)
    form = 'mp4' if not content else 'mp3'
    title = create_title(title)

    for file in files:
        file_info = file.split('.')
        if file_info[0] == title:
            if file_info[-1] == form:
                return False
    return True


# ===Video download function===
def start_download_video(video, directory):
    # downloads video
    video.streams.get_by_itag(22).download(
        f'{directory}', filename=create_title(video.title) + '.mp4')


# ===Audio download function===
def start_download_audio(audio, directory):
    # downloads audio
    audio.streams.filter(only_audio=True).first().download(
        f'{directory}', filename=create_title(audio.title) + '.mp3')


# ===Design of files displayed===
class LWI(TwoLineAvatarIconListItem):
    # icon is shown twice
    icon = StringProperty('')

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    # deletes file
    def delete(self, file_pressed):
        if not Kv.downloading:
            send_notification('Error', "Not yet downloaded")
        else:
            typ = file_pressed.text
            title = file_pressed.secondary_text
            file = title + ".mp4" if typ == "Video" else title + ".mp3"
            self.parent.remove_widget(file_pressed)
            os.remove(ANDROID_PATH + file)
            send_notification("Success", "File deleted")


# ===main display===
class Kv(MDGridLayout):
    downloading = BooleanProperty(False)  # to prevent crashes
    url = ObjectProperty(None)  # gets url from input
    content_type = BooleanProperty(False)  # False == video, True == audio

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    # changing audio or video options
    def change_type(self):
        self.content_type = not self.content_type

    # loading bar
    def loading_bar(self, stream, chunk, bytes_remaining):
        value = round((1 - bytes_remaining / stream.filesize) * 100, 3)
        self.ids.progress_bar.value = value

    # on downloaded
    def completed_download(self, stream, path_to_file):

        self.downloading = False
        send_notification("Success", "File was downloaded")

        file_name = path_to_file.replace(ANDROID_PATH, '')
        typ = "Video" if file_name.split(
            '.', maxsplit=1)[-1] == "mp4" else "Music"
        title = file_name.split('.', maxsplit=1)[0]
        icon = "movie-outline" if typ == "Video" else "music"

        for item in self.ids.list.children:
            if item.secondary_text == title and item.text == typ:
                last_widget = item

        self.add_new_widget(file_name, icon)
        self.ids.list.remove_widget(last_widget)

    # downloader function
    def download(self):
        if self.downloading:
            send_notification("Error", "Proccess in working!")
        else:
            self.downloading = True
            self.ids.progress_bar.value = 0

            try:
                link = self.url.text
                youtube_video = pytube.YouTube(link)
                youtube_video.register_on_progress_callback(self.loading_bar)
                youtube_video.register_on_complete_callback(
                    self.completed_download)

                # for android
                if platform == 'android':
                    if check_files(ANDROID_PATH, youtube_video.title, self.content_type):
                        if not self.content_type:
                            title = create_title(youtube_video.title) + ".mp4"
                            icon = "download"
                            self.add_new_widget(title, icon)

                            try:
                                start_download_video(
                                    youtube_video, ANDROID_PATH)
                            except:
                                self.downloading = False
                                typ = "Video"

                                for item in self.ids.list.children:
                                    if item.secondary_text == title.replace(".mp4", '') and item.text == typ:
                                        last_widget = item
                                        self.ids.list.remove_widget(
                                            last_widget)
                        else:
                            title = create_title(youtube_video.title) + ".mp3"
                            icon = "download"
                            self.add_new_widget(title, icon)

                            try:
                                start_download_audio(
                                    youtube_video, ANDROID_PATH)
                            except:
                                self.downloading = False
                                typ = "Music"

                                for item in self.ids.list.children:
                                    if item.secondary_text == title.replace(".mp3", '') and item.text == typ:
                                        last_widget = item
                                        self.ids.list.remove_widget(
                                            last_widget)
                    else:
                        send_notification(
                            'Already Downloaded', 'File already exists!')

            except Exception as exception:
                print('\n===============error===============\n')
                print(exception)
                print('\n===============error===============\n')
                self.downloading = False
                send_notification("Error", "Wrong URL")

    # Gets downloaded videos and audios
    def get_downloads(self):
        if platform == 'android':
            if check_dir(ANDROID_PATH):
                for i in check_dir(ANDROID_PATH):
                    icon = ("movie-outline"
                            if i.split(".", maxsplit=1)[-1] == "mp4"
                            else "music")
                    self.add_new_widget(i, icon)

            else:
                send_notification('Empty', 'No videos yet downloaded!')

    # Opens file on click
    def open_file(self, file):
        if self.downloading:
            send_notification('Error', "Not yet downloaded!")
        else:
            typ = file.text
            title = file.secondary_text
            file = title + ".mp4" if typ == "Video" else title + ".mp3"
            if platform == 'android':

                # open in default app
                context = autoclass(
                    'org.kivy.android.PythonActivity').mActivity
                Intent = autoclass(
                    'android.content.Intent')
                Uri = autoclass(
                    'android.net.Uri')

                if file.split('.')[1] == "mp4":
                    intent = Intent(Intent.ACTION_VIEW)
                    intent.setDataAndType(
                        Uri.parse(ANDROID_PATH + file), 'video/*')

                    context.startActivity(intent)
                elif file.split('.')[1] == "mp3":
                    intent = Intent(Intent.ACTION_VIEW)
                    intent.setDataAndType(
                        Uri.parse(ANDROID_PATH + file), 'audio/*')

                    context.startActivity(intent)

    # Adds widget
    @mainthread
    def add_new_widget(self, file, icon):
        text = str(file)
        typ = "Video" if text.split(".", maxsplit=1)[-1] == "mp4" else "Music"
        title = text.split(".", maxsplit=1)[0]

        self.ids.list.add_widget(LWI(
            text=typ,
            secondary_text=title,
            on_press=self.open_file,
            icon=icon
        ))


class MainApp(MDApp):
    path = str()

    def build(self):
        if platform == 'android':
            request_permissions(
                [Permission.READ_EXTERNAL_STORAGE, Permission.WRITE_EXTERNAL_STORAGE])

            self.path = f'{str(primary_external_storage_path())}/watchTube/'

        self.theme_cls.theme_style = 'Light'
        self.theme_cls.primary_palette = 'Purple'

        kv = Kv()
        kv.get_downloads()

        return kv

    def on_start(self):
        # makes the download directory
        try:
            os.mkdir(self.path, mode=0o000)
        except:
            pass


if __name__ == '__main__':
    app = MainApp()
    app.run()
